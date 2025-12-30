import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.composition_parser_enhanced import enhanced_parser

test_cases = [
    "Cr20 Fe20 Mn20 Ni40",
    "CoCrFeNi",
    "CoCrFeNiMo",
    "90 WC 10 Co",
    "WC-10Co"
]

print("Testing EnhancedCompositionParser...")
for case in test_cases:
    print(f"\nParsing: '{case}'")
    result = enhanced_parser.parse(case)
    if result and result.get('success'):
        print(f"[OK] Success!")
        print(f"   Binder Formula: {result.get('binder_formula')}")
        print(f"   Ceramic Formula: {result.get('ceramic_formula')}")
        print(f"   Binder wt%: {result.get('binder_wt_pct')}")
        print(f"   Is HEA: {result.get('is_hea')}")
    else:
        print(f"[FAIL] Failed: {result.get('message') if result else 'None'}")
