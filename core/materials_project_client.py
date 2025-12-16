"""
Materials Project API Client Module
Wraps the official mp-api client to provide data access with caching and error handling.
"""
import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

try:
    from mp_api.client import MPRester
    from emmet.core.summary import SummaryDoc
except ImportError:
    MPRester = None
    SummaryDoc = None
    print("Warning: mp-api not found. Materials Project integration will be disabled.")

from core.config import config

try:
    from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
    from pymatgen.entries.computed_entries import ComputedEntry
    from pymatgen.core import Composition
except ImportError:
    MaterialsProject2020Compatibility = None
    ComputedEntry = None
    Composition = None

class MaterialsProjectClient:
    """
    Client for interacting with the Materials Project API.
    Includes caching mechanism to avoid redundant API calls.
    """
    
    def __init__(self):
        """Initialize the client with API key from config."""
        self.api_key = config.MP_API_KEY
        if not self.api_key:
            raise ValueError("Materials Project API key not configured. Please set MP_API_KEY in .env file.")
            
        self.cache_dir = config.get_cache_path()
        self.rate_limit_delay = 1.0 / config.MP_RATE_LIMIT
        self._last_request_time = 0
        
    def _get_cache_key(self, endpoint: str, identifier: str) -> str:
        """Generate a unique cache filename based on endpoint and identifier."""
        safe_id = "".join(c for c in identifier if c.isalnum() or c in ('-', '_'))
        return f"{endpoint}_{safe_id}.json"

    def _load_from_cache(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load data from local cache if valid."""
        if not config.MP_CACHE_ENABLED:
            return None
            
        file_path = self.cache_dir / filename
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if cache is expired
            cached_time = datetime.fromisoformat(data.get('_cached_at', '2000-01-01'))
            if datetime.now() - cached_time > timedelta(days=config.MP_CACHE_TTL_DAYS):
                return None
                
            return data.get('content')
        except Exception as e:
            print(f"Error reading cache {filename}: {e}")
            return None

    def _save_to_cache(self, filename: str, content: Any):
        """Save data to local cache."""
        if not config.MP_CACHE_ENABLED:
            return
            
        file_path = self.cache_dir / filename
        data = {
            '_cached_at': datetime.now().isoformat(),
            'content': content
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            print(f"Error writing to cache {filename}: {e}")

    def _enforce_rate_limit(self):
        """Ensure we don't exceed the rate limit."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def search_materials(self, chemsys_formula_id: str) -> List[Dict[str, Any]]:
        """
        Search for materials by chemical system, formula, or MP ID.
        
        Args:
            chemsys_formula_id: e.g., "Fe-C", "Fe2O3", or "mp-1234"
            
        Returns:
            List of material summary documents as dictionaries.
        """
        cache_key = self._get_cache_key("summary", chemsys_formula_id)
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        self._enforce_rate_limit()
        
        if not MPRester:
            print("Error: MPRester not available.")
            return []
            
        try:
            with MPRester(self.api_key) as mpr:
                # Request only commonly needed fields to reduce complexity
                fields = [
                    "material_id", "formula_pretty", "symmetry",
                    "density", "volume",
                    "formation_energy_per_atom", "energy_above_hull",
                    "band_gap", "is_stable"
                ]
                
                # Determine query type
                if '-' in chemsys_formula_id and not chemsys_formula_id.startswith('mp-'):
                    # Chemical system like "Fe-C"
                    docs = mpr.materials.summary.search(
                        chemsys=chemsys_formula_id,
                        fields=fields
                    )
                elif chemsys_formula_id.startswith('mp-'):
                    # Material ID
                    docs = mpr.materials.summary.search(
                        material_ids=[chemsys_formula_id],
                        fields=fields
                    )
                else:
                    # Formula like "Fe2O3" or "Si"
                    docs = mpr.materials.summary.search(
                        formula=chemsys_formula_id,
                        fields=fields
                    )
                
                # Convert to dictionaries using model_dump() for Pydantic v2 compatibility
                serialized_docs = [doc.model_dump() for doc in docs]
                
                self._save_to_cache(cache_key, serialized_docs)
                return serialized_docs
                
        except Exception as e:
            print(f"Error fetching data from Materials Project: {e}")
            raise

    def get_material_data(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific material data by MP ID.
        """
        results = self.search_materials(material_id)
        if results:
            return results[0]
        return None

    def get_formation_energy(self, formula: str) -> Optional[float]:
        """
        Get the lowest formation energy per atom for a given formula.
        Returns None if not found.
        """
        results = self.search_materials(formula)
        if not results:
            return None
            
        # Filter for lowest energy and preferably stable
        min_energy = float('inf')
        best_match = None
        
        for doc in results:
            energy = doc.get("formation_energy_per_atom")
            if energy is not None:
                if energy < min_energy:
                    min_energy = energy
                    best_match = energy
        
        return best_match

    def get_density(self, formula: str) -> Optional[float]:
        """
        Get density (g/cm^3) for a given formula (average of stable phases or lowest energy).
        """
        results = self.search_materials(formula)
        if not results:
            return None
            
        # Sort by stability (energy_above_hull)
        sorted_results = sorted(results, key=lambda x: x.get('energy_above_hull', float('inf')))
        
        # Return density of the most stable structure
        if sorted_results:
            return sorted_results[0].get('density')
            
        return None

    def get_fere_correction(self, composition: Union[str, Dict[str, float]]) -> float:
        """
        Calculate the Materials Project Compatibility correction (incl. FERE for gases)
        for a given composition.
        Returns correction energy in eV/atom.
        """
        if not MaterialsProject2020Compatibility or not ComputedEntry or not Composition:
            print("Warning: pymatgen not available for FERE correction.")
            return 0.0
            
        try:
            # Create a dummy computed entry
            # Energy is irrelevant for the *correction value* calculation in many cases,
            # for FERE (Gas corrections), it depends on composition.
            
            comp = Composition(composition)
            # Create a dummy entry with 0 energy
            entry = ComputedEntry(comp, 0.0)
            
            # Initialize Compatibility
            compat = MaterialsProject2020Compatibility()
            
            # process_entries returns a list of processed entries
            corrected_entries = compat.process_entries([entry])
            
            if corrected_entries:
                corrected_entry = corrected_entries[0]
                # The correction is the difference
                return corrected_entry.correction / comp.num_atoms
            
            return 0.0
            
        except Exception as e:
            print(f"Error calculating FERE correction: {e}")
            return 0.0

# Global instance - lazy or safe initialization
try:
    if config.MP_API_KEY:
        mp_client = MaterialsProjectClient()
    else:
        mp_client = None
except Exception as e:
    print(f"Warning: Failed to initialize MP client: {e}")
    mp_client = None
