
import os
import sys
import pandas as pd
import numpy as np
import joblib
import logging
from xgboost import XGBRegressor
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.getcwd())

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_master_models():
    print("[Step 2] Training Master Models (HV & KIC)...")
    
    # 1. Load Enriched Data
    input_path = 'datasets/master_dataset_with_features.csv'
    if not os.path.exists(input_path):
        print(f"Error: Dataset not found at {input_path}")
        return
        
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows from {input_path}")
    
    # 2. Define Features
    # We use both traditional features (Grain Size, binder content) AND new physics features
    feature_cols = [
        # Process / Macro params
        'Binder_Vol_Pct', 
        'Grain_Size_um', 
        'Sinter_Temp_C', 
        
        # New Physics Features (The "Secret Sauce")
        'pred_formation_energy',    # Stability
        'pred_lattice_param',       # WC Interaction (Atomic size match)
        'lattice_mismatch_wc',      # Interface Coherency proxy
        'lattice_distortion',       # Solid Solution Strengthening
        'pred_magnetic_moment',     # Electronic structure proxy
        'coherent_potential',       # Refined mismatch
        # 'is_coherent' # Boolean might be less useful for trees than continuous 'coherent_potential'
    ]
    
    # Clean Data
    print("Cleaning data for training...")
    df_clean = df.dropna(subset=feature_cols + ['HV_kgf_mm2', 'KIC_MPa_m'])
    print(f"Data after cleaning: {len(df_clean)} rows (removed {len(df) - len(df_clean)} rows with NaNs)")
    
    if len(df_clean) < 50:
        print("Error: Too few data points for training.")
        return

    X = df_clean[feature_cols]
    
    # 3. Train HV Model
    print("\nTraining Hardness (HV) Model...")
    y_hv = df_clean['HV_kgf_mm2']
    
    xgb_hv = XGBRegressor(
        n_estimators=1000, 
        learning_rate=0.05, 
        max_depth=6, 
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42
    )
    
    # Cross-validation
    y_hv_pred = cross_val_predict(xgb_hv, X, y_hv, cv=5)
    r2_hv = r2_score(y_hv, y_hv_pred)
    mae_hv = mean_absolute_error(y_hv, y_hv_pred)
    
    print(f"HV Model CV Results: R² = {r2_hv:.4f}, MAE = {mae_hv:.4f} kgf/mm²")
    
    # Full Training
    xgb_hv.fit(X, y_hv)
    
    # Feature Importance
    print("\nHV Feature Importance:")
    for name, imp in sorted(zip(feature_cols, xgb_hv.feature_importances_), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {imp:.4f}")

    # 4. Train KIC Model
    print("\nTraining Fracture Toughness (KIC) Model...")
    y_kic = df_clean['KIC_MPa_m']
    
    xgb_kic = XGBRegressor(
        n_estimators=1000, 
        learning_rate=0.05, 
        max_depth=6, 
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42
    )
    
    # Cross-validation
    y_kic_pred = cross_val_predict(xgb_kic, X, y_kic, cv=5)
    r2_kic = r2_score(y_kic, y_kic_pred)
    mae_kic = mean_absolute_error(y_kic, y_kic_pred)
    
    print(f"KIC Model CV Results: R² = {r2_kic:.4f}, MAE = {mae_kic:.4f} MPa·m^1/2")
    
    # Full Training
    xgb_kic.fit(X, y_kic)
    
    # Feature Importance
    print("\nKIC Feature Importance:")
    for name, imp in sorted(zip(feature_cols, xgb_kic.feature_importances_), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {imp:.4f}")
        
    # 5. Save Models
    model_dir = Path('models/master_models')
    model_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(xgb_hv, model_dir / 'master_hv_model.pkl')
    joblib.dump(xgb_kic, model_dir / 'master_kic_model.pkl')
    joblib.dump(feature_cols, model_dir / 'master_feature_names.pkl')
    
    print(f"\n[Success] Master models saved to {model_dir}")

if __name__ == "__main__":
    train_master_models()
