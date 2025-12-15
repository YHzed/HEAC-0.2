import unittest
from core.hea_calculator import hea_calc
try:
    from core.hea_cermet import MaterialProcessor
except ImportError:
    MaterialProcessor = None
    print("Warning: Could not import MaterialProcessor (likely missing pandas). Skipping consistency test.")

class TestVECCalculation(unittest.TestCase):
    def test_al_co_cr_fe_ni_equiatomic(self):
        """
        Test VEC for AlCoCrFeNi (Equiatomic).
        Expected VEC = 7.2
        """
        composition = {'Al': 1.0, 'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0}
        vec = hea_calc.calculate_vec(composition)
        print(f"Calculated VEC for AlCoCrFeNi: {vec}")
        
        # We expect 7.2 based on standard Guo/Miedema VEC
        self.assertAlmostEqual(vec, 7.2, places=2, msg=f"Expected VEC=7.2, got {vec}")

    def test_cermet_processor_consistency(self):
        """
        Ensure MaterialProcessor (used in Cermet module) also returns correct VEC.
        """
        if not MaterialProcessor:
            print("Skipping MaterialProcessor test.")
            return

        mp = MaterialProcessor()
        # Parse formula
        comp = mp.parse_formula("AlCoCrFeNi")
        props = mp.calculate_properties(comp)
        vec = props['VEC']
        print(f"MaterialProcessor VEC for AlCoCrFeNi: {vec}")
        
        self.assertAlmostEqual(vec, 7.2, places=2)

if __name__ == '__main__':
    unittest.main()
