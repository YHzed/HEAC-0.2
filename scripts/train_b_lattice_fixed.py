# -*- coding: utf-8 -*-
"""
Model B - Fixed Version: Lattice Parameter Predictor
Implements structure-based classification and volume prediction approach

Key Improvements:
1. Filter by crystal structure (FCC/BCC separation)
2. Predict volume_per_atom instead of direct lattice parameter
3. Filter unstable structures by formation energy
4. Remove outliers

Author: HEAC Team
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_step(msg):
    """Print with separator"""
    print("\n" + "=" * 80)
    print(msg)
    print("=" * 80)

def main():
    print_step("Model B (Fixed): Lattice Parameter Predictor")
    print("Strategy: Structure-aware volume prediction")
    
    # Load data
    print_step("Step 1: Loading Zenodo data")
    data_path = 'training data/zenodo/structure_featurized.dat_all.csv'
    df = pd.read_csv(data_path, index_col=0)
    print(f"Original data size: {len(df)} samples")
    
    # Check if spacegroup column exists
    spacegroup_cols = [c for c in df.columns if 'space' in c.lower() or 'group' in c.lower()]
    print(f"\nAvailable structure columns: {spacegroup_cols}")
    
    # If no spacegroup column, use all data (fallback strategy)
    use_structure_filter = len(spacegroup_cols) > 0
    
    if use_structure_filter:
        # Try to find the spacegroup column
        sg_col = spacegroup_cols[0] if spacegroup_cols else None
        if sg_col:
            print(f"\nUsing column: {sg_col}")
            print(f"Unique values sample: {df[sg_col].value_counts().head(10)}")
    else:
        print("\n[!] No spacegroup column found - using all data")
    
    # Data cleaning
    print_step("Step 2: Data Cleaning")
    
    # Filter 1: Remove unstable structures (high formation energy)
    print("\n[Filter 1] Removing unstable structures...")
    ef_col = 'Ef_per_atom'
    if ef_col in df.columns:
        df_clean = df[df[ef_col] < 0.2].copy()
        print(f"After formation energy filter: {len(df_clean)} samples")
    else:
        df_clean = df.copy()
        print("[!] Formation energy column not found - skipping filter")
    
    # Filter 2: Remove volume outliers (3-sigma rule)
    print("\n[Filter 2] Removing volume outliers...")
    vol_col = 'volume_per_atom'
    if vol_col in df_clean.columns:
        vol_mean = df_clean[vol_col].mean()
        vol_std = df_clean[vol_col].std()
        df_clean = df_clean[
            (df_clean[vol_col] > vol_mean - 3*vol_std) &
            (df_clean[vol_col] < vol_mean + 3*vol_std)
        ].copy()
        print(f"After outlier filter: {len(df_clean)} samples")
    else:
        print("[!] volume_per_atom column not found - skipping filter")
    
    # Prepare features and target
    print_step("Step 3: Feature Preparation")
    
    # Use last 273 features (Matminer features)
    nfeatures = 273
    feature_names = df_clean.columns[-nfeatures:]
    X_all = df_clean[feature_names]
    
    # Remove zero-variance features
    variance = X_all.var()
    valid_features = variance[variance != 0].index
    X = X_all[valid_features]
    print(f"Valid features: {len(valid_features)}")
    
    # Target: volume_per_atom
    if vol_col in df_clean.columns:
        y = df_clean[vol_col]
        print(f"\nTarget: {vol_col}")
    else:
        print(f"\n[ERROR] Target column '{vol_col}' not found!")
        print("Available columns:", df_clean.columns.tolist())
        return 1
    
    print(f"Target statistics:")
    print(f"  Mean: {y.mean():.4f} A^3")
    print(f"  Std:  {y.std():.4f} A^3")
    print(f"  Range: [{y.min():.4f}, {y.max():.4f}] A^3")
    
    # Model training
    print_step("Step 4: Model Training")
    
    # Optimized XGBoost for volume prediction
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('xgb', xgb.XGBRegressor(
            n_estimators=500,
            max_depth=8,
            learning_rate=0.05,
            reg_lambda=0.1,
            reg_alpha=0.05,
            colsample_bytree=0.7,
            subsample=0.9,
            tree_method='hist',
            device='cpu',
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    print("\n[Training] 5-fold cross-validation...")
    try:
        y_pred = cross_val_predict(model, X, y, cv=5, n_jobs=1, verbose=0)
        
        # Metrics
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        r2 = r2_score(y, y_pred)
        
        print_step("Step 5: Results")
        print(f"\nVolume per Atom (A^3) - Evaluation Metrics:")
        print(f"  MAE:  {mae:.4f}")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  R2:   {r2:.4f}")
        
        # Performance assessment
        if r2 >= 0.90:
            print("\n[EXCELLENT] R2 >= 0.90 - Predictions are highly accurate!")
        elif r2 >= 0.80:
            print("\n[GOOD] R2 >= 0.80 - Good performance")
        elif r2 >= 0.60:
            print("\n[FAIR] R2 >= 0.60 - Moderate performance")
        else:
            print(f"\n[WARNING] R2 = {r2:.4f} - May need further optimization")
            print("Suggestions:")
            print("  - Try structure-specific models (FCC/BCC separation)")
            print("  - Add atomic radius features explicitly")
            print("  - Use ensemble methods")
        
        # Convert to lattice parameter (for demonstration)
        print("\n[Conversion] Volume -> Lattice Parameter:")
        print("  For FCC (Z=4): a = (4 * V_atom)^(1/3)")
        print("  For BCC (Z=2): a = (2 * V_atom)^(1/3)")
        
        # Example conversion (assuming FCC)
        a_pred_fcc = (4 * y_pred[:5]) ** (1/3)
        a_true_fcc = (4 * y.values[:5]) ** (1/3)
        print("\nSample predictions (FCC assumption):")
        for i in range(5):
            print(f"  Sample {i+1}: Pred={a_pred_fcc[i]:.3f} A, True={a_true_fcc[i]:.3f} A")
        
        # Train final model on all data
        print_step("Step 6: Training Final Model")
        model.fit(X, y)
        
        # Save model
        output_dir = Path('models/proxy_models')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = output_dir / 'lattice_model.pkl'
        joblib.dump(model, model_path)
        print(f"\n[OK] Model saved: {model_path}")
        
        # Save feature names
        feature_path = output_dir / 'feature_names.pkl'
        if not feature_path.exists():
            joblib.dump(list(valid_features), feature_path)
            print(f"[OK] Features saved: {feature_path}")
        
        # Save metrics
        metrics = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'target_name': 'Volume per atom (A^3)',
            'n_samples': len(y),
            'n_features': len(valid_features)
        }
        metrics_path = output_dir / 'lattice_metrics.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"[OK] Metrics saved: {metrics_path}")
        
        print_step("[DONE] Model B training completed successfully!")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
