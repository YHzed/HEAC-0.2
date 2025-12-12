import pandas as pd
import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from core.models import ModelFactory
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def load_data():
    print("Loading Boston Housing dataset from OpenML...")
    # Boston Housing dataset is ID 531 on OpenML
    boston = fetch_openml(data_id=531, as_frame=True, parser='auto')
    X = boston.data
    y = boston.target
    
    # Ensure all data is numeric
    X = X.apply(pd.to_numeric, errors='coerce')
    X = X.dropna()
    y = y[X.index]
    
    return X, y

def main():
    try:
        X, y = load_data()
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models_to_test = [
        'Linear Regression',
        'Ridge',
        'Lasso',
        'SVR',
        'Decision Tree',
        'Random Forest',
        'XGBoost',
        'LightGBM',
        'CatBoost'
    ]

    results = []

    print("\nStarting Model Verification...\n")
    print(f"{'Model':<20} | {'MSE':<10} | {'RMSE':<10} | {'MAE':<10} | {'R2':<10}")
    print("-" * 75)

    for model_name in models_to_test:
        try:
            # Create model
            model = ModelFactory.get_model('regression', model_name, params={'random_state': 42} if model_name not in ['SVR', 'Linear Regression', 'Ridge', 'Lasso'] else {})
            
            # Train
            model.fit(X_train_scaled, y_train)
            
            # Predict
            y_pred = model.predict(X_test_scaled)
            
            # Evaluate
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            results.append({
                'Model': model_name,
                'MSE': mse,
                'RMSE': rmse,
                'MAE': mae,
                'R2': r2
            })
            
            print(f"{model_name:<20} | {mse:<10.4f} | {rmse:<10.4f} | {mae:<10.4f} | {r2:<10.4f}")
            
        except Exception as e:
            print(f"{model_name:<20} | Error: {str(e)}")

    # Save results to CSV (optional but good for record)
    df_results = pd.DataFrame(results)
    df_results.to_csv('boston_performance_results.csv', index=False)
    print("\nVerification complete. Results saved to boston_performance_results.csv")

if __name__ == "__main__":
    main()
