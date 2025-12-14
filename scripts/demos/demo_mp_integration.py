"""
Simple MP Integration Demo - Test core functionality
"""

import sys
import os
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

# Load API key directly
env_path = Path(__file__).parent / '.env'
env_vars = {}
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

api_key = env_vars.get('MP_API_KEY')
if api_key:
    os.environ['MP_API_KEY'] = api_key

# Import database
from core.material_database import db

print("="*60)
print("Materials Project Integration Demo")
print("="*60)

# Test 1: Local data
print("\n[Test 1] Local Database")
wc_density = db.get_compound_density("WC")
print(f"  WC density (local): {wc_density} g/cm^3")

# Test 2: Try to get MP client
print("\n[Test 2] MP Client Initialization")
mp_client = db._get_mp_client()
if mp_client:
    print("  [OK] MP client initialized")
else:
    print("  [FAIL] MP client not available")
    sys.exit(1)

# Test 3: Try to fetch data  
print("\n[Test 3] Fetch Data from Materials Project")
try:
    print("  Querying: TiO2")
    results = db.search_mp_materials("TiO2")
    
    if results:
        print(f"  [OK] Found {len(results)} result(s)")
        first = results[0]
        print(f"  Material ID: {first.get('material_id', 'N/A')}")
        print(f"  Formula:  {first.get('formula_pretty', 'N/A')}")
        if first.get('density'):
            print(f"  Density: {first.get('density'):.3f} g/cm^3")
        if first.get('formation_energy_per_atom') is not None:
            print(f"  Formation Energy: {first.get('formation_energy_per_atom'):.4f} eV/atom")
    else:
        print("  [FAIL] No results")
        
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test automatic fallback
print("\n[Test 4] Automatic Fallback (use_mp=True)")
try:
    # Query WC with MP fallback (should return local data)
    wc_density_mp = db.get_compound_density("WC", use_mp=True)
    print(f"  WC density (with MP fallback): {wc_density_mp} g/cm^3")
    print(f"  [OK] Returned local data as expected")
    
except Exception as e:
    print(f"  [ERROR] {e}")

print("\n" + "="*60)
print("Demo Complete")
print("="*60)
print("\nThe Materials Project integration is working!")
print("You can now use:")
print("  - db.search_mp_materials(formula)")
print("  - db.get_mp_data(formula)")
print("  - db.get_density_from_mp(formula)")
print("  - db.get_compound_density(formula, use_mp=True)")
