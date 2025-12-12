import pytest
import pandas as pd
import numpy as np
from core.models import ModelFactory, ModelTrainer

@pytest.fixture
def regression_data():
    X = pd.DataFrame({'f1': np.random.rand(100), 'f2': np.random.rand(100)})
    y = 2 * X['f1'] + 3 * X['f2'] + 0.1 * np.random.randn(100)
    return X, y

@pytest.fixture
def classification_data():
    X = pd.DataFrame({'f1': np.random.rand(100), 'f2': np.random.rand(100)})
    y = (X['f1'] + X['f2'] > 1).astype(int)
    return X, y

def test_model_factory_regression():
    model = ModelFactory.get_model('regression', 'Linear Regression')
    assert model is not None
    assert type(model).__name__ == 'LinearRegression'

def test_model_factory_classification():
    model = ModelFactory.get_model('classification', 'Logistic Regression')
    assert model is not None
    assert type(model).__name__ == 'LogisticRegression'

def test_model_factory_invalid():
    with pytest.raises(ValueError):
        ModelFactory.get_model('regression', 'InvalidModelName')

def test_training_regression(regression_data):
    X, y = regression_data
    model = ModelFactory.get_model('regression', 'Linear Regression')
    trainer = ModelTrainer()
    
    # Split manually for test
    split = 80
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    trainer.train(model, X_train, y_train)
    assert trainer.model is not None
    
    metrics, preds = trainer.evaluate(X_test, y_test, 'regression')
    assert 'MSE' in metrics
    assert 'R2 Score' in metrics
    assert len(preds) == 20
    assert metrics['R2 Score'] > 0.5 # Should be decent on synthetic linear data

def test_training_classification(classification_data):
    X, y = classification_data
    model = ModelFactory.get_model('classification', 'Logistic Regression')
    trainer = ModelTrainer()
    
    split = 80
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    trainer.train(model, X_train, y_train)
    metrics, preds = trainer.evaluate(X_test, y_test, 'classification')
    
    assert 'Accuracy' in metrics
    assert 'Report' in metrics
    assert 'Confusion Matrix' in metrics
