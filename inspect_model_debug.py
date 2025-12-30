
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

def inspect_models():
    model_dir = Path("models/proxy_models")
    if not model_dir.exists():
        print(f"Directory not found: {model_dir}")
        return

    model_files = [
        'formation_energy_model.pkl',
        'lattice_model.pkl',
        'magnetic_moment_model.pkl'
    ]

    for filename in model_files:
        path = model_dir / filename
        if not path.exists():
            print(f"Skipping missing: {filename}")
            continue
            
        print(f"\n--- Inspecting {filename} ---")
        try:
            model = joblib.load(path)
            print(f"Type: {type(model)}")
            
            if hasattr(model, 'steps'):
                print(f"Pipeline Steps: {len(model.steps)}")
                for name, step in model.steps:
                    print(f"  Step '{name}': {type(step)}")
                    if hasattr(step, 'n_features_in_'):
                        print(f"    n_features_in_: {step.n_features_in_}")
                    else:
                        print(f"    (No n_features_in_)")
            else:
                print("Not a Pipeline or no steps attribute.")
                if hasattr(model, 'n_features_in_'):
                     print(f"Model n_features_in_: {model.n_features_in_}")

        except Exception as e:
            print(f"Error loading: {e}")

if __name__ == "__main__":
    inspect_models()
