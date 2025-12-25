
import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, r'd:\ML\HEAC 0.2')

from heac_inverse_design.core.optimization.inverse_designer import InverseDesigner

# Mock classes to avoid loading heavy models
class MockModel:
    def predict(self, features):
        return 1600.0 if features else 0.0

class MockProxy:
    def predict_all(self, feats):
        return {}
    def get_features(self, comp):
        return {}

class MockExtractor:
    def extract_all(self, composition, gs, cv, st, proxy_preds, c_type):
        return [1.0] * 10

def test_constraints():
    print("Testing InverseDesigner constraints...")
    
    designer = InverseDesigner(MockModel(), MockModel(), MockProxy(), MockExtractor())
    
    # Run a small design tasks
    solutions = designer.design(
        target_hv_range=(1500, 2000),
        target_kic_range=(10, 15),
        allowed_elements=['Co', 'Ni', 'Fe', 'Cr', 'Mo'],
        n_trials=50
    )
    
    print(f"Found {len(solutions)} solutions.")
    
    violation_count = 0
    total_elements = 0
    
    for sol in solutions:
        for el, frac in sol.composition.items():
            if frac > 0.001: # Ignore effectively zero
                total_elements += 1
                if not (0.05 <= frac <= 0.35):
                    print(f"VIOLATION: {el}={frac:.4f}")
                    violation_count += 1
    
    if violation_count == 0:
        print("SUCCESS: All element fractions are within [0.05, 0.35] (or 0).")
    else:
        print(f"FAILURE: Found {violation_count} violations out of {total_elements} checks.")

if __name__ == "__main__":
    test_constraints()
