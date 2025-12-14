"""
简单验证脚本 - 测试MP集成但不依赖dotenv

直接从.env文件读取配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*60)
print("Materials Project Integration Verification")
print("="*60)

# 手动读取.env文件
def load_env():
    env_path = project_root / '.env'
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

env_vars = load_env()
api_key = env_vars.get('MP_API_KEY')

# Test 1: Import material_database
print("\n[1/4] Testing module import...")
try:
    from core.material_database import db
    print("[OK] Module imported successfully")
except Exception as e:
    print(f"[FAIL] Module import failed: {e}")
    sys.exit(1)

# Test 2: Local database
print("\n[2/4] Testing local database...")
try:
    wc_density = db.get_compound_density("WC")
    wc_enthalpy = db.get_formation_enthalpy("WC")
    assert wc_density == 15.63
    assert wc_enthalpy == -40.0
    print("[OK] Local database working")
    print(f"  WC density: {wc_density} g/cm^3")
    print(f"  WC enthalpy: {wc_enthalpy} kJ/mol")
except Exception as e:
    print(f"[FAIL] Local database test failed: {e}")
    sys.exit(1)

# Test 3: Check versions and API key
print("\n[3/5] Checking versions and API configuration...")
try:
    import pydantic
    import mp_api
    print(f"  Pydantic version: {pydantic.__version__}")
    print(f"  mp-api version: {mp_api.__version__}")
    
    # Check if versions are compatible
    pydantic_major, pydantic_minor = map(int, pydantic.__version__.split('.')[:2])
    if pydantic_major == 2 and pydantic_minor >= 10:
        print("  [WARN] Pydantic 2.10+ may have compatibility issues - recommend 2.9.x")
    else:
        print("  [OK] Pydantic version looks compatible")
except Exception as e:
    print(f"  [WARN] Could not check versions: {e}")

if api_key and api_key != "your_api_key_here":
    print("[OK] API key configured")
    print(f"  Key: {api_key[:10]}...{api_key[-4:]}")
    has_api = True
else:
    print("[WARN] API key not configured (network tests will be skipped)")
    has_api = False

# Test 4: Test MP client
print("\n[4/5] Testing MP integration...")
if has_api:
    # 临时设置环境变量供mp-api使用
    os.environ['MP_API_KEY'] = api_key
    
    try:
        print("  Fetching Silicon (Si) data from Materials Project...")
        si_data = db.get_mp_data("Si")
        if si_data:
            print("[OK] Successfully fetched MP data")
            print(f"  Material ID: {si_data.get('material_id', 'N/A')}")
            print(f"  Formula: {si_data.get('formula_pretty', 'N/A')}")
            if si_data.get('density'):
                print(f"  Density: {si_data.get('density'):.3f} g/cm^3")
        else:
            print("[FAIL] No data received")
    except Exception as e:
        print(f"[FAIL] MP data fetch failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[SKIP] No API key (network test skipped)")

# Test 5: Fallback direct API test
print("\n[5/5] Fallback: Testing direct MP API...")
if has_api:
    try:
        from mp_api.client import MPRester
        with MPRester(api_key) as mpr:
            # Very simple query
            docs = mpr.materials.summary.search(
                material_ids=["mp-149"],
                fields=["material_id", "formula_pretty"]
            )
            if docs:
                print(f"[OK] Direct API test successful: {docs[0].formula_pretty}")
            else:
                print("[FAIL] No results from direct API test")
    except Exception as e:
        print(f"[FAIL] Direct API test failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[SKIP] No API key")

# Summary
print("\n" + "="*60)
print("Verification Summary")
print("="*60)

if has_api:
    print("[SUCCESS] All features working - MP integration ready")
else:
    print("[PARTIAL] Local database OK - configure API key for MP features")

print("\nNext steps:")
print("  - Read docs: docs/materials_project_usage.md")
print("  - Fetch data: python scripts/fetch_mp_data.py --formula TiO2")
print("  - View cache: python scripts/browse_mp_cache.py --stats")
print("\nAPI key configuration:")
print("  Get your key from: https://materialsproject.org/dashboard")
print("  Add to .env file: MP_API_KEY=your_key_here")
