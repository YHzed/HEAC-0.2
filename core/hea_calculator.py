
import math
from typing import Dict, Optional, Tuple, List
from pymatgen.core import Element
from core.material_database import db

# Universal gas constant in J/(mol K)
R_GAS = 8.314

class HEACalculator:
    """
    Calculator for High Entropy Alloy specific parameters and property estimations.
    """
    
    @staticmethod
    def calculate_vec(composition: Dict[str, float]) -> float:
        """
        Calculate Valence Electron Concentration (VEC).
        VEC = sum(ci * VECi)
        """
        vec = 0.0
        total_fraction = sum(composition.values())
        
        for el_str, fraction in composition.items():
            el = Element(el_str)
            # pymatgen might return None for some valence properties depending on data source
            # But usually group number is good proxy for VEC in this context?
            # Actually standard VEC definition uses:
            # - Transition metals: total s + d electrons (Group number)
            # - Pre-transition: Group number
            # - Post-transition/Non-metals: Group number usually works or valence shell e-
            
            # Using periodic table group is the standard definition for Guo's VEC
            v = el.group
            vec += (fraction / total_fraction) * v
            
        return vec

    @staticmethod
    def calculate_atomic_size_difference(composition: Dict[str, float]) -> float:
        """
        Calculate atomic size difference (delta).
        delta = sqrt(sum(ci * (1 - ri/r_bar)**2)) * 100
        """
        r_bar = 0.0
        radii = {}
        total_fraction = sum(composition.values())
        
        # 1. Calculate average radius
        for el_str, fraction in composition.items():
            el = Element(el_str)
            r = el.atomic_radius
            if r is None:
                continue # Skip if no radius (shouldn't happen for metals)
            radii[el_str] = r
            r_bar += (fraction / total_fraction) * r
            
        if r_bar == 0:
            return 0.0
            
        # 2. Calculate delta
        sq_diff_sum = 0.0
        for el_str, fraction in composition.items():
            if el_str not in radii:
                continue
            r = radii[el_str]
            sq_diff_sum += (fraction / total_fraction) * ((1 - r/r_bar) ** 2)
            
        return math.sqrt(sq_diff_sum) * 100

    @staticmethod
    def calculate_electronegativity_difference(composition: Dict[str, float]) -> float:
        """
        Calculate electronegativity difference (delta_chi).
        delta_chi = sqrt(sum(ci * (Xi - X_bar)**2))
        """
        x_bar = 0.0
        xs = {}
        total_fraction = sum(composition.values())
        
        # 1. Calculate average electronegativity
        for el_str, fraction in composition.items():
            try:
                el = Element(el_str)
                x = el.X # Pauling electronegativity
                xs[el_str] = x
                x_bar += (fraction / total_fraction) * x
            except:
                continue
            
        if x_bar == 0:
            return 0.0
            
        # 2. Calculate delta
        sq_diff_sum = 0.0
        for el_str, fraction in composition.items():
            if el_str not in xs:
                continue
            x = xs[el_str]
            sq_diff_sum += (fraction / total_fraction) * ((x - x_bar) ** 2)
            
        return math.sqrt(sq_diff_sum)

    @staticmethod
    def calculate_mixing_entropy(composition: Dict[str, float]) -> float:
        """
        Calculate Mixing Entropy (S_mix) in J/(mol K).
        S_mix = -R * sum(ci * ln(ci))
        """
        s_mix = 0.0
        total_fraction = sum(composition.values())
        
        for fraction in composition.values():
            c = fraction / total_fraction
            if c > 0:
                s_mix += c * math.log(c)
                
        return -R_GAS * s_mix

    @staticmethod
    def calculate_mixing_enthalpy(composition: Dict[str, float]) -> float:
        """
        Calculate Mixing Enthalpy (H_mix) in kJ/mol.
        H_mix = sum_{i<j} 4 * H_{ij}^{mix} * c_i * c_j
        Using the regular solution model approximation where Omega_ij approx 4 * H_mix_binary.
        """
        h_mix = 0.0
        total_fraction = sum(composition.values())
        
        elements = list(composition.keys())
        n = len(elements)
        
        for i in range(n):
            for j in range(i + 1, n):
                el_i = elements[i]
                el_j = elements[j]
                c_i = composition[el_i] / total_fraction
                c_j = composition[el_j] / total_fraction
                
                # Get binary enthalpy from database (kJ/mol for equimolar)
                # We multiply by 4 to get Interaction Parameter Omega (Omega approx 4 * H_mix_binary)
                # Validated: Database contains Delta H_mix (at 50-50), not Omega.
                h_binary = db.get_enthalpy(el_i, el_j)
                omega = 4 * h_binary
                
                h_mix += omega * c_i * c_j
                
        return h_mix

    @staticmethod
    def calculate_omega(composition: Dict[str, float], tm_avg: float = None) -> Optional[float]:
        """
        Calculate Omega parameter.
        Omega = Tm_avg * S_mix / |H_mix|
        
        If tm_avg is not provided, it will be calculated from composition.
        H_mix is in kJ/mol, S_mix in J/(mol K). Need to convert units.
        """
        h_mix_kj = HEACalculator.calculate_mixing_enthalpy(composition)
        s_mix_j = HEACalculator.calculate_mixing_entropy(composition)
        
        if abs(h_mix_kj) < 1e-4:
            # Ideally returns infinity for ideal solution (H_mix=0), but let's return None or large number
            return None
            
        if tm_avg is None:
            # Calculate linear average melting point
            tm_avg = 0.0
            total_fraction = sum(composition.values())
            for el_str, fraction in composition.items():
                el = Element(el_str)
                # Use melting_point, handle None
                tm = el.melting_point
                if tm is None: 
                    tm = 0 # Should not happen for metals
                tm_avg += (fraction / total_fraction) * tm
                
        # H_mix is kJ, so multiply by 1000 to match S_mix units (J)
        h_mix_j = h_mix_kj * 1000
        
        return (tm_avg * s_mix_j) / abs(h_mix_j)

    @staticmethod
    def estimate_hardness_chen(bulk_modulus: float, shear_modulus: float) -> Optional[float]:
        """
        Estimate Vickers Hardness using Chen's model.
        NOTE: This predicts the Intrinsic Hardness of the HEA Binder Phase only.
        Hv = 2 * (k^2 * G)^0.585 - 3
        where k = G/B
        Input units: GPa
        Output unit: GPa
        """
        if not bulk_modulus or not shear_modulus or bulk_modulus <= 0:
            return None
            
        k = shear_modulus / bulk_modulus
        g = shear_modulus
        
        try:
            hv = 2 * ((k**2 * g)**0.585) - 3
            return max(0, hv) # Hardness can't be negative
        except:
            return None

    @staticmethod
    def estimate_hardness_tian(bulk_modulus: float, shear_modulus: float) -> Optional[float]:
        """
        Estimate Vickers Hardness using Tian's model.
        NOTE: This predicts the Intrinsic Hardness of the HEA Binder Phase only.
        Hv = 0.92 * (k)^1.137 * G^0.708
        Input units: GPa
        Output unit: GPa
        """
        if not bulk_modulus or not shear_modulus or bulk_modulus <= 0:
            return None
            
        k = shear_modulus / bulk_modulus
        g = shear_modulus
        
        try:
            hv = 0.92 * (k**1.137) * (g**0.708)
            return hv
        except:
            return None
            
    @staticmethod
    def estimate_fracture_toughness_niu(bulk_modulus: float, shear_modulus: float) -> Optional[float]:
        """
        Estimate Fracture Toughness (K_IC) using Niu's correlation (approximated).
        Note: Toughness is complex and this is a rough estimation based on G/B (ductility).
        For now, returns None as a placeholder unless a specific robust formula is provided.
        """
        # Placeholder for future implementation
        return None

# Global instance
hea_calc = HEACalculator()
