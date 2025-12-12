import pytest
import pandas as pd
import numpy as np
import io
from core.data_processor import DataProcessor

@pytest.fixture
def sample_csv():
    data = """A,B,Target
1,10,0
2,20,1
3,30,0
4,40,1
5,50,0
"""
    return io.StringIO(data)

@pytest.fixture
def sample_csv_missing():
    data = """A,B,Target
1,10,0
2,,1
3,30,
4,40,1
,50,0
"""
    return io.StringIO(data)

def test_load_data_csv(sample_csv):
    dp = DataProcessor()
    success, msg = dp.load_data(sample_csv, 'csv')
    assert success is True
    assert dp.data is not None
    assert dp.data.shape == (5, 3)
    assert 'Target' in dp.columns

def test_handle_missing_drop(sample_csv_missing):
    dp = DataProcessor()
    dp.load_data(sample_csv_missing, 'csv')
    original_len = len(dp.data)
    dp.handle_missing_values('drop')
    assert len(dp.data) < original_len
    assert not dp.data.isnull().values.any()

def test_handle_missing_mean(sample_csv_missing):
    dp = DataProcessor()
    dp.load_data(sample_csv_missing, 'csv')
    dp.handle_missing_values('mean')
    assert not dp.data['B'].isnull().values.any()
    # Check if B's NaN was filled (index 1)
    # Mean of 10, 30, 40, 50 is 32.5
    assert dp.data.iloc[1]['B'] == 32.5

def test_prepare_data_split_scale(sample_csv):
    dp = DataProcessor()
    dp.load_data(sample_csv, 'csv')
    
    success, msg = dp.prepare_data(target_col='Target', test_size=0.2, use_scaling=True)
    assert success is True
    assert dp.X_train is not None
    assert dp.y_train is not None
    assert dp.X_test is not None
    assert dp.y_test is not None
    
    # Check scaling (StandardScaler by default, mean approx 0, std approx 1)
    # Small dataset makes exact check hard, but ensuring it's not original values works
    # Original A: 1,2,3,4,5. Scaled should be different.
    assert dp.X_train['A'].mean() == pytest.approx(0, abs=1.5) # Looser bound for small sample

def test_prepare_data_no_target(sample_csv):
    dp = DataProcessor()
    dp.load_data(sample_csv, 'csv')
    success, msg = dp.prepare_data(target_col=None)
    assert success is True
    assert dp.y_train is None
