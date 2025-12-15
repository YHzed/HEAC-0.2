
from pymatgen.core import Element
try:
    from mp_api.client import MPRester
except ImportError:
    pass

elements = ["Al", "Fe", "Ti", "C", "Cu"]
for el_str in elements:
    el = Element(el_str)
    print(f"Element: {el_str}")
    print(f"  Group: {el.group}")
    print(f"  Z: {el.Z}")
    try:
        print(f"  Valence: {el.valence}") # Check if this exists
    except:
        print(f"  Valence: Not found")
    
    # Check other attributes
    print(f"  Row: {el.row}")
    print(f"  Number of valence electrons (Z - core?): {el.Z - len(el.core_electrons) if hasattr(el, 'core_electrons') else 'N/A'}")
    
