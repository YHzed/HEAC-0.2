import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, r'd:\ML\HEAC 0.2')

from heac_inverse_design.core.optimization.inverse_designer import InverseDesigner, DesignSolution
from heac_inverse_design.core.models import ModelX, ModelY, ProxyModelEnsemble
from heac_inverse_design.core.features import FeatureExtractor

# Mock classes to avoid loading heavy models
class MockModel:
    def predict(self, features):
        return 1500.0 if 'HV' not in str(type(self)) else 10.0

class MockProxy:
    def predict_all(self, feats):
        return {
            'pred_formation_energy': -0.5,
            'pred_lattice_param': 3.6,
            'pred_magnetic_moment': -0.5
        }

def test_constraints():
    print("Testing constraints...")
    
    # Initialize with mocks
    designer = InverseDesigner(MockModel(), MockModel(), MockProxy(), FeatureExtractor())
    
    # Mock extractor to avoid actual calculation errors during penalty test
    designer.extractor.extract_all = lambda *args: {}
    
    # We hijack the objective function inside a dummy study to test logic without running full optimization
    # Actually, easier to just run a short optimization and check results
    
    print("Running short optimization...")
    solutions = designer.design(
        target_hv_range=(1600, 1800), # Target higher than mock return (1500)
        target_kic_range=(8, 12),      # Target matches mock return (10)
        allowed_elements=['Co', 'Ni', 'Fe', 'Cr'],
        n_trials=20
    )
    
    print(f"Found {len(solutions)} solutions.")
    
    for i, sol in enumerate(solutions):
        print(f"Solution {i}:")
        print(f"  Compo: {sol.composition}")
        print(f"  Temp: {sol.sinter_temp}")
        
        # Check atomic fractions
        for el, frac in sol.composition.items():
            if frac < 0.045: # Allow small floating point error
                print(f"  FAIL: Fraction {el}={frac} < 0.05")
            else:
                pass # print(f"  PASS: Fraction {el}={frac} >= 0.05")
                
    if len(solutions) == 0:
        print("No solutions found. This might be correct if penalties are working and mock model returns 1500 (outside 1600-1800 target).")
        # Let's try a target that includes 1500
        print("Retrying with reachable target...")
        solutions = designer.design(
            target_hv_range=(1400, 1600),
            target_kic_range=(8, 12),
            allowed_elements=['Co', 'Ni', 'Fe', 'Cr'],
            n_trials=20
        )
        print(f"Found {len(solutions)} solutions with reachable target.")
        for sol in solutions:
             for el, frac in sol.composition.items():
                if frac < 0.045:
                    print(f"  FAIL: Fraction {el}={frac} < 0.05")

if __name__ == "__main__":
    test_constraints()
