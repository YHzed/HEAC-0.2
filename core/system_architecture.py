import math
import numpy as np
import pandas as pd
import optuna
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional

# Re-use existing database
from .material_database import db as material_db

# -----------------------------------------------------------------------------
# 1. Design Space (Input Layer)
# -----------------------------------------------------------------------------
@dataclass
class DesignSpace:
    """
    Represents the input variables for the material design.
    """
    # HEA Metallic phase composition (Elements -> Atomic Fraction)
    hea_composition: Dict[str, float]
    
    # Ceramic phase composition (Compounds -> Volume/Weight Fraction)
    # For simplicity in this demo, we assume fixed WC target, but this allows flexibility
    ceramic_composition: Dict[str, float] = field(default_factory=lambda: {'WC': 1.0})
    
    # Microstructure Targets
    ceramic_vol_fraction: float = 0.5  # User target or Variable
    grain_size_um: float = 1.0
    
    # Process Parameters
    sinter_temp_c: float = 1400.0
    sinter_time_min: float = 60.0

    def get_binder_composition_normalized(self) -> Dict[str, float]:
        """Returns normalized atomic fractions of the HEA binder."""
        total = sum(self.hea_composition.values())
        if total == 0: return {}
        return {k: v/total for k, v in self.hea_composition.items()}

