
import sys
import os
import pandas as pd
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.hea_cermet import MaterialProcessor

def verify_features():
    mp = MaterialProcessor()
    
    # Test Cases
    # 1. Standard WC-Co (Reference)
    # 2. HEA Cermet (Ti-Zr-Hf-V-Nb-C + Co binder) - Wait, usually it's WC + (CoCrFeNi)
    # Let's try WC + AlCoCrFeNi binder
    
    test_data = {
        'Formula': [
            'WC80Co20', # Conventional
            'WC80Co5Ni5Fe5Cr5Al0', # High Entropy Binder candidate
            'TiC50Co50', # Different Ceramic
            'WC80Ti10Co10' # Mixed binder with Ti (High Carbon Affinity)
        ],
        'Sinter_Temp': [1400, 1450, 1500, 1400] # Celsius
    }
    
    df = pd.DataFrame(test_data)
    
    print("Processing Batch...")
    result_df = mp.process_batch_extended(df, 'Formula', is_weight_percent=True) # Usually industry uses Wt%
    
    # Define columns to check
    check_cols = [
        'Formula', 
        'Binder Vol Frac', 
        'T_liquidus (K)', 
        'Homologous Temp', 
        'Lattice Mismatch (%)', 
        'Shear Modulus Diff (GPa)', 
        'C Deficiency Potential'
    ]
    
    # Filter columns that exist
    cols = [c for c in check_cols if c in result_df.columns]
    
    print("\n--- Verified Advanced Features ---")
    print(result_df[cols].to_markdown(index=False))
    
    # Visual check logic
    # WC-Co should have Low Mismatch (Co is FCC/HCP match).
    # Carbon Deficiency: Ti should be high negative (high affinity). Co/Ni should be 0 or low.
    
if __name__ == "__main__":
    verify_features()
