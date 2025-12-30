
import os
import sys

# Add project root to path
sys.path.insert(0, os.getcwd())

from core.proxy_models import ProxyModelTrainer

def train_formation_energy():
    print("\n[Start] Training Formation Energy Model...")
    
    data_path = "training data/zenodo/structure_featurized.dat_all.csv"
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    trainer = ProxyModelTrainer(data_path)
    trainer.load_data()
    trainer.prepare_features()
    
    # Train
    trainer.train_formation_energy_model(cv=5)
    
    # Save
    output_dir = "models/proxy_models"
    trainer.save_models(output_dir=output_dir)
    print(f"[Done] Formation Energy Model saved to {output_dir}")

if __name__ == "__main__":
    train_formation_energy()
