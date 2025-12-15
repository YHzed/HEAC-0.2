import re
import math
import pandas as pd
import numpy as np
from .material_database import db as material_db

# Basic Element Properties Database (Simplified for demonstration)
# Data source key: 
# 'r': Atomic Radius (Angstrom) - standard empircal
# 'vec': Valence Electron Concentration
# 'mass': Atomic mass
# Basic Element Properties Database
# 'r': Atomic Radius (Angstrom) - standard empircal
# 'vec': Valence Electron Concentration
# 'mass': Atomic mass (amu)
# 'rho': Density (g/cm^3) at RT
# ELEMENT_DATA = {
#     'Al': {'r': 1.43, 'vec': 3, 'mass': 26.98, 'rho': 2.70},
#     'Co': {'r': 1.25, 'vec': 9, 'mass': 58.93, 'rho': 8.90},
#     'Cr': {'r': 1.28, 'vec': 6, 'mass': 51.99, 'rho': 7.19},
#     'Cu': {'r': 1.28, 'vec': 11, 'mass': 63.55, 'rho': 8.96},
#     'Fe': {'r': 1.26, 'vec': 8, 'mass': 55.85, 'rho': 7.87},
#     'Mn': {'r': 1.27, 'vec': 7, 'mass': 54.94, 'rho': 7.21},
#     'Ni': {'r': 1.24, 'vec': 10, 'mass': 58.69, 'rho': 8.90},
#     'Ti': {'r': 1.47, 'vec': 4, 'mass': 47.87, 'rho': 4.50},
#     'V':  {'r': 1.34, 'vec': 5, 'mass': 50.94, 'rho': 6.11},
#     'Zr': {'r': 1.60, 'vec': 4, 'mass': 91.22, 'rho': 6.52},
#     'Nb': {'r': 1.46, 'vec': 5, 'mass': 92.91, 'rho': 8.57},
#     'Mo': {'r': 1.39, 'vec': 6, 'mass': 95.95, 'rho': 10.28},
#     'Hf': {'r': 1.59, 'vec': 4, 'mass': 178.49, 'rho': 13.31},
#     'Ta': {'r': 1.46, 'vec': 5, 'mass': 180.95, 'rho': 16.69},
#     'W':  {'r': 1.39, 'vec': 6, 'mass': 183.84, 'rho': 19.25},
#     'C':  {'r': 0.77, 'vec': 4, 'mass': 12.01, 'rho': 2.26}, 
#     'N':  {'r': 0.75, 'vec': 5, 'mass': 14.01, 'rho': 0.00125}, # Gas usually, but interstitial in lattice
#     'Si': {'r': 1.18, 'vec': 4, 'mass': 28.09, 'rho': 2.33},
#     'B':  {'r': 0.90, 'vec': 3, 'mass': 10.81, 'rho': 2.34},
# }

# Simplified approx Mixing Enthalpy (kJ/mol) for selected binary pairs (i, j)
# Based on Miedema model values found in literature (Takeuchi & Inoue etc)
# Key: frozenset({el1, el2}) -> value
# This is a small subset for demonstration.
# BINARY_ENTHALPY = { ... } (managed by enthalpy.json now)

# Standard Properties for WC (Alpha) - Target Ceramic
P_WC = {
    'a': 2.906, # Angstrom (Hexagonal a-axis matches FCC (111) or BCC (110) in epitaxy)
    'c': 2.837, # Angstrom (Hexagonal c-axis)
    'G': 283.0, # GPa (Shear Modulus)
    'Tm': 3143.0, # Kelvin (Melting Point, approx)
    'alpha': 5.2, # CTE (um/m/K)
    'H0': 1600.0, # HV, intrinsic coarse grain hardness (approx)
    'K_hp': 600.0 # Hall-Petch constant (HV * um^0.5)
}

