
import sys
import os
import pandas as pd
import numpy as np
from sklearn.datasets import load_diabetes # Boston is deprecated in newer sklearn, using diabetes or simpler
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models import ModelFactory, ModelTrainer

def verify_stacking():
    print("Loading test data (Diabetes)...")
    data = load_diabetes()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = data.target
    
    # Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Initializing Stacking Regressor...")
    # Using defaults defined in models.py
    try:
        model = ModelFactory.get_model('regression', 'Stacking')
    except Exception as e:
        print(f"Failed to create model: {e}")
        return

    print("Training Stacking Model...")
    trainer = ModelTrainer()
    trainer.train(model, X_train, y_train)
    
    print("Evaluating...")
    try:
        metrics, preds = trainer.evaluate(X_test, y_test, 'regression')
        print("Metrics:", metrics)
        print("Example Preds:", preds[:5])
        print("Stacking Verification Successful.")
    except Exception as e:
        print(f"Evaluation Failed: {e}")

if __name__ == "__main__":
    verify_stacking()
