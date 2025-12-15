import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.optimization import Optimizer
from core.models import ModelFactory

def test_stacking_optimization():
    print("Generating synthetic data...")
    X = pd.DataFrame(np.random.rand(100, 5), columns=[f'f{i}' for i in range(5)])
    y = np.random.rand(100)
    
    print("Initializing Optimizer...")
    optimizer = Optimizer(X, y, 'regression')
    
    print("Running optimization for Stacking...")
    best_params = optimizer.optimize('Stacking', n_trials=5)
    
    print("Best Params:", best_params)
    
    # Assertions
    assert 'final_estimator' in best_params
    assert best_params['final_estimator'] in ['Ridge', 'Linear Regression', 'Random Forest']
    
    # Verify Model Creation with best params
    print("Creating model with best params...")
    model = ModelFactory.get_model('regression', 'Stacking', best_params)
    print("Model created successfully:", model)
    
    # Check if final estimator is correct type
    final_est = model.final_estimator
    print("Final Estimator Type:", type(final_est))
    
    # Validate final estimator matches selection
    best_fe = best_params.get('final_estimator')
    if best_fe == 'Ridge':
        from sklearn.linear_model import Ridge
        assert isinstance(final_est, Ridge)
    elif best_fe == 'Linear Regression':
        from sklearn.linear_model import LinearRegression
        assert isinstance(final_est, LinearRegression)
    elif best_fe == 'Random Forest':
        from sklearn.ensemble import RandomForestRegressor
        assert isinstance(final_est, RandomForestRegressor)
    
    print("Test Passed!")

if __name__ == "__main__":
    test_stacking_optimization()