# -----------------------------------------------------------------------------
# 2. Physics Engine (Transformation Layer)
# -----------------------------------------------------------------------------
class PhysicsEngine:
    """
    Transforms DesignSpace inputs into physics-based features.
    """
    def __init__(self):
        self.db = material_db
        # Target WC properties for mismatch calc
        self.wc_props = {
            'a': 2.906,     # Angstrom
            'alpha': 5.2,   # CTE
            'G': 283.0      # Shear Modulus GPa
        }

    def compute_features(self, design: DesignSpace) -> Dict[str, float]:
        """
        Main pipeline to generate all F (Atomic), G (Interface), H (Process) features.
        """
        features = {}
        binder_comp = design.get_binder_composition_normalized()
        
        # --- F. Atomic Features (VEC, Entropy, Enthalpy) ---
        features.update(self._calculate_atomic_features(binder_comp))
        
        # --- G. Interface Features (Mismatch, Wettability) ---
        features.update(self._calculate_interface_features(binder_comp))
        
        # --- H. Process Features (Homologous Temp, Diffusivity proxy) ---
        features.update(self._calculate_process_features(design, binder_comp))
        
        return features

    def calculate_volume_fractions(self, design: DesignSpace) -> Dict[str, float]:
        """
        Calculates the actual Volume Fraction of each phase and element.
        Flow: Atomic % (Binder) -> Weight % -> Volume % (Binder) -> Combined with Ceramic Vol %.
        """
        # 1. Binder Atomic -> Weight
        binder_atomic = design.get_binder_composition_normalized()
        binder_wt = {}
        total_mass = 0.0
        
        for el, atomic in binder_atomic.items():
            mass = self.db.get_property(el, 'mass')
            if mass:
                w = atomic * mass
                binder_wt[el] = w
                total_mass += w
                
        if total_mass == 0: return {}
        # Normalize Binder Weight Fractions
        binder_wt = {k: v/total_mass for k, v in binder_wt.items()}
        
        # 2. Binder Theoretical Density
        # 1/rho_mix = Sum(wt_i / rho_i)
        inv_rho = 0.0
        for el, wt in binder_wt.items():
            rho = self.db.get_property(el, 'rho')
            if rho:
                inv_rho += wt / rho
        
        rho_binder = 0.0
        if inv_rho > 0:
             rho_binder = 1.0 / inv_rho
             
        # 3. Overall Volume Fractions
        vol_ceramic = design.ceramic_vol_fraction
        vol_binder = 1.0 - vol_ceramic
        
        # 4. Element Volume Fractions in Total Composite
        # Vol_el_in_composite = Vol_el_in_binder * Vol_Binder
        # Vol_el_in_binder = (Wt_el / Rho_el) * Rho_binder
        
        vol_fractions = {
            'Phase_Ceramic': vol_ceramic,
            'Phase_Binder': vol_binder
        }
        
        for el, wt in binder_wt.items():
            rho = self.db.get_property(el, 'rho')
            if rho:
                # Volume fraction of element within the binder phase
                vol_in_binder = (wt / rho) * rho_binder
                # Volume fraction of element within the whole composite
                vol_in_total = vol_in_binder * vol_binder
                vol_fractions[f'Elem_Vol_{el}'] = round(vol_in_total, 4)
                
        vol_fractions['Density_Binder_Theoretical'] = round(rho_binder, 3)
        
        return vol_fractions

    def _calculate_atomic_features(self, composition: Dict[str, float]) -> Dict[str, float]:
        if not composition: return {}
        
        # VEC
        vec_sum = 0.0
        for el, f in composition.items():
            v = self.db.get_property(el, 'vec')
            if v: vec_sum += f * v
            
        # Mixing Entropy
        s_mix = -sum(c * math.log(c) for c in composition.values() if c > 0)
        
        # Mixing Enthalpy (Simplified loop)
        elements = list(composition.keys())
        h_mix = 0.0
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                el1, el2 = elements[i], elements[j]
                h_ij = self.db.get_enthalpy(el1, el2)
                h_mix += 4 * h_ij * composition[el1] * composition[el2]

        return {
            'VEC': vec_sum,
            'S_mix': s_mix,
            'H_mix': h_mix
        }

    def _calculate_interface_features(self, composition: Dict[str, float]) -> Dict[str, float]:
        if not composition: return {}
        
        # Lattice Mismatch
        # Approx lattice parameter of binder (Vegard's law based on structure)
        # Simplified: Use atomic radii calc or DB lattice constants if available
        # Here we copy logic: if VEC >= 8 FCC, else BCC
        
        vec_avg = 0.0
        for el, f in composition.items():
            v = self.db.get_property(el, 'vec')
            if v: vec_avg += f * v
            
        a_mix = 0.0
        for el, f in composition.items():
            r = self.db.get_property(el, 'r')
            if not r: continue
            
            # Estimate a_el based on crystal structure assumption
            if vec_avg >= 8.0: # FCC
                a_el = r * 2 * math.sqrt(2)
            else: # BCC
                a_el = r * 4 / math.sqrt(3)
            a_mix += f * a_el
            
        epsilon = 0.0
        if a_mix > 0:
            epsilon = abs(a_mix - self.wc_props['a']) / self.wc_props['a']

        # CTE Mismatch
        cte_mix = 0.0
        for el, f in composition.items():
            c = self.db.get_property(el, 'cte_micron_per_k') # Assuming new DB prop or default
            if c: cte_mix += f * c
        
        delta_cte = abs(cte_mix - self.wc_props['alpha'])

        # Wettability Index (Weighted average of contact angles or work of adhesion proxies)
        wet_index = 0.0
        for el, f in composition.items():
            w = self.db.get_property(el, 'wettability_index_wc')
            if w: wet_index += f * w

        return {
            'Lattice_Mismatch': epsilon,
            'CTE_Mismatch': delta_cte,
            'Wettability_Index': wet_index
        }

    def _calculate_process_features(self, design: DesignSpace, composition: Dict[str, float]) -> Dict[str, float]:
        if not composition: return {}
        
        # Melting Point (Linear Rule of Mixtures for now)
        tm_mix = 0.0
        for el, f in composition.items():
            tm = self.db.get_property(el, 'melting_point')
            if tm: tm_mix += f * tm
            
        # Homologous Temp
        t_sinter_k = design.sinter_temp_c + 273.15
        t_homo = 0.0
        if tm_mix > 0:
            t_homo = t_sinter_k / tm_mix
            
        # Densification Parameter (Toy model: func of T_homo and time)
        # Assume ideal densification > 0.8 T_m
        densification_proxy = t_homo * math.log(design.sinter_time_min + 1)
        
        return {
            'T_liquidus_approx': tm_mix,
            'T_homologous': t_homo,
            'Densification_Factor': densification_proxy
        }

