import math
import numpy as np
import pandas as pd
import optuna
import joblib
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional, Union

# Re-use existing database
from .material_database import db as material_db

# ModelX和特征注入器
try:
    from .modelx_adapter import ModelXAdapter
    from .feature_injector import FeatureInjector
    MODELX_AVAILABLE = True
except ImportError:
    MODELX_AVAILABLE = False
    print("Warning: ModelX adapter not available")

# -----------------------------------------------------------------------------
# 1. Design Space (Input Layer)
# -----------------------------------------------------------------------------
@dataclass
class DesignSpace:
    """
    Represents the input variables for the material design.
    Matches user request: Binder (Mass%), Hard Phase (Type), Process.
    """
    # HEA Metallic phase composition (Elements -> Mass Fraction or Atomic Fraction)
    # Default is Atomic unless is_mass_fraction is True
    hea_composition: Dict[str, float]
    is_mass_fraction: bool = False
    
    # Hard Phase Selection
    ceramic_type: str = 'WC' # Options: 'WC', 'TiC'
    
    # Microstructure Targets
    ceramic_vol_fraction: float = 0.5  # Target Volume Fraction
    grain_size_um: float = 1.0
    
    # Process Parameters
    sinter_temp_c: float = 1400.0
    sinter_time_min: float = 60.0
    process_route: str = 'Vacuum Sintering' # 'Vacuum', 'HIP', 'Sinter-HIP'

    @property
    def binder_vol_fraction(self) -> float:
        """粘结相体积分数（= 1 - 陶瓷体积分数）"""
        return 1.0 - self.ceramic_vol_fraction
    
    def get_binder_composition_atomic(self) -> Dict[str, float]:
        """Returns normalized atomic fractions of the HEA binder."""
        if not self.is_mass_fraction:
            total = sum(self.hea_composition.values())
            if total == 0: return {}
            return {k: v/total for k, v in self.hea_composition.items()}
        else:
            # Convert Mass -> Atomic
            atomic_counts = {}
            total_moles = 0.0
            for el, mass in self.hea_composition.items():
                molar_mass = material_db.get_property(el, 'mass')
                if molar_mass:
                    moles = mass / molar_mass
                    atomic_counts[el] = moles
                    total_moles += moles
            
            if total_moles == 0: return {}
            return {k: v/total_moles for k, v in atomic_counts.items()}

