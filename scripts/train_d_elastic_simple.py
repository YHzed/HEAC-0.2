# -*- coding: utf-8 -*-
"""
Model D Training Script - Elastic Modulus Predictor
Uses simulated data for framework testing
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.proxy_models import ProxyModelTrainer

def main():
    print("=" * 80)
    print("Training Model D: Elastic Modulus Predictor")
    print("=" * 80)
    print("NOTE: Using simulated data for framework testing")
    print("=" * 80)
    
    trainer = ProxyModelTrainer(
        data_path='training data/zenodo/structure_featurized.dat_all.csv'
    )
    
    trainer.load_data()
    trainer.prepare_features()
    
    print("\nStarting training...")
    try:
        metrics = trainer.train_elastic_modulus_model(cv=5)
        
        # Save models
        output_dir = 'models/proxy_models'
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        import joblib
        bulk_path = Path(output_dir) / 'bulk_modulus_model.pkl'
        joblib.dump(trainer.models['bulk_modulus'], bulk_path)
        print(f"\n[OK] Bulk modulus model saved: {bulk_path}")
        
        shear_path = Path(output_dir) / 'shear_modulus_model.pkl'
        joblib.dump(trainer.models['shear_modulus'], shear_path)
        print(f"[OK] Shear modulus model saved: {shear_path}")
        
        metrics_path = Path(output_dir) / 'elastic_metrics.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"[OK] Metrics saved: {metrics_path}")
        
        print("\n" + "=" * 80)
        print("Model D training completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