class MaterialProcessor:
    def __init__(self):
        # Use the shared database instance
        self.db = material_db
        # Use HEACalculator for core HEA property calculations
        from .hea_calculator import hea_calc
        self.hea_calc = hea_calc

    def parse_formula(self, formula_str):
        """
        Parses a chemical formula string into a dictionary of {Element: MoleFraction}.
        Supports formats like "AlCoCrFeNi", "Al10Co20...", "Al1.5Co...".
        """
        formula_str = formula_str.strip()
        # Regex to match Element name and optional amount
        # matches: ('Al', '1.5'), ('Co', ''), ...
        matches = re.findall(r'([A-Z][a-z]*)(\d*\.?\d*)', formula_str)
        
        composition = {}
        total_moles = 0.0
        
        valid_elements = True
        
        for el, amt in matches:
            if not self.db.get_element(el):
                # Fallback or strict error? For now, ignore or mark unknown
                # Ideally, we should maybe error out, but let's just skip for robustness in demo
                valid_elements = False
                continue
                
            amount = float(amt) if amt else 1.0
            composition[el] = composition.get(el, 0.0) + amount
            total_moles += amount
            
        if total_moles == 0:
            return None
        
        # Normalize to fractions
        normalized_comp = {k: v / total_moles for k, v in composition.items()}
        return normalized_comp

    def calculate_properties(self, composition):
        """
        Calculates basic HEA properties:
        - Mixing Entropy (S_mix) [R]
        - Valence Electron Concentration (VEC)
        - Atomic Size Difference (delta) [%]
        
        Uses HEACalculator for core calculations to ensure consistency.
        """
        if not composition:
            return None
            
        # 1. Mixing Entropy: S_mix = -R * sum(c_i * ln(c_i))
        # We will return it in units of R (gas constant), so calculation is just -sum(...)
        s_mix_R = -sum(c * math.log(c) for c in composition.values() if c > 0)
        
        # 2. VEC: Use HEACalculator for consistency (newer version)
        vec_avg = self.hea_calc.calculate_vec(composition)
        
        # 3. Atomic Size Difference: Use HEACalculator for consistency (newer version)
        delta = self.hea_calc.calculate_atomic_size_difference(composition)
        
        return {
            'S_mix (R)': round(s_mix_R, 4),
            'VEC': round(vec_avg, 4),
            'Delta (%)': round(delta, 4)
        }

    def calculate_enthalpy(self, composition):
        """
        Calculates mixing enthalpy.
        
        Uses HEACalculator for consistency (newer version).
        """
        return self.hea_calc.calculate_mixing_enthalpy(composition)

    def calculate_cermet_properties(self, composition, particle_size_um=1.0, is_weight_percent=False):
        """
        Calculates specific properties:
        - Binder Volume Fraction
        - Mean Free Path (Exner)
        
        Args:
            composition: Dictionary of Element/Phase -> Amount.
            particle_size_um: Grain size in microns.
            is_weight_percent: If True, values in composition are treated as weight ratios (e.g. Co=10, WC=90).
                               If False, values are treated as ATOMIC ratios (e.g. W=1, C=1, Co=0.1).
        """
        # Heuristic to identify binder 
        binders = {'Co', 'Ni', 'Fe', 'Al', 'Cu', 'Mn'}
        
        weight_fracs = {}
        
        if is_weight_percent:
            # Input is already weight (e.g. 10.0, 90.0)
            total_w = sum(composition.values())
            if total_w == 0:
                return {}
            weight_fracs = {k: v/total_w for k,v in composition.items()}
        else:
            # Input is Atomic -> Convert to Weight
            # Atomic Fraction * Atomic Mass -> Weight -> Normalize
            total_weight = 0.0
            
            for el, atomic_frac in composition.items():
                mass = self.db.get_property(el, 'mass')
                if mass is not None:
                    w = atomic_frac * mass
                    total_weight += w
                else:
                    # Missing data for element (or compound key like WC)
                    return {} 
            
            if total_weight == 0:
                return {}
                
            for el, atomic_frac in composition.items():
                 mass = self.db.get_property(el, 'mass')
                 # Already checked not None above, but safe
                 if mass:
                    w = atomic_frac * mass
                    weight_fracs[el] = w / total_weight
             
        # Normalize Weight Fractions (just to be safe)
        
        # Weight -> Volume Conversion
        # Vol_i = (Wt_i / Rho_i) 
        # VolFrac_i = Vol_i / Sum(Vol_k)
        
        total_vol = 0.0
        vol_fracs = {}
        
        for el, w_frac in weight_fracs.items():
            rho = self.db.get_property(el, 'rho')
            if rho is not None:
                v = w_frac / rho
                total_vol += v
            else:
                # If key is not in DB (e.g. "WC"), we fail.
                # Assuming input is decomposed to elements OR we add "WC" to DB.
                # For Cermet formulas like "AlCo...", they are elements.
                return {} 
                
        if total_vol == 0:
            return {}
            
        theoretical_density = 1.0 / total_vol
            
        binder_vol = 0.0
        
        for el, w_frac in weight_fracs.items():
            rho = self.db.get_property(el, 'rho')
            # Safe logic
            if rho:
                v_frac = (w_frac / rho) / total_vol
                vol_fracs[el] = v_frac
                if el in binders:
                    binder_vol += v_frac
                
        # Mean Free Path (Exner)
        # lambda = 2/3 * (V_binder / (1 - V_binder)) * d_grain
        if binder_vol >= 1.0 or binder_vol <= 0.0:
            mfp = 0.0 # Undefined or monolithic
        else:
            mfp = (2/3) * (binder_vol / (1 - binder_vol)) * particle_size_um
            
        return {
            'Binder Vol Frac': round(binder_vol, 4),
            'Mean Free Path (um)': round(mfp, 4),
            'Theoretical Density (g/cm^3)': round(theoretical_density, 4)
        }

    def calculate_binder_physics(self, full_composition, sinter_temp_c=None):
        """
        Calculates advanced physics-based features for the binder phase.
        Identifies binder elements, isolates them, and computes:
        - T_liquidus (Corrected with Deep Eutectic model)
        - Homologous Temperature (if sinter_temp_c provided)
        - Lattice Mismatch (vs WC)
        - CTE Mismatch (vs WC) [NEW]
        - Wettability Index (vs WC) [NEW]
        - Sigma Phase Risk [NEW]
        - Sigma Phase Risk [NEW]
        - Carbon Deficiency Potential
        - Active Element Sum (Wettability Proxy) [NEW]
        """
        # 1. Identify Binder Phase (Heuristic: exclude C, N, B, O)
        binder_elements = {}
        non_binder_sum = 0.0
        
        for el, amt in full_composition.items():
            if el not in ['C', 'N', 'B', 'O']:
                binder_elements[el] = amt
            else:
                non_binder_sum += amt
        
        # Normalize binder composition
        total_binder = sum(binder_elements.values())
        if total_binder == 0:
            return {}
            
        binder_comp = {k: v/total_binder for k,v in binder_elements.items()}
        
        # --- 1. Melting Point & T_homo (Deep Eutectic Correction) ---
        # T_liq linear = sum(c_i * Tm_i)
        t_lin = 0.0
        for el, frac in binder_comp.items():
            tm = self.db.get_property(el, 'melting_point')
            if tm:
                t_lin += frac * tm
        
        # Mixing Entropy of Binder
        s_mix_binder = -sum(c * math.log(c) for c in binder_comp.values() if c > 0)
        
        # Correction: T_liq = T_lin - K * S_mix
        # K is heuristic constant. For eutectics, significant drop. 
        # Using K=50 approx.
        t_liq = t_lin - (50 * s_mix_binder)
        
        t_homo = 0.0
        if sinter_temp_c is not None and t_liq > 0:
            t_sinter_k = sinter_temp_c + 273.15
            t_homo = t_sinter_k / t_liq
            
        # --- 2. Lattice Mismatch ---
        vec = 0.0
        for el, frac in binder_comp.items():
            v = self.db.get_property(el, 'vec')
            if v: vec += frac * v
            
        a_mix = 0.0
        for el, frac in binder_comp.items():
            a_el = self.db.get_property(el, 'lattice_constant_angstrom')
            # Fallback
            if not a_el:
                r_el = self.db.get_property(el, 'r')
                if r_el:
                    if vec >= 8.0: # FCC
                        a_el = r_el * 2 * math.sqrt(2) 
                    else: # BCC
                        a_el = r_el * 4 / math.sqrt(3) 
            
            if a_el:
                a_mix += frac * a_el
                
        # Mismatch epsilon
        # NOTE: This assumes FCC-like binder vs WC (HCP). 
        # A geometric simplification as WC a=2.906 is often compared to FCC d_111 or similar projected spacings.
        epsilon = 0.0
        epsilon_c = 0.0
        if a_mix > 0:
            epsilon = (a_mix - P_WC['a']) / P_WC['a']
            # Additional feature: Mismatch vs c-axis (assuming isotropic binder a_mix compares to c_WC)
            # This captures distortion if epitaxy is on prism planes or other orientations.
            epsilon_c = (a_mix - P_WC['c']) / P_WC['c']
            
        # --- 3. Modulus Mismatch ---
        g_mix = 0.0
        for el, frac in binder_comp.items():
            g_el = self.db.get_property(el, 'shear_modulus_GPa')
            if g_el:
                g_mix += frac * g_el
                
        delta_G = abs(g_mix - P_WC['G'])

        # --- 4. CTE Mismatch [NEW] ---
        # alpha_mix
        cte_mix = 0.0
        for el, frac in binder_comp.items():
            c = self.db.get_property(el, 'cte_micron_per_k')
            if c:
                cte_mix += frac * c
        
        # Mismatch vs WC
        delta_cte = abs(cte_mix - P_WC['alpha'])

        # --- 5. Wettability Index [NEW] ---
        # Note: Wettability is non-linear. "Active Element Sum" is added as a supplementary feature.
        wet_index = 0.0
        active_elements = {'Ti', 'Zr', 'Hf', 'V', 'Nb', 'Ta', 'Cr', 'Mo', 'W', 'Mn'}
        active_sum = 0.0
        
        for el, frac in binder_comp.items():
            w = self.db.get_property(el, 'wettability_index_wc')
            if w is not None:
                wet_index += frac * w
            if el in active_elements:
                active_sum += frac

        
        # --- 6. Sigma Phase Risk [NEW] ---
        # Rule of thumb: VEC [6.8, 8.0] is high risk for Sigma in HEAs (esp with Cr/V/Mo)
        # Also geometric distortion helps driving it? 
        sigma_risk_score = 0
        if 6.8 <= vec <= 8.2:
            sigma_risk_score += 1
            if 'Cr' in binder_comp or 'V' in binder_comp or 'Mo' in binder_comp:
                sigma_risk_score += 1
        
        c_deficiency = 0.0
        for el, frac in binder_comp.items():
            carbide_formulas = [f"{el}C", f"{el}2C", f"{el}3C2"]
            hf_val = 0.0
            for form in carbide_formulas:
                 val = self.db.get_formation_enthalpy(form)
                 if val:
                     if "3C2" in form: val /= 3
                     elif "2C" in form: val /= 2
                     hf_val = val
                     break
            c_deficiency += frac * hf_val
             
        return {
            'T_liquidus (K)': round(t_liq, 2),
            'T_liquidus_Ideal (K)': round(t_lin, 2), # Keep old for comparison
            'Homologous Temp': round(t_homo, 4),
            'Lattice Mismatch (%)': round(epsilon * 100, 4),
            'Lattice Mismatch c-axis (%)': round(epsilon_c * 100, 4),
            'Shear Modulus Diff (GPa)': round(delta_G, 2),
            'CTE Mismatch (um/m/K)': round(delta_cte, 2),
            'Wettability Index (0-10)': round(wet_index, 2),
            'Active Element Sum': round(active_sum, 4),
            'Sigma Phase Risk': sigma_risk_score,
            'C Deficiency Potential': round(c_deficiency, 2)
        }

    def calculate_wc_hardness(self, grain_size_um):
        """
        Calculate WC intrinsic hardness using Hall-Petch relation.
        H_WC(d) = H0 + K_hp / sqrt(d)
        """
        if grain_size_um <= 0:
            return P_WC['H0']
        return P_WC['H0'] + (P_WC['K_hp'] / math.sqrt(grain_size_um))

    def calculate_composite_hardness(self, binder_hardness_hv, vol_frac_binder, grain_size_um):
        """
        Calculate Cermet Composite Hardness.
        
        Args:
            binder_hardness_hv: Hardness of the binder (HV).
            vol_frac_binder: Volume fraction of binder (0.0 - 1.0).
            grain_size_um: WC grain size in microns.
            
        Returns:
            Dict with predicted hardness values (HV).
        """
        if binder_hardness_hv is None or vol_frac_binder is None:
            return {}
            
        # 1. Calculate WC effective hardness
        h_wc = self.calculate_wc_hardness(grain_size_um)
        
        # 2. Rule of Mixtures (Linear) - Upper Bound usually
        # H_rom = V_wc * H_wc + V_bind * H_bind
        v_wc = 1.0 - vol_frac_binder
        h_rom = (v_wc * h_wc) + (vol_frac_binder * binder_hardness_hv)
        
        # 3. Geometric Mean Model (Gong's) - Usually fits better for Cermets
        # H_geo = H_wc^V_wc * H_bind^V_bind
        # Avoid log(0)
        try:
             h_geo = (h_wc ** v_wc) * (binder_hardness_hv ** vol_frac_binder)
        except:
             h_geo = 0.0
             
        # 4. Lee-Gurland type manually? 
        # For now, ROM and Geo are good baselines.
        
        return {
            'Predicted Hardness (ROM) [HV]': round(h_rom, 1),
            'Predicted Hardness (Geo) [HV]': round(h_geo, 1),
            'WC Intrinsic Hardness [HV]': round(h_wc, 1)
        }

    def process_batch(self, formulas_list):
        """
        Simple batch processing for a list of formulas.
        Returns a DataFrame with results.
        """
        df = pd.DataFrame({'Formula': formulas_list})
        return self.process_batch_extended(df, 'Formula')

    def process_batch_extended(self, df, formula_col, grain_size_col=None, particle_size_default=1.0, is_weight_percent=False):
        results = []
        formulas = df[formula_col].astype(str).tolist()
        
        # Check if grain size column exists
        grain_sizes = []
        if grain_size_col and grain_size_col in df.columns:
            grain_sizes = df[grain_size_col].astype(float).tolist()
        else:
            grain_sizes = [particle_size_default] * len(formulas)
            
        # Check for Sinter/Process Temp column
        sinter_temps = []
        possible_temp_cols = ['Sinter_Temp', 'Temperature', 'T_sinter', 'Process_Temp']
        temp_col = next((c for c in possible_temp_cols if c in df.columns), None)
        
        if temp_col:
            sinter_temps = df[temp_col].astype(float).tolist()
        else:
            sinter_temps = [None] * len(formulas)
            
        for i, f in enumerate(formulas):
            comp = self.parse_formula(f)
            if comp:
                # Basic HEA
                props = self.calculate_properties(comp)
                
                # Enthalpy
                props['Enthalpy_mix (kJ/mol)'] = round(self.calculate_enthalpy(comp), 4)
                
                # Cermet
                # If is_weight_percent=True, 'comp' (parsed from string) acts as weight map
                cermet_props = self.calculate_cermet_properties(
                    comp, 
                    particle_size_um=grain_sizes[i], 
                    is_weight_percent=is_weight_percent
                )
                props.update(cermet_props)
                
                # Advanced Physics Features
                # Calculate based on ATOMIC composition (so if input was weight, we might need converted atomic comp)
                # But parse_formula returns 'comp' which is treated as atomic unless 'is_weight_percent' flag says otherwise in context of density calc.
                # However, calculate_properties treats 'comp' as atomic. 
                # If 'is_weight_percent' is True, self.parse_formula(f) still returns numbers.
                # If those numbers are weights, we need to convert to atomic for physics calcs (VEC, Melting Point).
                
                atomic_comp = comp
                if is_weight_percent:
                    # Convert Weight (comp) -> Atomic
                    # mol = wt / atomic_mass
                    mols = {}
                    for el, wt in comp.items():
                        mass = self.db.get_property(el, 'mass')
                        if mass:
                            mols[el] = wt / mass
                    # Normalize
                    total_mol = sum(mols.values())
                    if total_mol > 0:
                        atomic_comp = {k: v/total_mol for k,v in mols.items()}
                
                physics_props = self.calculate_binder_physics(atomic_comp, sinter_temp_c=sinter_temps[i])
                props.update(physics_props)
                
                results.append(props)
            else:
                results.append({'Error': 'Invalid Composition'})
                
        # Convert list of dicts to DF
        df_res = pd.DataFrame(results)
        
        # Concat with original
        return pd.concat([df.reset_index(drop=True), df_res], axis=1)
