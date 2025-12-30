
import os
import sys

# Add project root to path
sys.path.insert(0, os.getcwd())

from core.proxy_models import ProxyModelTrainer

def train_and_save():
    print("Starting full model retraining...")
    
    # Data path
    data_path = "training data/zenodo/structure_featurized.dat_all.csv"
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    # Initialize trainer
    trainer = ProxyModelTrainer(data_path)
    
    # Train all models
    trainer.train_all_models(cv=5)
    
    # Save models to correct directory
    output_dir = "models/proxy_models"
    trainer.save_models(output_dir=output_dir)
    
    print(f"Retraining complete. Models saved to {output_dir}")

if __name__ == "__main__":
    train_and_save()
