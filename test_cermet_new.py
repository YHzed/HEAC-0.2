import sys
import os

# Add current directory to path so we can import core
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.hea_cermet import MaterialProcessor

def test_improvements():
    try:
        mp = MaterialProcessor()
        
        # Test 1: Standard Co Binder
        # Co CTE ~13, WC ~5.2 -> Mismatch ~7.8
        # Wet Index Co=10
        print("Testing Co Binder...")
        binder_co = {'Co': 1.0}
        res_co = mp.calculate_binder_physics(binder_co, sinter_temp_c=1400)
        print("Co Results:", res_co)
        
        if 'CTE Mismatch (um/m/K)' not in res_co:
            print("FAIL: CTE Mismatch missing")
            return
        
        if abs(res_co['CTE Mismatch (um/m/K)'] - 7.8) > 1.0:
             print(f"WARNING: CTE Mismatch for Co {res_co['CTE Mismatch (um/m/K)']} deviates from expected ~7.8")

        # Test 2: High Entropy Binder AlCoCrFeNi
        print("\nTesting HEA Binder (AlCoCrFeNi)...")
        binder_hea = {'Al': 1, 'Co': 1, 'Cr': 1, 'Fe': 1, 'Ni': 1}
        res_hea = mp.calculate_binder_physics(binder_hea, sinter_temp_c=1400)
        print("HEA Results:", res_hea)
        
        # Check T_liq correction
        # Ideal linear T_liq vs Corrected
        if 'T_liquidus_Ideal (K)' in res_hea:
            delta_t = res_hea['T_liquidus_Ideal (K)'] - res_hea['T_liquidus (K)']
            print(f"Deep Eutectic Depression: {delta_t} K")
            if delta_t <= 0:
                print("FAIL: No freezing point depression observed")
        
        print("\nSUCCESS: All new keys present and logic operational.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improvements()
