
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.system_architecture import DesignSpace, PhysicsEngine

def verify_hea_cermet_theory():
    print("=== HEA Binder + Ceramic Hard Phase: Theoretical Verification ===\n")
    
    # 1. Define Design: High Entropy Binder + WC Hard Phase
    # Binder: CoCrFeNi (Equiatomic approx)
    print("1. DEFINING SYSTEM")
    print("   Hard Phase: WC (Tungsten Carbide)")
    print("   Binder Phase: HEA (Co-Cr-Fe-Ni)")
    
    design = DesignSpace(
        hea_composition={'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0},
        ceramic_composition={'WC': 1.0}, # Fixed target for now
        ceramic_vol_fraction=0.5,
        sinter_temp_c=1400
    )
    
    # 2. Analyze Physics
    engine = PhysicsEngine()
    features = engine.compute_features(design)
    
    # 3. Detailed Output of Interaction
    print("\n2. PHYSICS ENGINE ANALYSIS")
    
    # A. Binder Properties
    print("\n   [Binder Phase Properties]")
    print(f"   - Composition: {design.get_binder_composition_normalized()}")
    print(f"   - VEC (Valence Electron Concentration): {features['VEC']:.4f}")
    print(f"     -> Theory: VEC >= 8.0 indicates FCC structure (Ductile).")
    print(f"   - S_mix (Mixing Entropy): {features['S_mix']:.4f} R")
    print(f"     -> Theory: High Entropy (>1.5R) stabilizes solid solution.")

    # B. Interface / Interaction
    print("\n   [Interface Interaction: Binder <-> WC]")
    print(f"   - Lattice Mismatch: {features['Lattice_Mismatch']*100:.4f}%")
    print(f"     -> Calculation: |a_binder - a_WC| / a_WC")
    print(f"     -> Result: Low mismatch (<5%) implies coherent/semi-coherent interface (Strong Bonding).")
    
    print(f"   - CTE Mismatch: {features['CTE_Mismatch']:.4f} um/m/K")
    print(f"     -> Result: Lower difference reduces thermal stress during cooling.")
    
    print(f"   - Wettability Index: {features['Wettability_Index']:.4f} (0-10)")
    print(f"     -> Theory: Higher index means better wetting of WC by the HEA binder.")

    print(f"     -> Theory: Higher index means better wetting of WC by the HEA binder.")

    # D. Volume Fractions (New Request)
    print("\n   [Volume Fractions Analysis]")
    vol_stats = engine.calculate_volume_fractions(design)
    print(f"   - Ceramic Phase (WC): {vol_stats['Phase_Ceramic']*100:.1f} Vol%")
    print(f"   - Binder Phase (HEA): {vol_stats['Phase_Binder']*100:.1f} Vol%")
    print(f"   - Binder Density: {vol_stats['Density_Binder_Theoretical']} g/cm3")
    print("   - Element Distribution (Vol% in Composite):")
    for k, v in vol_stats.items():
        if 'Elem_Vol_' in k:
            el = k.replace('Elem_Vol_', '')
            print(f"     * {el}: {v*100:.2f}%")

    # C. Process
    print("\n   [Process Logic]")
    print(f"   - T_sinter: {design.sinter_temp_c} C")
    print(f"   - T_homologous: {features['T_homologous']:.4f}")
    print(f"     -> Theory: T_sinter / T_liquidus. Value > 0.8 required for good densification.")

if __name__ == "__main__":
    verify_hea_cermet_theory()
