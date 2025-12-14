
import sys
import os

# Add project root to sys.path to import modules
sys.path.append(r'd:\ML\HEAC 0.2')

from core.material_database import db

def verify():
    print("Verifying Material Database...")

    # Test 1: Compounds Enthalpy (Legacy check)
    wc_h = db.get_formation_enthalpy("WC")
    print(f"WC Enthalpy: {wc_h} (Expected: -40.0)")
    assert wc_h == -40.0

    # Test 2: Compounds Density (New feature)
    wc_rho = db.get_compound_density("WC")
    print(f"WC Density: {wc_rho} (Expected: 15.63)")
    assert wc_rho == 15.63

    tin_rho = db.get_compound_density("TiN")
    print(f"TiN Density: {tin_rho} (Expected: 5.22)")
    assert tin_rho == 5.22

    # Test 3: Missing Density
    unknown_rho = db.get_compound_density("Unknown")
    print(f"Unknown Density: {unknown_rho} (Expected: None)")
    assert unknown_rho is None

    # Test 4: Enthalpy (New pairs)
    al_w = db.get_enthalpy("Al", "W")
    print(f"Al-W Enthalpy: {al_w} (Expected: -2)")
    assert al_w == -2

    ta_hf = db.get_enthalpy("Ta", "Hf")
    print(f"Ta-Hf Enthalpy: {ta_hf} (Expected: 3)")
    assert ta_hf == 3

    print("Verification Successful!")

if __name__ == "__main__":
    verify()
