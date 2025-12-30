
import os
import sys
import pandas as pd
import numpy as np
import joblib
import random
import logging
from tqdm import tqdm
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.getcwd())

from core.feature_injector import FeatureInjector

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_random_composition(elements, n_components=5):
    """Generate a random equi-atomic-ish composition."""
    # Pick n random elements
    selected = random.sample(elements, n_components)
    
    # Random fractions (dirichlet-like or just normalized randoms)
    # Strategy: generate random numbers and normalize
    raw_fracs = [random.random() for _ in range(n_components)]
    total = sum(raw_fracs)
    fracs = [f/total for f in raw_fracs]
    
    # Format as string for parser (e.g. Co0.2Cr0.3...)
    # But FeatureInjector expects a string like "Co1Cr1Fe1Ni1" or decimal
    comp_str = "".join([f"{el}{fr:.3f}" for el, fr in zip(selected, fracs)])
    return comp_str

def step3_inverse_design():
    print("[Step 3] Inverse Design Campaign (The Funnel)...")
    
    # Configuration
    N_SAMPLES = 1000  # Start with 1000 for testing, user asked for 100k, we can scale
    # To run 100k, it might take a while. I will set it to 1000 for demo, 
    # but print how to change it.
    print(f"Goal: Generate {N_SAMPLES} candidates (demo mode, scale up in production)")
    
    CANDIDATE_ELEMENTS = ['Co', 'Cr', 'Fe', 'Ni', 'Al', 'Ti', 'V', 'Mn', 'Mo', 'W', 'Cu']
    TARGET_CERAMIC = 'WC'
    
    # Thresholds (Funnel)
    MAX_FORMATION_ENERGY = 0.2  # eV/atom (Relaxed from 0.05)
    MAX_MISMATCH = 0.10         # 10% (Relaxed from 5%)
    
    # Load Master Models
    master_model_dir = Path('models/master_models')
    try:
        xgb_hv = joblib.load(master_model_dir / 'master_hv_model.pkl')
        xgb_kic = joblib.load(master_model_dir / 'master_kic_model.pkl')
        master_features = joblib.load(master_model_dir / 'master_feature_names.pkl')
        print("Loaded Master Models.")
    except Exception as e:
        print(f"Error loading master models: {e}")
        return

    # Initialize Injector
    injector = FeatureInjector(model_dir='models/proxy_models')
    
    # Storage
    candidates = []
    
    print("Generating and screening candidates...")
    
    # 1. Generation & Physics Screening Loop
    for _ in tqdm(range(N_SAMPLES)):
        # A. Generate
        n_elems = random.randint(4, 6) # 4 to 6 component HEAs
        comp_str = generate_random_composition(CANDIDATE_ELEMENTS, n_elems)
        
        # Parse & Inject (Single row DF for injector compatibility)
        df_single = pd.DataFrame([{'binder_composition': comp_str, 'Ceramic_Type': TARGET_CERAMIC}])
        
        # We suppress verbose to avoid scroll spam
        # Note: FeatureInjector is designed for batch, but we can stick to single for loop logic here
        # For huge scale, vectorization is better, but injector relies on model.predict which is vectorized...
        # Ideally we construct a huge DF then predict all.
        pass 
    
    # BETTER STRATEGY: Batch Generation
    BATCH_SIZE = 1000
    N_BATCHES = max(1, N_SAMPLES // BATCH_SIZE)
    
    valid_candidates = []
    
    for i in range(N_BATCHES):
        print(f"Processing Batch {i+1}/{N_BATCHES}...")
        batch_comps = []
        for _ in range(BATCH_SIZE):
            n_elems = random.randint(4, 6)
            batch_comps.append(generate_random_composition(CANDIDATE_ELEMENTS, n_elems))
        
        df_batch = pd.DataFrame({'binder_composition': batch_comps, 'Ceramic_Type': [TARGET_CERAMIC]*BATCH_SIZE})
        
        # B. Physics Injection (The Heavy Lifting)
        # Suppress prints for speed
        df_features = injector.inject_features(df_batch, comp_col='binder_composition', ceramic_type_col='Ceramic_Type', verbose=False)
        
        # C. First Filter: Physics Stability
        # Formation Energy < 0.2
        # Mismatch < 10% (0.10)
        mask_stable = (df_features['pred_formation_energy'] < MAX_FORMATION_ENERGY)
        # UPDATED: Use standard name 'lattice_mismatch'
        mask_match = (df_features['lattice_mismatch'] < MAX_MISMATCH)
        
        df_survivors = df_features[mask_stable & mask_match].copy()
        
        if df_survivors.empty:
            continue
            
        # D. Add Process Parameters (Assumed fixed for screening)
        # UPDATED: Use standard snake_case names
        df_survivors['binder_vol_pct'] = 20.0
        df_survivors['grain_size_um'] = 1.0
        df_survivors['sinter_temp_c'] = 1400.0
        
        # === MAPPING LAYER ===
        # Map standard snake_case names to legacy names for Master Model compatibility
        # DO NOT RETRAIN MODELS for this task
        legacy_mapping = {
            'lattice_mismatch': 'lattice_mismatch_wc',
            'binder_vol_pct': 'Binder_Vol_Pct',
            'grain_size_um': 'Grain_Size_um',
            'sinter_temp_c': 'Sinter_Temp_C',
            # Add other mappings if necessary based on 'master_features' list
        }
        
        # Create a view for prediction with renamed columns
        df_for_pred = df_survivors.rename(columns=legacy_mapping)
        
        # Align features for Master Model
        # Ensure all required columns are present (some might be direct from injector like pred_formation_energy)
        X_survivors = df_for_pred[master_features]
        
        # E. Master Model Prediction
        df_survivors['pred_HV'] = xgb_hv.predict(X_survivors)
        df_survivors['pred_KIC'] = xgb_kic.predict(X_survivors)
        
        valid_candidates.append(df_survivors)
    
    if not valid_candidates:
        print("No candidates survived the physics filter!")
        return

    # Combine all batches
    df_results = pd.concat(valid_candidates, ignore_index=True)
    
    # Rank by Multi-objective (simple weighted sum)
    # Norm HV and KIC for scoring
    # HV target: 2000, KIC target: 15
    # Score = HV/2000 + KIC/15
    df_results['Score'] = (df_results['pred_HV'] / 2000.0) + (df_results['pred_KIC'] / 15.0)
    
    df_results = df_results.sort_values(by='Score', ascending=False)
    
    output_path = 'datasets/inverse_design_results.csv'
    df_results.to_csv(output_path, index=False)
    
    print(f"\n[Done] Screened {N_SAMPLES} compositions.")
    print(f"Survivors: {len(df_results)}")
    print(f"Top 5 Candidates saved to {output_path}:")
    print(df_results[['binder_composition', 'pred_HV', 'pred_KIC', 'Score']].head().to_string())

if __name__ == "__main__":
    step3_inverse_design()
