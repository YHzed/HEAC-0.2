
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from core.config import config
from mp_api.client import MPRester

def inspect_fields():
    api_key = config.MP_API_KEY
    if not api_key:
        print("MP_API_KEY not found.")
        return

    with MPRester(api_key) as mpr:
        print("Available fields in summary:")
        try:
            print(mpr.materials.summary.available_fields)
        except:
            print("Could not print available fields.")
            
        print("\nFetching summary for TiC (minimal fields)...")
        # specific query to check if we can get basic info
        docs = mpr.materials.summary.search(formula="TiC", fields=["material_id", "formula_pretty", "density"])
        if docs:
            print(f"Found {len(docs)} docs.")
            print("Material ID:", docs[0].material_id)

if __name__ == "__main__":
    inspect_fields()
