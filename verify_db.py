import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.material_database import db

def verify():
    print("Loading database...")
    lib = db.get_heac_library()
    print(f"Library Items: {len(lib)}")
    
    if len(lib) > 0:
        first_item = list(lib.values())[0]
        print(f"Sample Item Keys: {list(first_item.keys())}")
        
        # Check specific expected keys
        expected = ['formula_pretty', 'formation_energy_per_atom', 'density']
        missing = [k for k in expected if k not in first_item]
        if missing:
            print(f"WARNING: Missing expected keys: {missing}")
        else:
            print("Schema looks OK (basic keys present).")
    else:
        print("ERROR: Library is empty!")

if __name__ == "__main__":
    verify()