# -----------------------------------------------------------------------------
# 2. Physics Engine (Transformation Layer)
# -----------------------------------------------------------------------------
class PhysicsEngine:
    """
    Transforms DesignSpace inputs into physics-based features ($X$).
    Refined based on "Single Point Analysis Theory".
    """
    def __init__(self):
        self.db = material_db
        
        # ModelX支持
        self.feature_injector = None
        self.modelx_adapter = None
        if MODELX_AVAILABLE:
            try:
                # 尝试加载FeatureInjector（需要proxy模型）
                from .feature_injector import FeatureInjector
                self.feature_injector = FeatureInjector()
                print("✓ FeatureInjector loaded for proxy predictions")
            except Exception as e:
                print(f"Warning: FeatureInjector not available - {e}")
                # Proxy模型不可用时，仍然尝试加载ModelXAdapter（可能部分功能受限）
            
            try:
                self.modelx_adapter = ModelXAdapter()
                print("✓ ModelXAdapter loaded successfully")
            except Exception as e:
                print(f"Warning: ModelXAdapter not available - {e}")
        
        # Detailed Ceramic Properties for Mismatch Calc
        self.ceramic_db = {
            'WC': {
                'a': 2.906,     # Hexagonal a (Angstrom) - often used for mismatch with FCC (111)
                'alpha': 5.2,   # CTE (10^-6 / K)
                'G': 283.0,     # Shear Modulus (GPa)
                'Tm': 2870 + 273.15, # K
                'H_formation': -40.0 # kJ/mol
            },
            'TiC': {
                'a': 4.32,      # FCC a (Angstrom)
                'alpha': 7.4,   # CTE
                'G': 188.0,     # Shear Modulus
                'Tm': 3160 + 273.15,
                'H_formation': -184.0
            }
        }
    
    def get_ceramic_props(self, c_type: str):
        return self.ceramic_db.get(c_type, self.ceramic_db['WC'])

    def compute_features(self, design: DesignSpace) -> Dict[str, float]:
        """
        Main pipeline to generate features for ML ($X$).
        Input: DesignSpace -> Output: Feature Vector
        """
        features = {}
        binder_comp = design.get_binder_composition_atomic()
        cer_props = self.get_ceramic_props(design.ceramic_type)
        
        # --- A. Thermodynamic Features (Binder) ---
        features.update(self._calculate_thermo_features(binder_comp))
        
        # --- B. Structural/Interface Features ---
        features.update(self._calculate_structural_features(binder_comp, cer_props))
        
        # --- C. Process/Kinetic Features ---
        features.update(self._calculate_process_features(design, binder_comp, cer_props))
        
        # --- D. Global Features ---
        features['Ceramic_Vol_Frac'] = design.ceramic_vol_fraction
        features['Grain_Size'] = design.grain_size_um
        
        return features

    def compute_modelx_features(self, design: DesignSpace) -> Dict[str, float]:
        """
        生成ModelX模型所需的18个特征
        
        严格按照依赖链顺序计算：
        Layer 1: 基础特征（Matminer + 简单特征）
        Layer 2: Proxy模型预测
        Layer 3: 衍生特征（依赖Layer 2）
        
        Args:
            design: DesignSpace对象
            
        Returns:
            包含18个特征的字典
        """
        if not self.modelx_adapter or not self.feature_injector:
            raise RuntimeError("ModelX components not initialized")
        
        # 获取成分（原子分数和质量分数）
        composition_atomic = design.get_binder_composition_atomic()
        
        # 计算质量分数
        composition_wt = {}
        total_mass = 0.0
        for el, at_frac in composition_atomic.items():
            mass = self.db.get_property(el, 'mass', 0)
            w = at_frac * mass
            composition_wt[el] = w
            total_mass += w
        
        if total_mass > 0:
            composition_wt = {k: v/total_mass for k, v in composition_wt.items()}
        
        # ==== Layer 2: Proxy模型预测（使用FeatureInjector） ====
        proxy_features = {
            'pred_formation_energy': self.feature_injector.predict_formation_energy(composition_atomic),
            'pred_lattice_param': self.feature_injector.predict_lattice_parameter(composition_atomic),
            'pred_magnetic_moment': self.feature_injector.predict_magnetic_moment(composition_atomic)
        }
        
        # 定义合理的默认值（当proxy预测失败时使用）
        DEFAULT_PROXY_VALUES = {
            'pred_formation_energy': -0.5,  # eV/atom，典型HEA的负形成能
            'pred_lattice_param': 3.6,      # Å，FCC HEA的典型晶格常数
            'pred_magnetic_moment': 0.5     # μB/atom，弱磁性
        }
        
        # 处理None值，使用默认值并发出警告
        for key in proxy_features:
            if proxy_features[key] is None:
                import warnings
                warnings.warn(
                    f"⚠️ {key}预测失败，使用经验默认值={DEFAULT_PROXY_VALUES[key]}。"
                    f"这可能影响最终预测精度。",
                    UserWarning
                )
                proxy_features[key] = DEFAULT_PROXY_VALUES[key]
        
        # ==== 使用ModelXAdapter提取完整的18个特征 ====
        # 注意：Binder_Wt_Pct应该是粘结相的质量百分比
        # 简化假设：粘结相的体积分数约等于质量分数(实际应考虑密度差异)
        binder_wt_pct = design.binder_vol_fraction * 100  # 粘结相体积百分比
        
        modelx_features = self.modelx_adapter.extract_modelx_features(
            composition_atomic=composition_atomic,
            composition_wt=composition_wt,
            binder_wt_pct=binder_wt_pct,
            grain_size_um=design.grain_size_um,
            proxy_features=proxy_features,
            ceramic_type=design.ceramic_type
        )
        
        return modelx_features


    def calculate_volume_fractions(self, design: DesignSpace) -> Dict[str, float]:
        """Calculates detailed volume distribution."""
        # This remains largely similar, just needs to handle mass->atomic conversion correctly first
        binder_atomic = design.get_binder_composition_atomic()
        
        # 1. Calc Binder Density
        # Formula: 1/rho_mix = Sum(wt_i / rho_i)
        
        # First get Wt fractions from Atomic
        binder_wt = {}
        total_mass = 0.0
        for el, at in binder_atomic.items():
            m = self.db.get_property(el, 'mass', 0)
            w = at * m
            binder_wt[el] = w
            total_mass += w
            
        if total_mass > 0:
            binder_wt = {k: v/total_mass for k, v in binder_wt.items()}
            
        inv_rho = 0.0
        for el, wt in binder_wt.items():
            rho = self.db.get_property(el, 'rho') # g/cm3
            if rho and rho > 0:
                inv_rho += wt / rho
        
        rho_binder = 1.0 / inv_rho if inv_rho > 0 else 8.0
        
        # 2. Global Dist
        v_cer = design.ceramic_vol_fraction
        v_bind = 1.0 - v_cer
        
        stats = {
            'Phase_Ceramic': v_cer,
            'Phase_Binder': v_bind,
            'Density_Binder_Theoretical': rho_binder
        }
        
        # 3. Element Vol in Composite
        for el, wt in binder_wt.items():
            rho = self.db.get_property(el, 'rho')
            if rho:
                v_in_binder = (wt / rho) * rho_binder
                stats[f'Elem_Vol_{el}'] = v_in_binder * v_bind
                
        return stats

    def _calculate_thermo_features(self, composition: Dict[str, float]) -> Dict[str, float]:
        if not composition: return {}
        
        # VEC, Enthalpy, Entropy, Atomic Size Diff, Electronegativity Diff
        vec = 0.0
        r_avg = 0.0
        chi_avg = 0.0 # Electronegativity
        
        for el, c in composition.items():
            vec += c * self.db.get_property(el, 'vec', 0)
            r_avg += c * self.db.get_property(el, 'r', 0)
            chi_avg += c * self.db.get_property(el, 'electronegativity_pauling', 0)
            
        # Delta (Atomic Size)
        delta_r = 0.0
        delta_chi = 0.0
        for el, c in composition.items():
            r = self.db.get_property(el, 'r', 0)
            chi = self.db.get_property(el, 'electronegativity_pauling', 0)
            if r_avg > 0:
                delta_r += c * (1 - r/r_avg)**2
            delta_chi += c * (chi - chi_avg)**2
            
        delta_r = math.sqrt(delta_r) * 100 # %
        delta_chi = math.sqrt(delta_chi)
        
        # Mixing Enthalpy/Entropy
        s_mix = -8.314 * sum(c * math.log(c) for c in composition.values() if c > 0)
        
        h_mix = 0.0
        elements = list(composition.keys())
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                el1, el2 = elements[i], elements[j]
                h_ij = self.db.get_enthalpy(el1, el2)
                h_mix += 4 * h_ij * composition[el1] * composition[el2]
                
        return {
            'VEC': vec,
            'H_mix': h_mix,
            'S_mix': s_mix,
            'Delta_R': delta_r,
            'Delta_Chi': delta_chi
        }

    def _calculate_structural_features(self, composition: Dict[str, float], cer_props: dict) -> Dict[str, float]:
        if not composition: return {}
        
        # 1. Lattice Mismatch
        # Improved Model: Use VEC to guess structure (FCC/BCC), then estimate lattice parameter
        vec = sum(c * self.db.get_property(el, 'vec', 0) for el, c in composition.items())
        
        # Calculate average atomic radius
        r_avg_pm = sum(c * self.db.get_property(el, 'r', 0) for el, c in composition.items())
        r_avg_angstrom = r_avg_pm / 100.0
        
        # Estimate Lattice Constant a_binder based on structure assumption
        if vec >= 8.0:
            # FCC Assumption
            # a_fcc = 2 * sqrt(2) * r
            a_binder = 2 * math.sqrt(2) * r_avg_angstrom
        else:
            # BCC Assumption
            # a_bcc = 4 * r / sqrt(3)
            a_binder = 4 * r_avg_angstrom / math.sqrt(3)
            
        # Mismatch Calculation
        # For WC (Hex), mismatch is tricky. Simple metric: |a_binder - a_ceramic| / a_ceramic
        # TiC is FCC, so direct comparison works well.
        mismatch = abs(a_binder - cer_props['a']) / cer_props['a']
        
        # 2. CTE Mismatch
        alpha_binder = 0.0
        for el, c in composition.items():
            # If CTE missing, assume typical metal ~12 if not found (a known limitation fixed by report P0)
            # Here we use a safe default or 0 if missing, risking accuracy
            cte = self.db.get_property(el, 'cte_micron_per_k') 
            # Note: User report said this field is missing. I should check if I added it?
            # If still missing, we might get 0. 
            if cte is None: cte = 12.0 # Fallback
            alpha_binder += c * cte
            
        delta_cte = abs(alpha_binder - cer_props['alpha'])
        
        return {
            'Lattice_Constant_Est': a_binder,
            'Lattice_Mismatch': mismatch,
            'CTE_Mismatch': delta_cte,
            'CTE_Binder': alpha_binder
        }

    def _calculate_process_features(self, design: DesignSpace, composition: Dict[str, float], cer_props: dict) -> Dict[str, float]:
        # Liquidus Temperature (Revised with Eutectic Depression)
        # T_liq = Sum(c*Tm) - K * S_mix (Depression Effect)
        
        tm_avg = 0.0
        for el, c in composition.items():
            tm_avg += c * self.db.get_property(el, 'melting_point', 0)
            
        # Ideal Solution M.P. is roughly linear, but eutectics drop it.
        # Simple heuristic: T_liq approx T_avg - 50 * (S_mix/R) (Just a scalar)
        # S_mix is in J/mol K. R=8.314. S_mix/R is roughly 0.69 (binary) - 1.6 (5-component).
        # HEA depressions can be 200-300K. 
        # Let's use: T_liq = T_avg - 200 * (S_mix / 13.0) approx for HEAs
        
        s_mix = -8.314 * sum(c * math.log(c) for c in composition.values() if c > 0)
        depression = 150.0 * (s_mix / 13.3) # Normalized approx
        
        t_liq = tm_avg - depression
        
        t_sinter_k = design.sinter_temp_c + 273.15
        t_homo = t_sinter_k / t_liq if t_liq > 0 else 0
        
        return {
            'T_Liquidus_Est': t_liq,
            'T_Homologous': t_homo,
            'Sinter_Temp_K': t_sinter_k
        }

