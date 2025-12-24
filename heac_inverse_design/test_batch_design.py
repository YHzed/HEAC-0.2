"""
批量设计测试脚本

测试批量设计功能。
"""

import sys
sys.path.insert(0, r'd:\ML\HEAC 0.2')

print("=" * 60)
print("Testing Batch Design Functionality")
print("=" * 60)

# Test 1: Create BatchDesigner
print("\n[Test 1] Creating BatchDesigner...")
try:
    from heac_inverse_design.core.models import ModelX, ModelY, ProxyModelEnsemble
    from heac_inverse_design.core.features import FeatureExtractor
    from heac_inverse_design.core.optimization import InverseDesigner, BatchDesigner
    
    modelx = ModelX(r'd:\ML\HEAC 0.2\models\ModelX.pkl')
    modely = ModelY(r'd:\ML\HEAC 0.2\models\ModelY.pkl')
    proxy = ProxyModelEnsemble(r'd:\ML\HEAC 0.2\models\proxy_models')
    extractor = FeatureExtractor()
    
    designer = InverseDesigner(modelx, modely, proxy, extractor)
    batch_designer = BatchDesigner(designer)
    
    print("[OK] BatchDesigner created")
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Add tasks from DataFrame
print("\n[Test 2] Adding tasks from DataFrame...")
try:
    import pandas as pd
    
    tasks_df = pd.DataFrame({
        'Name': ['High Hardness', 'Balanced'],
        'HV_Min': [1800, 1600],
        'HV_Max': [2000, 1800],
        'KIC_Min': [8, 10],
        'KIC_Max': [10, 13]
    })
    
    num_added = batch_designer.add_task_from_dataframe(tasks_df)
    print(f"[OK] Added {num_added} tasks")
    
    for task in batch_designer.tasks:
        print(f"   - {task.name}: HV {task.hv_range}, KIC {task.kic_range}")
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Batch Design module ready for use")
print("=" * 60)
print("\nTo test in UI:")
print("  cd heac_inverse_design\\ui")
print("  streamlit run inverse_design_app.py")
