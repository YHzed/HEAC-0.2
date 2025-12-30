
import sys
import os
import pandas as pd
import joblib

# Add project root to path
sys.path.insert(0, os.getcwd())

from core.feature_injector import FeatureInjector

def verify_injector():
    print("Verifying FeatureInjector...")
    injector = FeatureInjector(model_dir='models/proxy_models')
    
    df_test = pd.DataFrame([
        {'binder_composition': 'Co1Cr1Fe1Ni1', 'Ceramic_Type': 'WC'}
    ])
    
    df_out = injector.inject_features(df_test, comp_col='binder_composition', ceramic_type_col='Ceramic_Type', verbose=False)
    
    columns = df_out.columns.tolist()
    print(f"Injector Output Columns: {columns}")
    
    if 'lattice_mismatch' in columns:
        print("PASS: 'lattice_mismatch' found.")
    else:
        print("FAIL: 'lattice_mismatch' NOT found.")
        return False
        
    if 'lattice_mismatch_wc' in columns:
        print("FAIL: Legacy 'lattice_mismatch_wc' found (Should be removed).")
        return False
    else:
        print("PASS: Legacy 'lattice_mismatch_wc' correctly removed.")
        
    return True

def verify_inverse_design():
    print("\nVerifying Inverse Design Script...")
    result = os.system("python scripts/step3_inverse_design.py")
    
    if result == 0:
        print("PASS: scripts/step3_inverse_design.py ran successfully.")
        
        # Check output file
        if os.path.exists('datasets/inverse_design_results.csv'):
            print("PASS: Results file created.")
            df = pd.read_csv('datasets/inverse_design_results.csv')
            print(f"Results Count: {len(df)}")
            if len(df) > 0:
                print(f"Top Score: {df['Score'].max()}")
                return True
        else:
            print("FAIL: Results file NOT created.")
    else:
        print("FAIL: scripts/step3_inverse_design.py crashed.")
        
    return False

if __name__ == "__main__":
    v1 = verify_injector()
    v2 = verify_inverse_design()
    
    if v1 and v2:
        print("\nALL TESTS PASSED.")
    else:
        print("\nSOME TESTS FAILED.")
