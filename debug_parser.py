
import sys
import os
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.composition_parser_enhanced import EnhancedCompositionParser

def test_parser():
    parser = EnhancedCompositionParser()
    
    test_cases = [
        "80.0 Ti(C,N) 20.0 Cr20 Fe20 Mn20 Ni40",
        "70.0 (Ti,W)C,Cr3C2 30.0 Co20 Cr20 Fe20 Ni35 Ti5",
        "85.0 (Ti,W)C 15.0 CoCrFeNiMo",
        "70.0 (Ti,W)C 30.0 CoCrFeNiMo",
        "90 WC 10 Co" # Should still work
    ]
    
    print("Testing EnhancedCompositionParser...")
    print("-" * 60)
    
    for case in test_cases:
        print(f"\nInput: '{case}'")
        try:
            result = parser.parse(case)
            if result and result.get('success'):
                print("✅ Success!")
                print(f"   Ceramic: {result.get('ceramic_elements')} ({result.get('ceramic_formula')})")
                print(f"   Binder:  {result.get('binder_formula')} ({result.get('binder_wt_pct')}%)")
            else:
                print("❌ Failed")
                print(f"   Message: {result.get('message') if result else 'None'}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_parser()
