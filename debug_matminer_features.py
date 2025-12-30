
try:
    from matminer.featurizers.composition import YangSolidSolution, ElementProperty
    from pymatgen.core import Composition
    
    print("[OK] Matminer imports successful.")
    
    # Test YangSolidSolution
    yss = YangSolidSolution()
    print("\nYangSolidSolution Feature Labels:")
    print(yss.feature_labels())
    
    comp = Composition("CoCrFeNiMn")
    feats = yss.featurize(comp)
    print("\nFeature Values for CoCrFeNiMn:")
    for label, val in zip(yss.feature_labels(), feats):
        print(f"  {label}: {val}")
        
    # Test ElementProperty (VEC specifically if applicable, or generic)
    # usually ElementProperty handles periodic table properties
    ep = ElementProperty.from_preset("magpie")
    print("\nElementProperty (Magpie) Feature Labels (First 5):")
    print(ep.feature_labels()[:5])

except ImportError as e:
    print(f"[ERROR] ImportError: {e}")
except Exception as e:
    print(f"[ERROR] Error: {e}")
