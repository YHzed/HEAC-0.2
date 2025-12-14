
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from core.config import config
from mp_api.client import MPRester

def debug():
    api_key = config.MP_API_KEY
    with MPRester(api_key) as mpr:
        print("Searching for TiC in summary...")
        docs = mpr.materials.summary.search(formula="TiC", fields=["material_id", "structure"])
        print(f"Found {len(docs)} TiC docs.")
        
        ids = [str(d.material_id) for d in docs]
        print(f"IDs: {ids[:5]}...")
        
        try:
            print("Fetching elasticity for these IDs...")
            el_docs = mpr.materials.elasticity.search(material_ids=ids, fields=["material_id", "k_voigt_reuss_hill", "g_voigt_reuss_hill"])
            print(f"Found {len(el_docs)} elastic docs.")
            
            for d in el_docs:
                print(f"  {d.material_id}: K={d.k_voigt_reuss_hill}, G={d.g_voigt_reuss_hill}")
        except Exception as e:
            print(f"Error fetching elasticity: {e}")

if __name__ == "__main__":
    debug()
