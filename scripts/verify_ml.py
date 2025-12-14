
import sys
import os
import numpy as np
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import ModelFactory, ModelTrainer

def test_ml_models():
    print("Starting ML Algorithms Verification...")
    
    # Dummy Data
    X_train = np.random.rand(100, 5)
    y_train_reg = np.random.rand(100)
    y_train_clf = np.random.randint(0, 2, 100)
    
    X_test = np.random.rand(20, 5)
    y_test_reg = np.random.rand(20)
    y_test_clf = np.random.randint(0, 2, 20)
    
    models_to_test = [
        ('regression', 'Linear Regression'),
        ('regression', 'Random Forest'),
        ('regression', 'XGBoost'),
        ('classification', 'Logistic Regression'),
        ('classification', 'Random Forest'),
        ('classification', 'XGBoost')
    ]
    
    trainer = ModelTrainer()
    
    for task_type, model_name in models_to_test:
        print(f"\nTesting {model_name} ({task_type})...")
        try:
            model = ModelFactory.get_model(task_type, model_name)
            
            if task_type == 'regression':
                trainer.train(model, X_train, y_train_reg)
                metrics, _ = trainer.evaluate(X_test, y_test_reg, task_type)
            else:
                trainer.train(model, X_train, y_train_clf)
                metrics, _ = trainer.evaluate(X_test, y_test_clf, task_type)
                
            print(f"PASS: {model_name} - Metrics: {metrics}")
            
        except ImportError as e:
            print(f"SKIP: {model_name} - Not installed: {e}")
        except Exception as e:
            print(f"FAIL: {model_name} - Error: {e}")
            
    print("\nVerification Complete.")

if __name__ == "__main__":
    test_ml_models()
