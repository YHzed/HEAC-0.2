import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.material_database import db

print("Testing MaterialDatabase accessors...")

try:
    enthalpy = db.get_all_enthalpy_data()
    print(f"Enthalpy data loaded: {len(enthalpy)} entries")
except Exception as e:
    print(f"FAILED get_all_enthalpy_data: {e}")

try:
    compounds = db.get_all_compounds()
    print(f"Compounds data loaded: {len(compounds)} entries")
except Exception as e:
    print(f"FAILED get_all_compounds: {e}")

try:
    heac = db.get_heac_library()
    print(f"HEAC library loaded: {len(heac)} entries")
except Exception as e:
    print(f"FAILED get_heac_library: {e}")

print("Verification complete.")
