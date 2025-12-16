
import math
from typing import Dict, Optional, Tuple, List
try:
    from pymatgen.core import Element
except ImportError:
    Element = None
    print("Warning: pymatgen not found. Some calculations will be limited.")
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
        Calculate Valence Electron Concentration (VEC) based on Guo's definition.
        VEC = sum(ci * VECi)
        Uses values from core.material_database (e.g. Al=3, not 13).
        """
        vec = 0.0
        total_fraction = sum(composition.values())
        
        for el_str, fraction in composition.items():
            # Use database 'vec' property which follows Guo's standard (e.g. Al=3)
            # Fallback to Element.group is risky for Al/Si if not in DB, but DB covers standard HEA elements.
            v = db.get_property(el_str, 'vec')
            
            if v is None:
                # Fallback attempts
                try:
                    if Element:
                        el = Element(el_str)
                        # For transition metals, group number is usually fine.
                        v = el.group
                        if v > 12: 
                            v -= 10 # Rough heuristic for p-block (Al 13->3, Si 14->4)
                    else:
                        v = 0.0
                except:
                    v = 0.0
            
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
            if not Element:
                continue
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
                if not Element:
                    continue
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
                if not Element:
                    tm = 0
                else:
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

    @staticmethod
    def calculate_average_resistivity(composition: Dict[str, float]) -> Optional[float]:
        """
        Calculate the weighted average electrical resistivity (Ohm m).
        Note: HEA resistivity is usually much higher due to scattering (Nordheim rule),
        this calculates the 'Ideal' rule of mixtures base value.
        """
        rho_mix = 0.0
        total_fraction = sum(composition.values())
        
        for el_str, fraction in composition.items():
            if not Element:
                return None
            try:
                el = Element(el_str)
                # electrical_resistivity is in ohm m? 
                # pymatgen gives it in units (check docs? usually ohm m or micro ohm cm)
                # Pymatgen 2024: electrical_resistivity is in ohm m usually.
                # But sometimes it's None.
                rho = el.electrical_resistivity
                if rho is None:
                    # Fallback for common elements if needed or just skip
                    continue
                rho_mix += (fraction / total_fraction) * rho
            except:
                continue
                
        return rho_mix if rho_mix > 0 else None

    @staticmethod
    def estimate_youngs_modulus_mixture(composition: Dict[str, float]) -> Optional[float]:
        """
        Estimate Young's Modulus using Rule of Mixtures (GPa).
        E_mix = sum(fi * Ei)
        """
        e_mix = 0.0
        total_fraction = sum(composition.values())
        valid_count = 0
        
        for el_str, fraction in composition.items():
            if not Element:
                return None
            try:
                el = Element(el_str)
                # Youngs modulus in GPa. 
                # Pymatgen: youngs_modulus.
                e_val = el.youngs_modulus
                if e_val is None:
                    continue
                e_mix += (fraction / total_fraction) * e_val
                valid_count += 1
            except:
                continue
                
        # If we missed too many major elements, return None?
        # For now, if we have any data, return it
        return e_mix if valid_count > 0 else None

    @staticmethod
    def analyze_bonding_character(composition: Dict[str, float]) -> Dict[str, float]:
        """
        Analyze bonding character based on Electronegativity Difference.
        Returns dictionary with:
        - electronegativity_difference
        - average_electronegativity
        - ionic_character_percent (Pauling equation approximation)
        """
        delta_chi = HEACalculator.calculate_electronegativity_difference(composition)
        
        # Calculate X_bar again (optimization: reuse if called from elsewhere)
        x_bar = 0.0
        total_fraction = sum(composition.values())
        if Element:
             for el_str, fraction in composition.items():
                try:
                    x_bar += (fraction / total_fraction) * Element(el_str).X
                except: pass
        
        # Pauling Ionic Character % = 100 * (1 - exp(- (delta_x / 2)^2 ))?
        # Or simple linear approx?
        # Pauling's formula for single bond A-B: 1 - exp(-0.25 * (Xa - Xb)^2)
        # We use delta_chi as an 'averaged' difference?
        # Let's use the formula on the aggregate delta_chi for a rough 'Global Ionicity'
        
        ionic_pct = 100 * (1 - math.exp(-0.25 * (delta_chi ** 2)))
        
        return {
            "electronegativity_difference": delta_chi,
            "average_electronegativity": x_bar,
            "ionic_character_percent": ionic_pct,
            "covalent_character_percent": 100.0 - ionic_pct
        }

    @staticmethod
    def predict_properties_from_bonding(composition: Dict[str, float]) -> Dict[str, Optional[float]]:
        """
        Predict Young's Modulus and Hardness using Electronegativity Difference mechanism.
        Uses heuristics if exact coefficients are not calibrated.
        """
        # 1. Get Base Modulus (Rule of Mixtures)
        e_rom = HEACalculator.estimate_youngs_modulus_mixture(composition)
        bonding = HEACalculator.analyze_bonding_character(composition)
        delta_chi = bonding["electronegativity_difference"]
        
        # Heuristic: 
        # Higher Ionic Character (Delta Chi) -> Stronger bond energy/stiffness?
        # Often Covalent/Ionic mix is harder than Metallic.
        # But high Delta Chi in HEAs might imply intermetallics (brittle).
        
        # Proposed correction/prediction:
        # Hardness is often correlated with E. H ~ E/10 to E/20.
        # Using a bonding correction factor?
        # For now, we return the Rule-Of-Mixtures E and an estimated H based on E.
        
        # Hardness estimation (approx): Hv = 0.06 * E (common for ceramics/intermetallics)
        # Adjusted by bonding?
        # Let's provide the E_mix and a predicted Hardness.
        
        if e_rom is None:
            return {"predicted_youngs_modulus": None, "predicted_hardness_bonding": None}
            
        # Hardness prediction based on E and Ionicity?
        # Purely heuristic placeholder as per user request to "Establish... mechanism"
        # We will assume H increases with Ionic Character component? 
        
        hv_est = 0.06 * e_rom # Trivial E -> H
        
        return {
            "predicted_youngs_modulus": e_rom,
            "predicted_hardness_bonding": hv_est, # GPa
            "bonding_ionic_pct": bonding["ionic_character_percent"]
        }

# Global instance
hea_calc = HEACalculator()
