import json
import os
from typing import Dict, Any, Optional, List

class MaterialDatabase:
    _instance = None
    _data: Dict[str, Dict[str, Any]] = {}
    _heac_library: Dict[str, Any] = {}
    _mp_client = None  # 延迟加载MP客户端

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MaterialDatabase, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def get_all_enthalpy_data(self) -> Dict[str, float]:
        """Returns the entire enthalpy dataset."""
        return self._enthalpy_data

    def get_all_compounds(self) -> Dict[str, Dict[str, Any]]:
        """Returns the entire compounds dataset."""
        return self._compounds_data

    def get_heac_library(self) -> Dict[str, Any]:
        """Returns the entire HEAC library."""
        return self._heac_library

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
            
        # 记录compounds.json的路径，用于更新
        self._compounds_path = compounds_path

        # 加载新的HEAC MP Library
        self._load_heac_library()

    def _load_heac_library(self):
        """Loads the HEAC MP library from JSON."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(current_dir, 'data', 'heac_mp_library.json')
        
        try:
            with open(lib_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._heac_library = data.get('materials', {})
        except FileNotFoundError:
            # It's okay if it doesn't exist yet, we might be building it
            self._heac_library = {}
        except json.JSONDecodeError:
            print(f"Error: Failed to decode HEAC library at {lib_path}")
            self._heac_library = {}

    def _get_mp_client(self):
        """延迟加载Materials Project客户端"""
        if self._mp_client is None:
            try:
                from core.materials_project_client import MaterialsProjectClient
                self._mp_client = MaterialsProjectClient()
            except Exception as e:
                print(f"Warning: Could not initialize Materials Project client: {e}")
                self._mp_client = False  # 标记为不可用
        return self._mp_client if self._mp_client is not False else None

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

    def get_formation_enthalpy(self, formula: str, use_mp: bool = False) -> Optional[float]:
        """
        Retrieves the standard formation enthalpy for a compound (e.g. 'WC', 'TiC').
        
        Args:
            formula: Chemical formula
            use_mp: If True and local data not found, query Materials Project
            
        Returns:
            Formation enthalpy in kJ/mol or None if not found
        """
        # 首先尝试本地数据
        data = self._compounds_data.get(formula)
        if isinstance(data, dict):
            enthalpy = data.get('enthalpy')
            if enthalpy is not None:
                return enthalpy
        elif data is not None:
            return data
            
        # 如果本地没有且允许使用MP，从网络获取
        if use_mp:
            return self.get_formation_enthalpy_from_mp(formula)
        
        return None

    def get_compound_density(self, formula: str, use_mp: bool = False) -> Optional[float]:
        """
        Retrieves the density for a compound in g/cm³.
        
        Args:
            formula: Chemical formula
            use_mp: If True and local data not found, query Materials Project
            
        Returns:
            Density in g/cm³ or None if not found
        """
        # 首先尝试本地数据
        data = self._compounds_data.get(formula)
        if isinstance(data, dict):
            density = data.get('density')
            if density is not None:
                return density
                
        # 如果本地没有且允许使用MP，从网络获取
        if use_mp:
            return self.get_density_from_mp(formula)
            
        return None
    
    def get_ceramic_properties(self, formula: str, use_mp: bool = False) -> Optional[Dict[str, Any]]:
        """
        获取陶瓷材料的完整属性（密度、晶格参数、结构等）
        
        Args:
            formula: 化学式（如 'WC', 'TiC', 'TiN'）
            use_mp: 是否使用Materials Project API（在线查询）
        
        Returns:
            {
                'density': float,  # g/cm³
                'structure': str,  # 'hexagonal', 'fcc', etc.
                'lattice_a': float,  # Å
                'lattice_c': float,  # Å (if applicable)
                'neighbor_distance': float,  # Å
                'space_group': str,
                'source': str  # 'local' or 'Materials Project'
            }
            如果未找到返回None
        """
        # 1. 尝试从compounds.json获取本地数据
        local_data = self._compounds_data.get(formula)
        if local_data and isinstance(local_data, dict):
            # 检查是否包含结构信息
            if 'structure' in local_data or 'lattice_a' in local_data:
                result = local_data.copy()
                if 'source' not in result:
                    result['source'] = 'local'
                return result
        
        # 2. 如果允许，从Materials Project获取
        if use_mp:
            mp_data = self.get_mp_data(formula)
            if mp_data:
                # 从MP数据提取陶瓷属性
                result = {
                    'density': mp_data.get('density'),
                    'source': 'Materials Project',
                    'material_id': mp_data.get('material_id')
                }
                # 尝试从structure对象提取晶格参数
                structure = mp_data.get('structure')
                if structure:
                    try:
                        lattice = structure.lattice
                        result['lattice_a'] = lattice.a
                        result['lattice_b'] = lattice.b
                        result['lattice_c'] = lattice.c
                        result['space_group'] = structure.get_space_group_info()[0]
                        # 计算最近邻距离（简化版）
                        if hasattr(lattice, 'a'):
                            result['neighbor_distance'] = lattice.a / (2 ** 0.5)  # FCC近似
                    except Exception as e:
                        print(f"Warning: Could not extract lattice params from MP structure: {e}")
                
                return result
        
        # 3. 没有找到数据
        return None

    def get_all_elements(self) -> Dict[str, Dict[str, Any]]:
        """Returns the entire database."""
        return self._data
    
    def get_heac_material_data(self, formula: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves material data from the local HEAC MP library.
        Searches by formula (e.g., 'TiC', 'Al2O3').
        Returns the entry with the lowest formation energy if multiple exist.
        """
        candidates = []
        for mid, data in self._heac_library.items():
            if data.get('formula_pretty') == formula:
                candidates.append(data)
        
        if not candidates:
            return None
            
        # Return candidate with lowest formation energy
        # Filter out those without energy
        valid_candidates = [c for c in candidates if c.get('formation_energy_per_atom') is not None]
        
        if not valid_candidates:
            # If all are None, just return first candidate
            return candidates[0]
            
        return min(valid_candidates, key=lambda x: x['formation_energy_per_atom'])

    def get_extended_properties(self, formula: str) -> Dict[str, Any]:
        """
        Retrieves a comprehensive dictionary of properties for a material.
        Includes placeholders for experimental data.
        """
        data = self.get_heac_material_data(formula)
        if not data:
            return {}
            
        # Ensure all requested fields exist (even if None)
        extended_fields = [
            "vickers_hardness", "fracture_toughness", "transverse_rupture_strength",
            "youngs_modulus", "high_temp_hardness", "oxidation_resistance",
            "cte", "wettability", "relative_density", "vec",
            "atomic_size_difference", "mixing_enthalpy", "mixing_entropy",
            "electronegativity_difference", "omega", "solubility_parameter",
            "binding_energy", "sintering_method", "sintering_temperature",
            "sintering_time"
        ]
        
        # specific mapping from internal keys to user requested friendly names if needed
        # Internal: hardness_chen, hardness_tian -> External: vickers_hardness (est)
        
        result = data.copy()
        
        # Fill computed/mapped fields
        result['vickers_hardness'] = data.get('hardness_chen') # Default to Chen model
        result['fracture_toughness'] = data.get('fracture_toughness_est')
        result['atomic_size_difference'] = data.get('delta_size_diff')
        result['electronegativity_difference'] = data.get('electronegativity_diff')
        
        # Calculate Young's Modulus from Bulk/Shear if missing but B/G exist
        # E = 9KG / (3K + G)
        k = data.get('bulk_modulus')
        g = data.get('shear_modulus')
        if k and g and not result.get('youngs_modulus'):
            result['youngs_modulus'] = (9 * k * g) / (3 * k + g)
            
        # Fill missing with None
        for field in extended_fields:
            if field not in result:
                result[field] = None
                
        return result

    def get_heac_library_stats(self) -> Dict[str, Any]:
        """Returns statistics about the loaded HEAC library."""
        return {
            "count": len(self._heac_library),
            "systems": len(set(d.get('formula_pretty') for d in self._heac_library.values()))
        }
    
    # ========== Materials Project 集成方法 ==========
    
    def get_mp_data(self, formula: str) -> Optional[Dict[str, Any]]:
        """
        从Materials Project获取材料数据
        
        Args:
            formula: 化学式或MP ID (例如: "TiO2" or "mp-1234")
            
        Returns:
            材料数据字典，如果未找到返回None
        """
        mp_client = self._get_mp_client()
        if not mp_client:
            return None
            
        try:
            return mp_client.get_material_data(formula)
        except Exception as e:
            print(f"Error fetching data from Materials Project for {formula}: {e}")
            return None
    
    def get_formation_enthalpy_from_mp(self, formula: str) -> Optional[float]:
        """
        从Materials Project获取生成焓
        
        Args:
            formula: 化学式
            
        Returns:
            生成焓 (eV/atom)，注意单位与本地数据(kJ/mol)不同
        """
        mp_client = self._get_mp_client()
        if not mp_client:
            return None
            
        try:
            return mp_client.get_formation_energy(formula)
        except Exception as e:
            print(f"Error fetching formation enthalpy from MP for {formula}: {e}")
            return None
    
    def get_density_from_mp(self, formula: str) -> Optional[float]:
        """
        从Materials Project获取密度
        
        Args:
            formula: 化学式
            
        Returns:
            密度 (g/cm³)
        """
        mp_client = self._get_mp_client()
        if not mp_client:
            return None
            
        try:
            return mp_client.get_density(formula)
        except Exception as e:
            print(f"Error fetching density from MP for {formula}: {e}")
            return None
    
    def update_compound_from_mp(self, formula: str, save: bool = True) -> bool:
        """
        从Materials Project更新化合物数据到本地JSON文件
        
        Args:
            formula: 化学式
            save: 是否立即保存到文件
            
        Returns:
            True if successful, False otherwise
        """
        mp_data = self.get_mp_data(formula)
        if not mp_data:
            print(f"No data found for {formula} in Materials Project")
            return False
        
        # 提取密度和生成焓
        density = mp_data.get('density')
        formation_energy = mp_data.get('formation_energy_per_atom')
        
        # 更新内存中的数据
        if formula not in self._compounds_data:
            self._compounds_data[formula] = {}
        
        if density is not None:
            self._compounds_data[formula]['density'] = density
        
        # 注意：MP的formation_energy单位是eV/atom，需要转换
        if formation_energy is not None:
            # 这里保存原始值，用户可根据需要转换
            self._compounds_data[formula]['enthalpy'] = formation_energy
            self._compounds_data[formula]['enthalpy_unit'] = 'eV/atom'
        
        # 添加来源标记
        self._compounds_data[formula]['source'] = 'Materials Project'
        self._compounds_data[formula]['material_id'] = mp_data.get('material_id')
        
        # 保存到文件
        if save:
            try:
                with open(self._compounds_path, 'w', encoding='utf-8') as f:
                    json.dump(self._compounds_data, f, indent=4, ensure_ascii=False)
                print(f"Successfully updated {formula} in {self._compounds_path}")
                return True
            except Exception as e:
                print(f"Error saving compound data: {e}")
                return False
        
        return True
    
    def search_mp_materials(self, chemsys_formula_id: str) -> List[Dict[str, Any]]:
        """
        在Materials Project中搜索材料
        
        Args:
            chemsys_formula_id: 化学系统、化学式或MP ID (例如: "Fe-C", "Fe2O3", "mp-1234")
            
        Returns:
            材料列表
        """
        mp_client = self._get_mp_client()
        if not mp_client:
            return []
            
        try:
            return mp_client.search_materials(chemsys_formula_id)
        except Exception as e:
            print(f"Error searching Materials Project: {e}")
            return []

# Simple global instance for easy import
db = MaterialDatabase()
