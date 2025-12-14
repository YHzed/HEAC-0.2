
import sys
import os
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.material_database import db

def verify_library():
    print("="*60)
    print("Verifying HEAC MP Library Integration")
    print("="*60)
    
    # Reload to ensure we get fresh data if file changed
    db._load_heac_library()
    
    stats = db.get_heac_library_stats()
    print(f"Library Stats: {stats}")
    
    if stats['count'] == 0:
        print("[WARN] Library is empty. (Build might still be running or failed)")
        return
    
    print("[OK] Library loaded successfully.")
    
    # Test queries
    test_formulas = ["TiC", "WC", "Al2O3", "Fe"]
    for formula in test_formulas:
        print(f"\nQuerying {formula}...")
        data = db.get_heac_material_data(formula)
        if data:
            print(f"  [FOUND] Material ID: {data.get('material_id')}")
            print(f"  UE_Density: {data.get('density')}")
            print(f"  Formation Energy: {data.get('formation_energy_per_atom')} eV/atom")
        else:
            print(f"  [MISSING] {formula} not in library (or not in target system list)")

if __name__ == "__main__":
    verify_library()
