import joblib
import pandas as pd

# Load ModelX
model_dict = joblib.load(r'd:\ML\HEAC 0.2\models\ModelX.pkl')

print("="*80)
print("ModelX Analysis Report")
print("="*80)

print("\n1. Dictionary Keys:")
for key in model_dict.keys():
    print(f"   - {key}: {type(model_dict[key])}")

print("\n2. Model Details:")
if 'model' in model_dict:
    model = model_dict['model']
    print(f"   Model Type: {type(model)}")
    if hasattr(model, 'n_features_in_'):
        print(f"   Number of Features: {model.n_features_in_}")
    if hasattr(model, 'feature_names_in_'):
        print(f"   Feature Names ({len(model.feature_names_in_)}):")
        for i, fname in enumerate(model.feature_names_in_, 1):
            print(f"      {i:2d}. {fname}")

print("\n3. Other Components:")
for key, value in model_dict.items():
    if key != 'model':
        print(f"   {key}:")
        if isinstance(value, (list, tuple)):
            print(f"      Type: {type(value)}, Length: {len(value)}")
            if len(value) < 20:
                for item in value:
                    print(f"         - {item}")
        elif isinstance(value, dict):
            print(f"      Type: dict, Keys: {list(value.keys())}")
        else:
            print(f"      Type: {type(value)}, Value: {value}")

print("\n" + "="*80)
