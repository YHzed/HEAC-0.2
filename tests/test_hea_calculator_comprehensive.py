import unittest
from core.hea_calculator import hea_calc
from core.material_database import db

class TestHEACalculatorComprehensive(unittest.TestCase):
    """
    Comprehensive tests for HEACalculator using known theoretical values.
    """

    def test_vec_calculation(self):
        """
        Test Valence Electron Concentration (VEC).
        """
        # 1. Pure Elements
        # Fe: Group 8 -> VEC 8
        self.assertAlmostEqual(hea_calc.calculate_vec({'Fe': 1.0}), 8.0, places=2)
        # Al: Group 13 -> VEC 3 (standard for HEA/Miedema)
        self.assertAlmostEqual(hea_calc.calculate_vec({'Al': 1.0}), 3.0, places=2)
        
        # 2. Standard Equiatomic HEA: AlCoCrFeNi
        # Al(3) + Co(9) + Cr(6) + Fe(8) + Ni(10) = 36
        # Avg = 36 / 5 = 7.2
        comp = {'Al': 1.0, 'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0}
        self.assertAlmostEqual(hea_calc.calculate_vec(comp), 7.2, places=2)

    def test_mixing_enthalpy(self):
        """
        Test Mixing Enthalpy (H_mix) = Sum(4 * H_ij * ci * cj).
        Based on sub-regular solution model approximation.
        """
        # 1. Ideal / Zero interaction
        # Pure element -> 0
        self.assertEqual(hea_calc.calculate_mixing_enthalpy({'Fe': 1.0}), 0.0)
        
        # 2. Binary System AB (Equiatomic)
        # H_mix = 4 * H_AB * 0.5 * 0.5 = H_AB
        # Check Al-Ni (H=-22 kJ/mol in json)
        h_al_ni = db.get_enthalpy('Al', 'Ni') # -22
        comp = {'Al': 0.5, 'Ni': 0.5}
        h_calc = hea_calc.calculate_mixing_enthalpy(comp)
        self.assertAlmostEqual(h_calc, h_al_ni, places=2)
        
        # 3. Ternary Equiatomic
        # H_mix = 4 * (H_AB*c*c + H_BC*c*c + H_AC*c*c)
        # c = 1/3
        # H_mix = 4/9 * (H_AB + H_BC + H_AC)
        comp_ternary = {'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0} # CoCrFe
        # Co-Cr: -4, Co-Fe: -1, Cr-Fe: -1 -> Sum = -6
        # Expected: 4/9 * -6 = -2.666...
        h_calc_t = hea_calc.calculate_mixing_enthalpy(comp_ternary)
        self.assertAlmostEqual(h_calc_t, 4/9 * -6, places=2)

    def test_mixing_entropy(self):
        """
        Test Mixing Entropy (S_mix) = -R * Sum(ci * ln(ci)).
        """
        R = 8.314
        # 1. Pure element -> 0
        self.assertEqual(hea_calc.calculate_mixing_entropy({'Fe': 1.0}), 0.0)
        
        # 2. Equiatomic binary -> -R * (0.5ln0.5 + 0.5ln0.5) = R * ln(2)
        import math
        expected = R * math.log(2)
        self.assertAlmostEqual(hea_calc.calculate_mixing_entropy({'Fe': 1.0, 'Ni': 1.0}), expected, places=3)
        
        # 3. Equiatomic 5-component -> R * ln(5)
        expected_5 = R * math.log(5)
        comp = {'Al': 1.0, 'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0}
        self.assertAlmostEqual(hea_calc.calculate_mixing_entropy(comp), expected_5, places=3)

    def test_atomic_size_difference(self):
        """
        Test Atomic Size Difference (Delta).
        """
        # 1. Pure element -> 0
        self.assertEqual(hea_calc.calculate_atomic_size_difference({'Fe': 1.0}), 0.0)
        
        # 2. Binary with different sizes
        # Just check it's positive
        comp = {'Fe': 1.0, 'Al': 1.0} # Fe(1.26), Al(1.43)
        delta = hea_calc.calculate_atomic_size_difference(comp)
        self.assertGreater(delta, 0.0)
        
    def test_omega_parameter(self):
        """
        Test Omega = Tm * Smix / |Hmix|
        """
        # CoCrFeNi (Solid solution, high entropy)
        # H_mix should be small negative, S_mix high -> Omega > 1
        comp = {'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0} 
        omega = hea_calc.calculate_omega(comp)
        
        self.assertIsNotNone(omega)
        # Co-Cr(-4), Co-Fe(-1), Co-Ni(0), Cr-Fe(-1), Cr-Ni(-7), Fe-Ni(-2)
        # Sum = -15.
        # H_mix = 4/16 * (-15) = -3.75 kJ/mol = -3750 J/mol
        # S_mix = R * ln(4) = 8.314 * 1.386 ~ 11.5 J/molK
        # Tm avg ~ 1700-1800K
        # Omega ~ 1750 * 11.5 / 3750 ~ 5.3
        self.assertGreater(omega, 1.1) 
        
    def test_electronegativity_difference(self):
        """Test electronegativity difference."""
        comp = {'Fe': 0.5, 'Ni': 0.5}
        d_chi = hea_calc.calculate_electronegativity_difference(comp)
        self.assertAlmostEqual(d_chi, 0.0, delta=0.5) # Fe and Ni are close

if __name__ == '__main__':
    unittest.main()
