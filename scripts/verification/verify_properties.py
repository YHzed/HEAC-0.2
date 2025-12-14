
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.material_database import db

def verify_props():
    print("="*60)
    print("Verifying Extended Properties (Elasticity, VEC, Hardness)")
    print("="*60)
    
    # Reload library
    db._load_heac_library()
    
    stats = db.get_heac_library_stats()
    print(f"Library Stats: {stats}")
    
    # Check specific materials
    # Try TiC (Likely has elastic data)
    targets = ["TiC", "WC", "ZrN", "Al2O3", "Fe"]
    
    for formula in targets:
        print(f"\n--- {formula} ---")
        # Use new method
        data = db.get_extended_properties(formula)
        
        if not data:
            print("  [MISSING] Not in library")
            continue
            
        print(f"  ID: {data.get('material_id')}")
        print(f"  VEC: {data.get('vec')}")
        print(f"  Vickers Hardness: {data.get('vickers_hardness')}")
        print(f"  Young's Modulus: {data.get('youngs_modulus')}")
        print(f"  Fracture Toughness: {data.get('fracture_toughness')}")
        print(f"  Oxidation Resistance: {data.get('oxidation_resistance')}")
        print(f"  Sintering Temp: {data.get('sintering_temperature')}")
        
        # Verify all keys exist
        expected_keys = [
            "vickers_hardness", "fracture_toughness", "transverse_rupture_strength",
            "youngs_modulus", "high_temp_hardness", "oxidation_resistance",
            "cte", "wettability", "relative_density", "vec",
            "atomic_size_difference", "mixing_enthalpy", "mixing_entropy",
            "electronegativity_difference", "omega", "solubility_parameter",
            "binding_energy", "sintering_method", "sintering_temperature",
            "sintering_time"
        ]
        
        missing_keys = [k for k in expected_keys if k not in data]
        if missing_keys:
            print(f"  [FAIL] Missing schema keys: {missing_keys}")
        else:
            print("  [OK] All extended schema keys present.")

if __name__ == "__main__":
    verify_props()
