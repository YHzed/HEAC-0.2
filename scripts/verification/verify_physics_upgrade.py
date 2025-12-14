"""
Physics Model Upgrade Verification Script

This script tests the enhanced physical models (CTE mismatch, Wettability, Deep Eutectic, Sigma Phase)
by comparing known "Good" and "Bad" cermet formulas to verify feature discrimination capability.
"""

import sys
import pandas as pd
from core.hea_cermet import MaterialProcessor

def main():
    print("=" * 80)
    print("Physics-Informed Feature Verification")
    print("=" * 80)
    
    # Initialize processor
    processor = MaterialProcessor()
    
    # Test Cases
    test_cases = [
        {
            'name': 'Good: Pure Co Binder (Baseline)',
            'formula': 'Co',
            'expected': 'Low Sigma Risk, High Wettability, High T_liq'
        },
        {
            'name': 'Good: Co-Ni (Classic)',
            'formula': 'CoNi',
            'expected': 'Low Sigma Risk, High Wettability'
        },
        {
            'name': 'Moderate: CoCrFeNi (Cantor)',
            'formula': 'CoCrFeNi',
            'expected': 'Moderate Sigma Risk (Cr presence), Moderate Wettability'
        },
        {
            'name': 'Bad: High Cr Content',
            'formula': 'Cr3Co',
            'expected': 'High Sigma Risk, Lower Wettability'
        },
        {
            'name': 'Bad: AlCoCrFeNi (High VEC)',
            'formula': 'AlCoCrFeNi',
            'expected': 'Potential Sigma Risk, Mixed Wettability'
        },
        {
            'name': 'Test: Ti Addition (Strong Carbide Former)',
            'formula': 'CoTi',
            'expected': 'High C Deficiency, Lower T_liq'
        }
    ]
    
    results = []
    
    for tc in test_cases:
        print(f"\n{'-' * 80}")
        print(f"Testing: {tc['name']}")
        print(f"Formula: {tc['formula']}")
        print(f"Expected: {tc['expected']}")
        print(f"{'-' * 80}")
        
        # Parse composition
        comp = processor.parse_formula(tc['formula'])
        
        if not comp:
            print(f"ERROR: Failed to parse {tc['formula']}")
            continue
        
        # Calculate properties
        basic_props = processor.calculate_properties(comp)
        h_mix = processor.calculate_enthalpy(comp)
        physics_props = processor.calculate_binder_physics(comp, sinter_temp_c=1400)
        
        # Combine results
        result = {
            'Name': tc['name'],
            'Formula': tc['formula'],
            **basic_props,
            'H_mix (kJ/mol)': round(h_mix, 2),
            **physics_props
        }
        
        results.append(result)
        
        # Print key metrics
        print(f"\nKey Physics Features:")
        print(f"  VEC: {basic_props.get('VEC', 'N/A')}")
        print(f"  Delta (%): {basic_props.get('Delta (%)', 'N/A')}")
        print(f"  H_mix (kJ/mol): {round(h_mix, 2)}")
        print(f"  T_liquidus (K): {physics_props.get('T_liquidus (K)', 'N/A')}")
        print(f"  T_liquidus_Ideal (K): {physics_props.get('T_liquidus_Ideal (K)', 'N/A')}")
        print(f"  Eutectic Depression (K): {physics_props.get('T_liquidus_Ideal (K)', 0) - physics_props.get('T_liquidus (K)', 0)}")
        print(f"  CTE Mismatch (um/m/K): {physics_props.get('CTE Mismatch (um/m/K)', 'N/A')}")
        print(f"  Wettability Index (0-10): {physics_props.get('Wettability Index (0-10)', 'N/A')}")
        print(f"  Sigma Phase Risk: {physics_props.get('Sigma Phase Risk', 'N/A')}")
        print(f"  C Deficiency Potential: {physics_props.get('C Deficiency Potential', 'N/A')}")
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print(df.to_string(index=False))
    
    # Key Observations
    print("\n" + "=" * 80)
    print("KEY OBSERVATIONS")
    print("=" * 80)
    
    # 1. Sigma Phase Risk
    print("\n1. Sigma Phase Risk Assessment:")
    high_risk = df[df['Sigma Phase Risk'] >= 2]
    if not high_risk.empty:
        print(f"   High Risk Formulas (Score >= 2):")
        for _, row in high_risk.iterrows():
            print(f"     - {row['Name']}: Risk Score = {row['Sigma Phase Risk']}")
    else:
        print("   No high-risk formulas detected.")
    
    # 2. CTE Mismatch
    print("\n2. CTE Mismatch (Thermal Stress Risk):")
    print(f"   Range: {df['CTE Mismatch (um/m/K)'].min():.2f} - {df['CTE Mismatch (um/m/K)'].max():.2f}")
    print(f"   Mean: {df['CTE Mismatch (um/m/K)'].mean():.2f}")
    
    # 3. Wettability
    print("\n3. Wettability Index (Interface Strength):")
    print(f"   Range: {df['Wettability Index (0-10)'].min():.2f} - {df['Wettability Index (0-10)'].max():.2f}")
    print(f"   Best: {df.loc[df['Wettability Index (0-10)'].idxmax(), 'Name']}")
    
    # 4. Eutectic Depression
    df['Eutectic_Depression'] = df['T_liquidus_Ideal (K)'] - df['T_liquidus (K)']
    print("\n4. Eutectic Depression (Deep Eutectic Effect):")
    print(f"   Range: {df['Eutectic_Depression'].min():.0f} - {df['Eutectic_Depression'].max():.0f} K")
    print(f"   Largest Depression: {df.loc[df['Eutectic_Depression'].idxmax(), 'Name']} ({df['Eutectic_Depression'].max():.0f} K)")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    
    return df

if __name__ == "__main__":
    main()
