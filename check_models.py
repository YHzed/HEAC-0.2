import joblib

print("检查ModelY...")
try:
    modely = joblib.load('models/ModelY.pkl')
    print(f"  Type: {type(modely)}")
    if isinstance(modely, dict):
        print(f"  Keys: {list(modely.keys())}")
        if 'model' in modely:
            print(f"  Model type: {type(modely['model'])}")
except Exception as e:
    print(f"  Error: {e}")

print("\n检查ModelX...")
try:
    modelx = joblib.load('models/ModelX.pkl')
    print(f"  Type: {type(modelx)}")
    if isinstance(modelx, dict):
        print(f"  Keys: {list(modelx.keys())}")
        if 'feature_names' in modelx:
            print(f"  First 5 features: {modelx['feature_names'][:5]}")
except Exception as e:
    print(f"  Error: {e}")
