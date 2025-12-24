import joblib

print("="*70)
print("ModelX 完整特征分析")
print("="*70)

modelx = joblib.load('models/ModelX.pkl')
features_x = modelx['feature_names']

print(f"\n特征总数: {len(features_x)}")
print(f"目标变量: {modelx['target_name']}")
print(f"\n完整特征列表（Python格式）:")
print("MODELX_FEATURES = [")
for feat in features_x:
    print(f"    '{feat}',")
print("]")

print("\n" + "="*70)
print("ModelY 完整特征分析")  
print("="*70)

modely = joblib.load('models/ModelY.pkl')
features_y = modely['feature_names']

print(f"\n特征总数: {len(features_y)}")
print(f"目标变量: {modely['target_name']}")
print(f"\n完整特征列表（Python格式）:")
print("MODELY_FEATURES = [")
for feat in features_y:
    print(f"    '{feat}',")
print("]")

# 比较特征
print("\n" + "="*70)
print("特征对比")
print("="*70)
if features_x == features_y:
    print("✓ ModelX和ModelY使用相同的特征")
else:
    print("⚠ ModelX和ModelY特征不同!")
    x_only = set(features_x) - set(features_y)
    y_only = set(features_y) - set(features_x)
    if x_only:
        print(f"\nX独有特征 ({len(x_only)}个):")
        for f in x_only:
            print(f"  - {f}")
    if y_only:
        print(f"\nY独有特征 ({len(y_only)}个):")
        for f in y_only:
            print(f"  - {f}")

print("\n" + "="*70)
print("模型信息")
print("="*70)
print(f"\nModelX - {modelx['target_name']}:")
print(f"  模型类型: {type(modelx['model'])}")
print(f"  CV得分: {modelx.get('cv_score', 'N/A')}")

print(f"\nModelY - {modely['target_name']}:")
print(f"  模型类型: {type(modely['model'])}")
print(f"  CV得分: {modely.get('cv_score', 'N/A')}")
