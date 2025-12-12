import re
import math
import json
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, Tuple
from .material_database import db as material_db

class MaterialProcessor:
    """
    Handles material property calculations for HEA and Cermet systems.
    
    Attributes:
        db: Reference to the shared material database instance.
        element_data: Dictionary of base element properties (radius, VEC, mass, etc.).
        wc_props: Dictionary of standard properties for Tungsten Carbide (WC).
    """
    
    def __init__(self):
        """Initializes the MaterialProcessor and loads reference data."""
        self.db = material_db
        self.element_data: Dict[str, Dict[str, float]] = {}
        self.wc_props: Dict[str, float] = {}
        self._load_reference_data()

    def _load_reference_data(self) -> None:
        """Loads element and WC properties from JSON configuration file."""
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'materials.json')
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.element_data = data.get('ELEMENT_DATA', {})
                self.wc_props = data.get('P_WC', {})
        except FileNotFoundError:
            # Fallback for critical WC props if file missing (though file should exist)
            print(f"Warning: {data_path} not found. Using defaults.")
            self.wc_props = {
                'a': 2.906, 
                'G': 283.0, 
                'Tm': 3143.0, 
                'alpha': 5.2 
            }

    def parse_formula(self, formula_str: str) -> Optional[Dict[str, float]]:
        """
        Parses a chemical formula string into a normalized composition dictionary.
        
        Args:
            formula_str: String like "AlCoCrFeNi" or "Al10Co20".
            
        Returns:
            Dictionary {Element: MoleFraction} or None if invalid.
        """
        if not isinstance(formula_str, str):
            return None
            
        formula_str = formula_str.strip()
        matches = re.findall(r'([A-Z][a-z]*)(\d*\.?\d*)', formula_str)
        
        composition = {}
        total_moles = 0.0
        
        for el, amt in matches:
            # Validate element existence in DB or local map
            if not self.db.get_element(el) and el not in self.element_data:
                continue
                
            amount = float(amt) if amt else 1.0
            composition[el] = composition.get(el, 0.0) + amount
            total_moles += amount
            
        if total_moles == 0:
            return None
        
        return {k: v / total_moles for k, v in composition.items()}

    def calculate_properties(self, composition: Dict[str, float]) -> Dict[str, float]:
        """
        Calculates basic HEA properties: S_mix, VEC, and Atomic Size Difference.
        
        Args:
            composition: Dictionary of {Element: MoleFraction}.
            
        Returns:
            Dictionary of calculated properties.
        """
        if not composition:
            return {}
            
        # 1. Mixing Entropy: S_mix = -R * sum(c_i * ln(c_i))
        s_mix_R = -sum(c * math.log(c) for c in composition.values() if c > 0)
        
        # 2. VEC & Atomic Size
        vec_vals = []
        r_vals = []
        fracs = []
        
        for el, frac in composition.items():
            # Try DB first, then local fallback
            vec = self.db.get_property(el, 'vec')
            if vec is None and el in self.element_data:
                vec = self.element_data[el].get('vec')
                
            r = self.db.get_property(el, 'r')
            if r is None and el in self.element_data:
                r = self.element_data[el].get('r')
                
            if vec is not None:
                vec_vals.append(frac * vec)
            
            if r is not None:
                 r_vals.append(r)
                 fracs.append(frac)

        vec_avg = sum(vec_vals) if vec_vals else 0.0
        
        # 3. Delta
        delta = 0.0
        if r_vals:
            r_bar = sum(c * r for c, r in zip(fracs, r_vals))
            if r_bar > 0:
                sq_diffs = [c * ((1 - r / r_bar) ** 2) for c, r in zip(fracs, r_vals)]
                delta = math.sqrt(sum(sq_diffs)) * 100
        
        return {
            'S_mix (R)': round(s_mix_R, 4),
            'VEC': round(vec_avg, 4),
            'Delta (%)': round(delta, 4)
        }

    def calculate_enthalpy(self, composition: Dict[str, float]) -> float:
        """
        Calculates mixing enthalpy based on binary pairs.
        
        Args:
           composition: Normalized dictionary of {Element: Fraction}.
           
        Returns:
           Mixing enthalpy in kJ/mol.
        """
        elements = list(composition.keys())
        h_mix = 0.0
        
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                el1, el2 = elements[i], elements[j]
                c_i, c_j = composition[el1], composition[el2]
                
                h_ij = self.db.get_enthalpy(el1, el2)
                # Miedema approximation model factor
                h_mix += 4 * h_ij * c_i * c_j
                
        return h_mix

    def calculate_cermet_properties(self, 
                                  composition: Dict[str, float], 
                                  particle_size_um: float = 1.0, 
                                  is_weight_percent: bool = False) -> Dict[str, float]:
        """
        Calculates cermet-specific properties like binder volume and mean free path.
        """
        binders = {'Co', 'Ni', 'Fe', 'Al', 'Cu', 'Mn'}
        weight_fracs = {}
        
        if is_weight_percent:
            total_w = sum(composition.values())
            if total_w == 0: return {}
            weight_fracs = {k: v/total_w for k, v in composition.items()}
        else:
            # Convert Atomic -> Weight
            total_weight = 0.0
            temp_weights = {}
            for el, atomic_frac in composition.items():
                mass = self.db.get_property(el, 'mass') or (self.element_data.get(el, {}).get('mass'))
                if mass:
                    w = atomic_frac * mass
                    temp_weights[el] = w
                    total_weight += w
                else:
                    return {} # Missing mass data
            
            if total_weight == 0: return {}
            weight_fracs = {k: v/total_weight for k, v in temp_weights.items()}

        # Weight -> Volume
        total_vol = 0.0
        vol_fracs = {}
        
        for el, w_frac in weight_fracs.items():
            rho = self.db.get_property(el, 'rho') or (self.element_data.get(el, {}).get('rho'))
            if rho:
                v = w_frac / rho
                total_vol += v
            else:
                return {} # Missing density data

        if total_vol == 0: return {}
        theoretical_density = 1.0 / total_vol
        
        binder_vol = 0.0
        for el, w_frac in weight_fracs.items():
            rho = self.db.get_property(el, 'rho') or (self.element_data.get(el, {}).get('rho'))
            if rho:
                v_frac = (w_frac / rho) / total_vol
                vol_fracs[el] = v_frac
                if el in binders:
                    binder_vol += v_frac

        # Exner formula
        mfp = 0.0
        if 0.0 < binder_vol < 1.0:
            mfp = (2/3) * (binder_vol / (1 - binder_vol)) * particle_size_um
            
        return {
            'Binder Vol Frac': round(binder_vol, 4),
            'Mean Free Path (um)': round(mfp, 4),
            'Theoretical Density (g/cm^3)': round(theoretical_density, 4)
        }

    def calculate_binder_physics(self, full_composition: Dict[str, float], sinter_temp_c: Optional[float] = None) -> Dict[str, float]:
        """
        Calculates advanced binder physics including liquidus temp and mismatches.
        """
        # Identify binder elements
        binder_comp = {el: amt for el, amt in full_composition.items() if el not in ['C', 'N', 'B', 'O']}
        total_binder = sum(binder_comp.values())
        
        if total_binder == 0: return {}
        binder_comp = {k: v/total_binder for k, v in binder_comp.items()} # Normalize
        
        # Melt Point & T_homo
        t_lin = 0.0
        for el, frac in binder_comp.items():
            tm = self.db.get_property(el, 'melting_point')
            if tm: t_lin += frac * tm
            
        s_mix_binder = -sum(c * math.log(c) for c in binder_comp.values() if c > 0)
        t_liq = t_lin - (50 * s_mix_binder) # Deep eutectic heuristic
        
        t_homo = 0.0
        if sinter_temp_c is not None and t_liq > 0:
             t_homo = (sinter_temp_c + 273.15) / t_liq
             
        # Mismatches (Lattice, Modulus, CTE, Wettability)
        params = {'vec': 0.0, 'a_mix': 0.0, 'g_mix': 0.0, 'cte_mix': 0.0, 'wet_index': 0.0}
        
        for el, frac in binder_comp.items():
            props = {
                'vec': self.db.get_property(el, 'vec') or self.element_data.get(el, {}).get('vec'),
                'r': self.db.get_property(el, 'r') or self.element_data.get(el, {}).get('r'),
                'g': self.db.get_property(el, 'shear_modulus_GPa'),
                'cte': self.db.get_property(el, 'cte_micron_per_k'),
                'wet': self.db.get_property(el, 'wettability_index_wc')
            }
            
            # VEC
            if props['vec']: params['vec'] += frac * props['vec']
            
            # Lattice Constant
            a_el = self.db.get_property(el, 'lattice_constant_angstrom')
            if not a_el and props['r']:
                # Approximate FCC vs BCC radius
                factor = 2 * math.sqrt(2) if (params['vec'] >= 8.0) else (4 / math.sqrt(3))
                a_el = props['r'] * factor
            if a_el: params['a_mix'] += frac * a_el
            
            # Others
            if props['g']: params['g_mix'] += frac * props['g']
            if props['cte']: params['cte_mix'] += frac * props['cte']
            if props['wet']: params['wet_index'] += frac * props['wet']

        # Compare with WC targets
        wc = self.wc_props
        epsilon = (params['a_mix'] - wc.get('a', 2.906)) / wc.get('a', 2.906) if params['a_mix'] else 0.0
        delta_g = abs(params['g_mix'] - wc.get('G', 283.0))
        delta_cte = abs(params['cte_mix'] - wc.get('alpha', 5.2))
        
        # Sigma Phase Risk
        sigma_risk = 0
        if 6.8 <= params['vec'] <= 8.2:
            sigma_risk += 1
            if any(x in binder_comp for x in ['Cr', 'V', 'Mo']):
                sigma_risk += 1
                
        # C Deficiency
        c_def = 0.0
        for el, frac in binder_comp.items():
            # Simply check Mono-carbide formation Enthalpy as proxy
            hf = self.db.get_formation_enthalpy(f"{el}C") or 0.0
            c_def += frac * hf

        return {
            'T_liquidus (K)': round(t_liq, 2),
            'T_liquidus_Ideal (K)': round(t_lin, 2),
            'Homologous Temp': round(t_homo, 4),
            'Lattice Mismatch (%)': round(epsilon * 100, 4),
            'Shear Modulus Diff (GPa)': round(delta_g, 2),
            'CTE Mismatch (um/m/K)': round(delta_cte, 2),
            'Wettability Index (0-10)': round(params['wet_index'], 2),
            'Sigma Phase Risk': sigma_risk,
            'C Deficiency Potential': round(c_def, 2)
        }

    def process_batch(self, formulas_list: List[str]) -> pd.DataFrame:
        """Batch processes a list of formula strings."""
        df = pd.DataFrame({'Formula': formulas_list})
        return self.process_batch_extended(df, 'Formula')

    def process_batch_extended(self, 
                             df: pd.DataFrame, 
                             formula_col: str, 
                             grain_size_col: Optional[str] = None, 
                             particle_size_default: float = 1.0, 
                             is_weight_percent: bool = False) -> pd.DataFrame:
        """
        Extends a dataframe with calculated properties used in HEA Cermet Lab.
        """
        results = []
        formulas = df[formula_col].astype(str).tolist()
        
        grain_sizes = df[grain_size_col].astype(float).tolist() if (grain_size_col and grain_size_col in df.columns) else [particle_size_default] * len(formulas)
        
        # Attempt to find common temperature columns
        temp_col = next((c for c in ['Sinter_Temp', 'Temperature', 'T_sinter', 'Process_Temp'] if c in df.columns), None)
        sinter_temps = df[temp_col].astype(float).tolist() if temp_col else [None] * len(formulas)

        for i, f in enumerate(formulas):
            comp = self.parse_formula(f)
            if comp:
                # 1. Basic HEA Props
                props = self.calculate_properties(comp)
                
                # 2. Enthalpy
                props['Enthalpy_mix (kJ/mol)'] = round(self.calculate_enthalpy(comp), 4)
                
                # 3. Cermet Props
                cermet_props = self.calculate_cermet_properties(
                    comp, 
                    particle_size_um=grain_sizes[i], 
                    is_weight_percent=is_weight_percent
                )
                props.update(cermet_props)
                
                # 4. Physics using Atomic composition
                atomic_comp = comp
                if is_weight_percent:
                    # Conversion needed for physics (Tm, VEC, etc rely on atomic)
                    mols = {}
                    for el, wt in comp.items():
                        mass = self.db.get_property(el, 'mass') or self.element_data.get(el, {}).get('mass')
                        if mass: mols[el] = wt / mass
                    
                    total_mol = sum(mols.values())
                    if total_mol > 0:
                        atomic_comp = {k: v/total_mol for k, v in mols.items()}
                        
                physics_props = self.calculate_binder_physics(atomic_comp, sinter_temp_c=sinter_temps[i])
                props.update(physics_props)
                
                results.append(props)
            else:
                results.append({'Error': 'Invalid Composition'})
                
        df_res = pd.DataFrame(results)
        return pd.concat([df.reset_index(drop=True), df_res], axis=1)
