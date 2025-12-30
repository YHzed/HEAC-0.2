
import os
import sys
import pandas as pd
import logging
import joblib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.getcwd())

from core.feature_injector import FeatureInjector

def inspect_features():
    print("Inspecting Feature Mismatch...")
    
    model_dir = 'models/proxy_models'
    feature_names_path = os.path.join(model_dir, 'feature_names.pkl')
    
    if os.path.exists(feature_names_path):
        feature_names = joblib.load(feature_names_path)
        print(f"Total expected features: {len(feature_names)}")
        print("\nFirst 10 expected features:")
        print(feature_names[:10])
        print("\nLast 10 expected features:")
        print(feature_names[-10:])
    else:
        print("feature_names.pkl not found!")

    # Check what Matminer generates
    try:
        from matminer.featurizers.composition import ElementProperty
        from pymatgen.core import Composition
        
        ep = ElementProperty.from_preset("magpie")
        labels = ep.feature_labels()
        print(f"\nMatminer 'magpie' preset generates {len(labels)} features.")
        print("First 10 generated features:")
        print(labels[:10])
    except Exception as e:
        print(f"Matminer error: {e}")

if __name__ == "__main__":
    inspect_features()
