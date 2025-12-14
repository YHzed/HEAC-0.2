from mp_api.client import MPRester
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("MP_API_KEY")

if not api_key:
    print("Error: MP_API_KEY not found in environment variables.")
    exit(1)

def fetch_heac():
    print("Connecting to Materials Project...")
    with MPRester(api_key) as mpr:
        # 1. Try to find a complex carbide (e.g., 3 metals + C)
        # Note: MP often doesn't have 5-component solid solutions indexed as single entries.
        # We will search for constituent binary carbides which are the basis of the HEA Cermet.
        
        constituents = ["Ti", "Zr", "Hf", "Nb", "Ta"]
        target_anion = "C"
        
        print(f"Searching for constituent carbides (M-{target_anion}) for M in {constituents}...")
        
        found_data = []
        
        for metal in constituents:
            # Search for binary M-C compounds
            # Using mpr.materials.summary correctly
            docs = mpr.materials.summary.search(chemsys=f"{metal}-{target_anion}", fields=["material_id", "formula_pretty", "formation_energy_per_atom", "is_stable", "symmetry", "structure"])
            
            if docs:
                # Filter for stable or lowest energy match
                # Sort by stability (is_stable=True first) then formation energy
                docs.sort(key=lambda x: (not x.is_stable, x.formation_energy_per_atom))
                best_doc = docs[0]
                print(f"Found {metal}-{target_anion}: {best_doc.formula_pretty} (ID: {best_doc.material_id}, Stable: {best_doc.is_stable})")
                found_data.append({
                    "material_id": str(best_doc.material_id),
                    "formula": best_doc.formula_pretty,
                    "formation_energy_per_atom": best_doc.formation_energy_per_atom,
                    "is_stable": best_doc.is_stable,
                    "symmetry": str(best_doc.symmetry),
                    # "structure": best_doc.structure.as_dict() # Structure might be too large to print, save to file
                })
            else:
                print(f"No results for {metal}-{target_anion}")
        
        # 2. Also try to find a ternary example if possible, e.g., (Ti,Zr)C
        print("\nSearching for ternary carbides (e.g., Ti-Zr-C)...")
        ternary_docs = mpr.materials.summary.search(chemsys="Ti-Zr-C", fields=["material_id", "formula_pretty"])
        if ternary_docs:
             print(f"Found ternary example: {ternary_docs[0].formula_pretty}")
             found_data.append({
                "material_id": str(ternary_docs[0].material_id),
                "formula": ternary_docs[0].formula_pretty,
                "note": "Ternary example"
             })
        else:
             print("No Ti-Zr-C found.")

        # Save results
        if found_data:
            filename = "heac_constituents_data.json"
            with open(filename, "w") as f:
                json.dump(found_data, f, indent=4)
            print(f"\nSaved data for {len(found_data)} materials to {filename}")
        else:
            print("No data found.")

if __name__ == "__main__":
    fetch_heac()
