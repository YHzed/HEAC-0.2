
import os
import sys
import pandas as pd
import logging

# Add project root to path
sys.path.insert(0, os.getcwd())

from core.feature_injector import FeatureInjector

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def inject_features():
    print("[Step 1] Feature Injection (Physics Tagging)...")
    
    # 1. Load Data
    input_path = 'training data/HEA_processed.csv'
    output_path = 'datasets/master_dataset_with_features.csv'

    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return

    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows.")
    
    # 2. Initialize Injector
    model_dir = 'models/proxy_models'
    injector = FeatureInjector(model_dir=model_dir)
    
    # 3. Inject Features
    # Use 'Binder_Composition' as the composition column
    comp_col = 'Binder_Composition'
    ceramic_col = 'Ceramic_Type'
    
    if comp_col not in df.columns:
        # Fallback to similar columns
        candidates = [c for c in df.columns if 'binder' in c.lower() and 'comp' in c.lower()]
        if candidates:
            comp_col = candidates[0]
            print(f"Warning: Using column '{comp_col}' for composition.")
        else:
             print("Error: Could not find composition column.")
             return

    print("Injecting features (this may take a moment)...")
    df_enhanced = injector.inject_features(df, comp_col=comp_col, ceramic_type_col=ceramic_col, verbose=True)
    
    # 4. Save
    os.makedirs('datasets', exist_ok=True)
    df_enhanced.to_csv(output_path, index=False)
    print(f"\n[Success] Enhanced dataset saved to {output_path}")
    
    # 5. Verify
    print("\n[Verification] Sample of injected features:")
    new_cols = ['pred_formation_energy', 'pred_lattice_param', 'lattice_mismatch_wc', 
                'pred_magnetic_moment', 'lattice_distortion', 'coherent_potential', 'is_coherent']
    print(df_enhanced[new_cols].head())

if __name__ == "__main__":
    inject_features()