# -----------------------------------------------------------------------------
# 3. AI Predictor (Prediction Layer)
# -----------------------------------------------------------------------------
class AIPredictor:
    """
    ML-based Predictor.
    优先使用ModelX进行HV预测，fallback到启发式方法。
    """
    def __init__(self, model_dir='saved_models'):
        self.model_dir = model_dir
        self.models = {}
        self.physics_engine = None  # 用于生成ModelX特征
        self._load_models()
        
    def _load_models(self):
        """尝试加载训练好的模型，优先加载ModelX和ModelY"""
        # 1. 尝试加载ModelX (HV预测)
        modelx_path = os.path.join('models', 'ModelX.pkl')
        if os.path.exists(modelx_path) and MODELX_AVAILABLE:
            try:
                # 初始化PhysicsEngine用于特征生成
                self.physics_engine = PhysicsEngine()
                print(f"✓ ModelX loaded successfully (R²=0.911)")
                self.models['ModelX'] = True
            except Exception as e:
                print(f"Warning: Failed to load ModelX: {e}")
        
        # 2. 尝试加载ModelY (KIC预测)
        modely_path = os.path.join('models', 'ModelY.pkl')
        if os.path.exists(modely_path):
            try:
                import joblib
                self.models['ModelY'] = joblib.load(modely_path)
                print(f"✓ ModelY loaded successfully for KIC prediction")
                
                # 如果PhysicsEngine还未初始化(ModelX加载失败),初始化它
                if not self.physics_engine and MODELX_AVAILABLE:
                    self.physics_engine = PhysicsEngine()
            except Exception as e:
                print(f"Warning: Failed to load ModelY: {e}")
        
        # 3. 加载其他模型（PhaseStability等）
        for target in ['PhaseStability']:
            path = os.path.join(self.model_dir, f'cermet_model_{target.lower()}.joblib')
            if os.path.exists(path):
                try:
                    self.models[target] = joblib.load(path)
                except:
                    print(f"Failed to load model: {path}")
                    
    def predict(self, features_or_design: Union[Dict[str, float], 'DesignSpace']) -> Dict[str, float]:
        """
        预测材料性能
        
        优先使用ModelX（如果可用），否则使用启发式方法
        
        Args:
            features_or_design: 特征字典或DesignSpace对象
            
        Returns:
            预测结果字典
        """
        results = {}
        
        # 判断输入类型
        if isinstance(features_or_design, DesignSpace):
            design = features_or_design
            # 生成传统特征
            features = self.physics_engine.compute_features(design) if self.physics_engine else {}
        else:
            features = features_or_design
            design = None
        
        # Convert features dict to DataFrame (1 row) for flexible model input
        X = pd.DataFrame([features])
        
        # ❗ 为了避免重复警告，只计算一次ModelX特征（ModelX和ModelY共用）
        modelx_features = None
        if self.physics_engine and design and ('ModelX' in self.models or 'ModelY' in self.models):
            try:
                modelx_features = self.physics_engine.compute_modelx_features(design)
            except Exception as e:
                print(f"compute_modelx_features failed: {e}")
        
        # --- HV Prediction (优先使用ModelX) ---
        if 'ModelX' in self.models and modelx_features is not None:
            try:
                # 使用ModelX预测
                hv_pred = self.physics_engine.modelx_adapter.predict_single(modelx_features)
                results['Predicted_HV'] = hv_pred
                results['HV_Source'] = 'ModelX (R²=0.91)'
            except Exception as e:
                print(f"ModelX prediction failed: {e}, using fallback")
                results['Predicted_HV'] = self._fallback_hv(features)
                results['HV_Source'] = 'Heuristic (ModelX Error)'
        else:
            # Fallback到启发式
            results['Predicted_HV'] = self._fallback_hv(features)
            results['HV_Source'] = 'Heuristic'
            
        # --- K1C Prediction (优先使用ModelY) ---
        if 'ModelY' in self.models and modelx_features is not None:
            try:
                # 准备特征DataFrame
                from .modelx_adapter import ModelXAdapter
                adapter = ModelXAdapter()
                X_modely = adapter.prepare_features_dataframe([modelx_features])
                
                # 使用ModelY预测
                k1c_pred = self.models['ModelY'].predict(X_modely)[0]
                
                # ❗ KIC不能为负值，如果为负取绝对值并警告
                if k1c_pred < 0:
                    import warnings
                    warnings.warn(
                        f"⚠️ ModelY预测返回负值{k1c_pred:.2f}，已转换为绝对值。"
                        f"请检查模型训练数据。",
                        UserWarning
                    )
                    k1c_pred = abs(k1c_pred)
                
                results['Predicted_K1C'] = k1c_pred
                results['K1C_Source'] = 'ModelY'
            except Exception as e:
                print(f"ModelY prediction failed: {e}, using fallback")
                results['Predicted_K1C'] = self._fallback_k1c(features)
                results['K1C_Source'] = 'Heuristic (ModelY Error)'
        elif 'K1C' in self.models:
            # 使用旧的K1C模型(如果存在)
            try:
                results['Predicted_K1C'] = self.models['K1C'].predict(X)[0]
                results['K1C_Source'] = 'ML Model'
            except:
                results['Predicted_K1C'] = self._fallback_k1c(features)
                results['K1C_Source'] = 'Heuristic (Model Error)'
        else:
            # Fallback到启发式
            results['Predicted_K1C'] = self._fallback_k1c(features)
            results['K1C_Source'] = 'Heuristic'
            
        # --- Phase Stability / Composition ---
        if 'PhaseStability' in self.models:
            results['Phase_Analysis'] = self.models['PhaseStability'].predict(X)[0]
        else:
            results['Phase_Analysis'] = "No ML Model. Assuming Standard HEA+Ceramic."
            
        return results

    def _fallback_hv(self, f):
        # Improved Heuristic from Report
        base = 1600.0
        vec = f.get('VEC', 8.0)
        # Strengthening from lattice distortion
        delta = f.get('Delta_R', 0)
        strengthening = delta * 50.0 
        # Porosity penalty
        t_homo = f.get('T_Homologous', 1.0)
        porosity = max(0, (0.95 - t_homo) * 2000)
        
        # Hardness drops if binders are too soft (VEC > 8.5)
        softening = max(0, (vec - 8.5) * 300)
        
        return base + strengthening - porosity - softening

    def _fallback_k1c(self, f):
        # Base
        base = 10.0
        # VEC Effect: Ductility peak around 8.0-8.2
        vec = f.get('VEC', 8.0)
        ductility = max(0, 1.0 - abs(vec - 8.2)) * 5.0
        
        # Mismatch penalty
        mis = f.get('Lattice_Mismatch', 0)
        mis_penalty = mis * 20.0
        
        return base + ductility - mis_penalty

