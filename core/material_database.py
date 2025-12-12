import json
import os
from typing import Dict, Any, Optional

class MaterialDatabase:
    _instance = None
    _data: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MaterialDatabase, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self):
        """Loads element data from the JSON file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, 'data', 'elements.json')
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            # Fallback or empty init if file missing
            print(f"Warning: Element database not found at {data_path}")
            self._data = {}
        except json.JSONDecodeError:
            print(f"Error: Failed to decode element database at {data_path}")
            self._data = {}

        enthalpy_path = os.path.join(current_dir, 'data', 'enthalpy.json')
        try:
            with open(enthalpy_path, 'r', encoding='utf-8') as f:
                self._enthalpy_data = json.load(f)
        except FileNotFoundError:
            self._enthalpy_data = {}

        compounds_path = os.path.join(current_dir, 'data', 'compounds.json')
        try:
            with open(compounds_path, 'r', encoding='utf-8') as f:
                self._compounds_data = json.load(f)
        except FileNotFoundError:
            self._compounds_data = {}

    def get_element(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the dictionary of properties for a given element symbol.
        """
        return self._data.get(symbol)

    def get_property(self, symbol: str, property_name: str, default: Any = None) -> Any:
        """
        Retrieves a specific property for an element.
        """
        element = self._data.get(symbol)
        if element:
            return element.get(property_name, default)
        return default

    def get_enthalpy(self, el1: str, el2: str) -> float:
        """
        Retrieves the mixing enthalpy for a binary pair.
        Order of elements does not matter.
        """
        pair = sorted([el1, el2])
        key = f"{pair[0]}-{pair[1]}"
        return self._enthalpy_data.get(key, 0.0)

    def get_formation_enthalpy(self, formula: str) -> Optional[float]:
        """
        Retrieves the standard formation enthalpy for a compound (e.g. 'WC', 'TiC').
        Returns None if not found.
        """
        data = self._compounds_data.get(formula)
        if isinstance(data, dict):
            return data.get('enthalpy')
        return data

    def get_compound_density(self, formula: str) -> Optional[float]:
        """
        Retrieves the density for a compound in g/cm³.
        Returns None if not found.
        """
        data = self._compounds_data.get(formula)
        if isinstance(data, dict):
            return data.get('density')
        return None

    def get_all_elements(self) -> Dict[str, Dict[str, Any]]:
        """Returns the entire database."""
        return self._data

# Simple global instance for easy import
db = MaterialDatabase()
