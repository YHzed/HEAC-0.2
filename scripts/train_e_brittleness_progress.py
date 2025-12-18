# -*- coding: utf-8 -*-
"""
Model E Training Script - Brittleness Index Predictor
With real-time progress display
"""

import sys
from pathlib import Path
import time
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.proxy_models import ProxyModelTrainer

def print_progress(message, step=None, total=None):
    """Print progress with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    if step is not None and total is not None:
        print(f"[{timestamp}] [{step}/{total}] {message}")
    else:
        print(f"[{timestamp}] {message}")

def main():
    print("=" * 80)
    print("Training Model E: Brittleness Index Predictor (Pugh Ratio)")
    print("=" * 80)
    print("NOTE: Using simulated data for framework testing")
    print("=" * 80)
    
    print_progress("Initializing trainer...")
    trainer = ProxyModelTrainer(
        data_path='training data/zenodo/structure_featurized.dat_all.csv'
    )
    
    print_progress("Loading data...", 1, 4)
    trainer.load_data()
    print_progress(f"Data loaded: {trainer.df.shape[0]} samples", 1, 4)
    
    print_progress("Preparing features...", 2, 4)
    trainer.prepare_features()
    print_progress(f"Features ready: {len(trainer.feature_names)} dimensions", 2, 4)
    
    print_progress("Starting model training...", 3, 4)
    print_progress("This will take approximately 3-5 minutes")
    print_progress("Training Pugh Ratio predictor with 5-fold CV...")
    
    try:
        start_time = time.time()
        metrics = trainer.train_brittleness_model(cv=5)
        elapsed = time.time() - start_time
        
        print_progress(f"Training completed in {elapsed/60:.1f} minutes", 3, 4)
        
        # Display metrics
        print("\n" + "=" * 80)
        print("Model Performance:")
        print("=" * 80)
        if isinstance(metrics, dict) and 'mae' in metrics:
            print(f"MAE:  {metrics['mae']:.4f}")
            print(f"RMSE: {metrics['rmse']:.4f}")
            print(f"R2:   {metrics['r2']:.4f}")
        
        # Save models
        print_progress("Saving model...", 4, 4)
        output_dir = 'models/proxy_models'
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        import joblib
        model_path = Path(output_dir) / 'brittleness_model.pkl'
        joblib.dump(trainer.models['brittleness'], model_path)
        print_progress(f"Model saved: {model_path}", 4, 4)
        
        # Save metrics
        metrics_path = Path(output_dir) / 'brittleness_metrics.pkl'
        joblib.dump(metrics, metrics_path)
        print_progress(f"Metrics saved: {metrics_path}", 4, 4)
        
        # Save feature names if not exists
        feature_path = Path(output_dir) / 'feature_names.pkl'
        if not feature_path.exists():
            joblib.dump(list(trainer.feature_names), feature_path)
            print_progress(f"Feature names saved: {feature_path}")
        
        print("\n" + "=" * 80)
        print("[DONE] Model E training completed successfully!")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print_progress(f"[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
