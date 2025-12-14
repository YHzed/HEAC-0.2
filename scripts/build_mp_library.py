
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Build path to core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import config
from mp_api.client import MPRester
from core.hea_calculator import hea_calc

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("library_build.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
TRANSITION_METALS = [
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", 
    "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", 
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au"
]
NON_METALS = ["C", "N", "B"]
OUTPUT_FILE = Path(__file__).parent.parent / "core" / "data" / "heac_mp_library.json"

def get_target_systems() -> List[str]:
    """
    Generate list of chemical systems to query.
    We want:
    1. Pure elements (Unary)
    2. Metal-NonMetal binaries (M-C, M-N, M-B)
    """
    systems = []
    
    # Unaries
    logger.info("Generating Unary systems...")
    for m in TRANSITION_METALS:
        systems.append(m)
    for nm in NON_METALS:
        systems.append(nm)
        
    # Binaries
    logger.info("Generating Binary systems...")
    for m in TRANSITION_METALS:
        for nm in NON_METALS:
            systems.append(f"{m}-{nm}")
            
    return systems

def fetch_data(api_key: str, systems: List[str]) -> Dict[str, Any]:
    """
    Fetch data from Materials Project for the given systems.
    Includes summary data and elasticity data.
    """
    all_data = {}
    material_ids_to_fetch_elasticity = []
    
    fields = [
        "material_id", 
        "formula_pretty", 
        "composition", # Needed for VEC/Delta calc
        "structure", 
        "symmetry", 
        "formation_energy_per_atom", 
        "energy_above_hull", 
        "is_stable", 
        "band_gap", 
        "density", 
        "total_magnetization"
    ]
    
    # 1. Fetch Summary Data
    with MPRester(api_key) as mpr:
        total = len(systems)
        for idx, sys_str in enumerate(systems):
            logger.info(f"[{idx+1}/{total}] Querying {sys_str}...")
            
            try:
                if "-" in sys_str:
                    docs = mpr.materials.summary.search(chemsys=sys_str, fields=fields)
                else:
                    docs = mpr.materials.summary.search(chemsys=sys_str, fields=fields)
                
                if not docs:
                    continue
                
                logger.info(f"  Found {len(docs)} materials for {sys_str}")
                
                for doc in docs:
                    mid = str(doc.material_id)
                    try:
                        doc_dict = doc.model_dump()
                    except AttributeError:
                        doc_dict = doc.dict()
                    
                    # Convert composition to dict of {Element: Fraction} for calculator
                    # composition field typically comes as object, model_dump handles it but let's ensure
                    # We might need to reconstruct it for our calculator if it's stored as string or whatever
                    # MP returns composition as a Composite object usually.
                    
                    all_data[mid] = doc_dict
                    material_ids_to_fetch_elasticity.append(mid)
                    
            except Exception as e:
                logger.error(f"Error fetching {sys_str}: {e}")

        # 2. Fetch Elasticity Data (Batch)
        logger.info(f"Fetching elasticity data for {len(material_ids_to_fetch_elasticity)} materials...")
        
        # We can't query all at once if list is too long (limit is usually 1000?)
        # Let's chunk it
        chunk_size = 500
        elastic_data_map = {}
        
        for i in range(0, len(material_ids_to_fetch_elasticity), chunk_size):
            chunk = material_ids_to_fetch_elasticity[i:i+chunk_size]
            logger.info(f"  Fetching elasticity chunk {i}-{i+len(chunk)}...")
            try:
                # elasticity.search returns ElasticityDoc
                # We filter by material_ids
                el_docs = mpr.materials.elasticity.search(material_ids=chunk, fields=["material_id", "k_voigt_reuss_hill", "g_voigt_reuss_hill", "homogeneous_poisson"])
                
                for doc in el_docs:
                    mid = str(doc.material_id)
                    elastic_data_map[mid] = {
                        "bulk_modulus": doc.k_voigt_reuss_hill,
                        "shear_modulus": doc.g_voigt_reuss_hill,
                        "poisson_ratio": doc.homogeneous_poisson
                    }
            except Exception as e:
                logger.error(f"Error fetching elasticity chunk: {e}")

    # 3. Merge and Calculate Properties
    logger.info("Merging and calculating derived properties...")
    
    for mid, data in all_data.items():
        # Merge Elasticity
        if mid in elastic_data_map:
            data.update(elastic_data_map[mid])
        else:
            data["bulk_modulus"] = None
            data["shear_modulus"] = None
            data["poisson_ratio"] = None
            
        # Extract composition for calculator
        # data['composition'] is likely a dict or Composite object dump
        # Example dump: {'Ti': 1.0, 'C': 1.0} or something similar depending on MP version
        # Usually summary doc 'composition' dump is a dictionary-like structure
        # Let's inspect data['composition'] to safe-guard
        
        comp_dict = {}
        try:
            raw_comp = data.get('composition', {})
            # If it's a dict with element keys
            for k, v in raw_comp.items():
                # raw_comp might be complex, but usually 'Ti': 1.0
                # If pymatgen Composition dump, it might be nested
                # Safe way: retrieve formula_pretty if composition fails
                pass 
                
            # Actually, let's use pymatgen Composition from formula_pretty to be safe
            from pymatgen.core import Composition
            comp = Composition(data.get('formula_pretty'))
            # Get atomic fractions
            comp_dict = {str(el): amt for el, amt in comp.get_el_amt_dict().items()}
            # Normalize to fractions
            total = sum(comp_dict.values())
            comp_dict = {k: v/total for k, v in comp_dict.items()}
            
        except Exception as e:
            logger.warning(f"Could not parse composition for {mid}: {e}")
            continue
            
        # Calculations
        try:
            data['vec'] = hea_calc.calculate_vec(comp_dict)
            data['delta_size_diff'] = hea_calc.calculate_atomic_size_difference(comp_dict)
            data['electronegativity_diff'] = hea_calc.calculate_electronegativity_difference(comp_dict)
            data['mixing_enthalpy'] = hea_calc.calculate_mixing_enthalpy(comp_dict)
            data['mixing_entropy'] = hea_calc.calculate_mixing_entropy(comp_dict)
            
            # Omega (Tm needed)
            data['omega'] = hea_calc.calculate_omega(comp_dict)
            
            # Hardness (G, B needed)
            g = data.get('shear_modulus')
            b = data.get('bulk_modulus')
            if g and b:
                data['hardness_chen'] = hea_calc.estimate_hardness_chen(b, g)
                data['hardness_tian'] = hea_calc.estimate_hardness_tian(b, g)
                data['fracture_toughness_est'] = hea_calc.estimate_fracture_toughness_niu(b, g)
            else:
                data['hardness_chen'] = None
                data['hardness_tian'] = None
                data['fracture_toughness_est'] = None
                
            # Placeholders for manual entry
            data['sintering_temp'] = None
            data['sintering_time'] = None
            data['sintering_method'] = None
            
        except Exception as e:
            logger.error(f"Calculation error for {mid}: {e}")

    return all_data

def save_library(data: Dict[str, Any], filepath: Path):
    """Save the fetched data to a JSON file."""
    output = {
        "_meta": {
            "created_at": datetime.now().isoformat(),
            "source": "Materials Project",
            "entries_count": len(data),
            "description": "Expanded HEAC Library with Elasticity and Calculated Properties"
        },
        "materials": data
    }
    
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)
        
    logger.info(f"Saved {len(data)} entries to {filepath}")

def main():
    if not config.MP_API_KEY:
        logger.error("MP_API_KEY not found in config. Please check your .env file.")
        return

    logger.info("Starting EXPANDED HEAC Material Library Build (Elasticity + Props)...")
    
    target_systems = get_target_systems()
    logger.info(f"Total target systems: {len(target_systems)}")
    
    # Uncomment for testing
    # target_systems = target_systems[:5]
    
    data = fetch_data(config.MP_API_KEY, target_systems)
    save_library(data, OUTPUT_FILE)
    logger.info("Build Complete!")

if __name__ == "__main__":
    main()