# -----------------------------------------------------------------------------
# 3. AI Predictor (Prediction Layer)
# -----------------------------------------------------------------------------
class AIPredictor:
    """
    Wraps ML models to predict properties from Physics Features.
    """
    def __init__(self):
        # In a real scenario, we would load trained models here (pickle/joblib)
        # self.model_hv = load('model_hv.pkl')
        pass
        
    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Returns dictionary of predicted properties: HV, KIC, Density, etc.
        Using simple analytical equations as placeholders for now.
        """
        vec = features.get('VEC', 8.0)
        mismatch = features.get('Lattice_Mismatch', 0.0)
        t_homo = features.get('T_homologous', 0.8)
        
        # --- Model 1: Interface Quality (0.0 - 1.0) ---
        # Low mismatch + Good wetting (high index) -> Good Interface
        wetting = features.get('Wettability_Index', 5.0) / 10.0 # Norm 0-1
        interface_score = 0.5 * (1.0 - min(mismatch, 1.0)) + 0.5 * wetting
        
        # --- Model 3: Mechanics (HV, KIC) ---
        # Hardness: Increases with VEC (solid solution) but decreases if interface is poor
        # Toy Equation: Base HV (1500) + Solid Solution (VEC) - Porosity(T_homo)
        
        base_hv = 1600.0
        ss_strengthening = abs(vec - 8.0) * 200 # Deviation from stability correlates with strain? Just toy.
        porosity_penalty = max(0, (0.9 - t_homo) * 1000) # Penalty if T < 0.9 Tm
        
        hv_pred = base_hv + ss_strengthening - porosity_penalty
        
        # Fracture Toughness (K1C):
        # Ductile binder (VEC > 8 usually FCC/Ductile) -> Higher K1C
        # Good interface -> Higher K1C
        base_k1c = 10.0
        ductility_bonus = max(0, (vec - 7.5) * 2.0)
        interface_bonus = interface_score * 5.0
        
        k1c_pred = base_k1c + ductility_bonus + interface_bonus
        
        return {
            'Predicted_HV': hv_pred,
            'Predicted_K1C': k1c_pred,
            'Interface_Quality': interface_score
        }

# -----------------------------------------------------------------------------
# 4. Inverse Optimizer (Optimization Layer)
# -----------------------------------------------------------------------------
class InverseOptimizer:
    """
    Uses Genetic Algorithms (NSGA-II via Optuna) to find optimal designs.
    """
    def __init__(self):
        self.physics = PhysicsEngine()
        self.predictor = AIPredictor()
        
    def optimize(self, n_trials=50, target_hv=1800.0, target_k1c=12.0):
        """
        Runs optimization to maximize HV and K1C towards targets.
        """
        
        def objective(trial):
            # 1. Suggest Design Variables (Composition)
            # Elements pool: Co, Ni, Fe, Cr, Mo
            # We fix the total binder fraction to 1.0 (internal normalization)
            
            c_co = trial.suggest_float('Co', 0.0, 1.0)
            c_ni = trial.suggest_float('Ni', 0.0, 1.0)
            c_fe = trial.suggest_float('Fe', 0.0, 1.0)
            c_cr = trial.suggest_float('Cr', 0.0, 0.5) # Limit Cr to avoid sigma
            c_mo = trial.suggest_float('Mo', 0.0, 0.3)
            
            # Sintering Temp variable
            t_sinter = trial.suggest_float('T_sinter', 1200, 1500)
            
            # Construct Design
            comp = {'Co': c_co, 'Ni': c_ni, 'Fe': c_fe, 'Cr': c_cr, 'Mo': c_mo}
            
            # Check if valid (sum > 0)
            if sum(comp.values()) < 1e-3:
                # Penalty
                return -1.0, -1.0
            
            design = DesignSpace(
                hea_composition=comp,
                sinter_temp_c=t_sinter
            )
            
            # 2. Physics Engine
            feats = self.physics.compute_features(design)
            
            # 3. Predictor
            preds = self.predictor.predict(feats)
            
            # 4. Objective
            # We want to MAXIMIZE HV and MAXIMIZE K1C
            # Optuna default is Minimize, so we return negative or set direction='maximize'
            
            return preds['Predicted_HV'], preds['Predicted_K1C']
            
        # NSGA-II Sampler
        sampler = optuna.samplers.NSGAIISampler()
        study = optuna.create_study(
            directions=['maximize', 'maximize'],
            sampler=sampler
        )
        
        study.optimize(objective, n_trials=n_trials)
        
        return study.best_trials