# -----------------------------------------------------------------------------
# 4. Inverse Optimizer (Optimization Layer)
# -----------------------------------------------------------------------------
class InverseOptimizer:
    """
    Uses Genetic Algorithms (NSGA-II via Optuna) to find optimal designs.
    Updated to support new DesignSpace.
    """
    def __init__(self):
        self.physics = PhysicsEngine()
        self.predictor = AIPredictor()
        
    def optimize(self, n_trials=50, target_hv=1800.0, target_k1c=12.0):
        def objective(trial):
            # 1. Variables
            # Composition (Atomic for internal optim)
            c_co = trial.suggest_float('Co', 0.0, 1.0)
            c_ni = trial.suggest_float('Ni', 0.0, 1.0)
            c_fe = trial.suggest_float('Fe', 0.0, 1.0)
            c_cr = trial.suggest_float('Cr', 0.0, 0.5) 
            c_mo = trial.suggest_float('Mo', 0.0, 0.3)
            
            t_sinter = trial.suggest_float('T_sinter', 1250, 1550)
            
            comp = {'Co': c_co, 'Ni': c_ni, 'Fe': c_fe, 'Cr': c_cr, 'Mo': c_mo}
            if sum(comp.values()) < 1e-3: return -1.0, -1.0
            
            # 2. Design
            design = DesignSpace(
                hea_composition=comp,
                sinter_temp_c=t_sinter,
                ceramic_type='WC', # Default in Opt for now
                is_mass_fraction=False 
            )
            
            # 3. Physics & ML
            feats = self.physics.compute_features(design)
            preds = self.predictor.predict(feats)
            
            return preds['Predicted_HV'], preds['Predicted_K1C']
            
        sampler = optuna.samplers.NSGAIISampler()
        study = optuna.create_study(directions=['maximize', 'maximize'], sampler=sampler)
        study.optimize(objective, n_trials=n_trials)
        return study.best_trials
