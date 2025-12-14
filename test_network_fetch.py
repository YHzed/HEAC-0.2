import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.material_database import db
from core.materials_project_client import mp_client

print("="*60)
print("Network Connectivity Test (Bypassing Cache)")
print("="*60)

# Force disable cache for this test
# We can do this by mocking the cache load method or just asking for something random
# But cleaner to set the config at runtime if possible, or just ask for a unique ID.
# Let's try two approaches.

# 1. Fetch something likely not cached: "Al2O3"
target_formula = "Al2O3"
print(f"\n[Test 1] Fetching {target_formula} via MaterialDatabase...")
try:
    # Check if it exists in cache first to be sure
    cache_key = mp_client._get_cache_key("summary", target_formula)
    cache_file = mp_client.cache_dir / cache_key
    if cache_file.exists():
        print(f"  [NOTE] {target_formula} IS currently in cache. Removing it to force network...")
        try:
            os.remove(cache_file)
            print("  [OK] Cache file removed.")
        except Exception as e:
            print(f"  [WARN] Failed to remove cache file: {e}")

    # Now fetch
    data = db.get_mp_data(target_formula)
    
    if data:
        print(f"[SUCCESS] Fetched data for {target_formula}")
        print(f"  Material ID: {data.get('material_id')}")
        print(f"  Density: {data.get('density')}")
    else:
        print("[FAIL] Returned None (check logs for errors)")

except Exception as e:
    print(f"[ERROR] Exception during fetch: {e}")
    import traceback
    traceback.print_exc()

# 2. Direct MPRester test with debugging
print("\n[Test 2] Direct MPRester ping (api.materialsproject.org)...")
try:
    from mp_api.client import MPRester
    import requests
    
    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        print("[SKIP] No MP_API_KEY found")
    else:
        print(f"Using API Key: {api_key[:4]}...")
        with MPRester(api_key) as mpr:
            # Try a very lightweight call
            print("  Searching for 'Au'...")
            docs = mpr.materials.summary.search(formula="Au", fields=["material_id"])
            if docs:
                print(f"[SUCCESS] Found {len(docs)} documents for Au")
            else:
                print("[FAIL] Found 0 documents")

except Exception as e:
    print(f"[ERROR] MPRester failed: {e}")
    import traceback
    traceback.print_exc()

# 3. Check proxy settings
print("\n[Debug] Environment Proxy Settings:")
print(f"  HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'Not Set')}")
print(f"  HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'Not Set')}")
print(f"  ALL_PROXY: {os.environ.get('ALL_PROXY', 'Not Set')}")
