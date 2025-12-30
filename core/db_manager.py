"""
Database Manager (V2 Architecture)
Handles all interactions with the Cermet Database including data entry, retrieval, and feature calculation.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .db_models import Base, Experiment, Composition, Property, CalculatedFeature

# Configure logger
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manager for the HEAC Cermet Database (V2).
    
    Features:
    - Experiment management (CRUD)
    - Automatic Composition Parsing
    - Feature Injection (Physics + Proxy Models)
    - Search and Filtering
    """
    
    def __init__(self, db_path: str = 'cermet_master_v2.db'):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # Lazy loaded helpers
        self.parser = None
        self.physics_calc = None
        self.feature_engine = None
        
        logger.info(f"Database initialized: {db_path}")
    
    def _load_helpers(self):
        """Lazy loads helper modules to avoid circular imports and startup lag."""
        if self.parser is None:
            # Import here to avoid top-level dependencies if possible, or just standard import
            # Assuming these are safe to import now
            try:
                from core.composition_parser_enhanced import EnhancedCompositionParser
                from core.physics_calculator import PhysicsCalculator
                from core.feature_engine import FeatureEngine
                
                self.parser = EnhancedCompositionParser()
                self.physics_calc = PhysicsCalculator()
                self.feature_engine = FeatureEngine()
                logger.info("Helper modules loaded successfully")
            except ImportError as e:
                logger.error(f"Failed to load helper modules: {e}")
                raise

    def create_tables(self):
        """Create all database tables defined in formatting models."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """Drop all tables (Use with caution)."""
        Base.metadata.drop_all(self.engine)
        logger.warning("All tables dropped")
    
    def add_experiment(
        self,
        raw_composition: str,
        source_id: str = 'manual',
        sinter_temp_c: float = None,
        grain_size_um: float = None,
        sinter_method: str = None,
        load_kgf: float = None,
        hv: float = None,
        kic: float = None,
        trs: float = None,
        binder_vol_pct: float = None,
        auto_calculate_features: bool = True
    ) -> int:
        """
        Add a single experiment record to the database.
        
        Args:
            raw_composition: The raw composition string (e.g., "WC-10Co").
            source_id: Identifier for the data source.
            sinter_temp_c: Sintering temperature in Celsius.
            grain_size_um: Grain size in microns.
            sinter_method: Method used for sintering.
            load_kgf: Load used for hardness testing.
            hv: Vickers Hardness.
            kic: Fracture Toughness.
            trs: Transverse Rupture Strength.
            binder_vol_pct: Explicit binder volume percent (optional).
            auto_calculate_features: If True, computes physics/proxy features immediately.
            
        Returns:
            The ID of the newly created experiment.
        """
        self._load_helpers()
        session = self.Session()
        
        try:
            # 1. Parse Composition
            # The parser handles various formats and normalizing
            parse_result = self.parser.parse(raw_composition)
            
            if not parse_result.get('success'):
                raise ValueError(f"Failed to parse composition: {raw_composition} - {parse_result.get('message')}")
            
            # 2. Create Experiment Record
            experiment = Experiment(
                source_id=source_id,
                raw_composition=raw_composition,
                sinter_temp_c=sinter_temp_c,
                grain_size_um=grain_size_um,
                sinter_method=sinter_method,
                load_kgf=load_kgf
            )
            session.add(experiment)
            session.flush()  # Flush to get the ID
            
            # 3. Handle Composition Details
            binder_wt_pct = parse_result.get('binder_wt_pct')
            binder_formula = parse_result['binder_formula']
            ceramic_formula = parse_result['ceramic_formula']
            
            # Calculate Volume % if Weight % is known, or vice versa
            binder_vol = None
            if binder_wt_pct is not None:
                binder_vol = self.physics_calc.wt_to_vol(
                    binder_wt_pct=binder_wt_pct,
                    binder_formula=binder_formula,
                    ceramic_formula=ceramic_formula
                )
            elif binder_vol_pct is not None:
                # If Vol% provided, back-calculate Wt%
                binder_wt_pct = self.physics_calc.vol_to_wt(
                    binder_vol_pct=binder_vol_pct,
                    binder_formula=binder_formula,
                    ceramic_formula=ceramic_formula
                )
                binder_vol = binder_vol_pct
            
            # Determine if it's HEA (High Entropy Alloy)
            from core.db_config import is_hea_binder
            is_hea_flag = is_hea_binder(raw_composition)
            
            # Count elements in binder
            element_count = len(parse_result.get('binder_elements', {}))
            
            composition = Composition(
                exp_id=experiment.id,
                binder_formula=binder_formula,
                binder_wt_pct=binder_wt_pct,
                binder_vol_pct=binder_vol,
                ceramic_formula=ceramic_formula,
                secondary_phase=parse_result.get('secondary_phase'),
                ceramic_wt_pct=100 - binder_wt_pct if binder_wt_pct is not None else None,
                is_hea=is_hea_flag,
                element_count=element_count
            )
            session.add(composition)
            
            # 4. create properties record
            prop = Property(
                exp_id=experiment.id,
                hv=hv,
                kic=kic,
                trs=trs
            )
            session.add(prop)
            
            # 5. Calculate Features (Optional)
            if auto_calculate_features:
                try:
                    features_dict = self.feature_engine.calculate_features(
                        binder_formula=binder_formula,
                        ceramic_formula=ceramic_formula,
                        binder_wt_pct=binder_wt_pct,
                        use_matminer=False  # Default to false for speed
                    )
                    
                    proxy_feat = features_dict.get('proxy_features', {})
                    physics_feat = features_dict.get('physics_features', {})
                    matminer_feat = features_dict.get('matminer_features', {})
                    full_matminer = features_dict.get('full_matminer_features', {})
                    
                    feature = CalculatedFeature(
                        exp_id=experiment.id,
                        # Proxy
                        pred_formation_energy=proxy_feat.get('pred_formation_energy'),
                        pred_lattice_param=proxy_feat.get('pred_lattice_param'),
                        pred_magnetic_moment=proxy_feat.get('pred_magnetic_moment'),
                        pred_bulk_modulus=proxy_feat.get('pred_bulk_modulus'),
                        pred_shear_modulus=proxy_feat.get('pred_shear_modulus'),
                        # Physics
                        lattice_mismatch=physics_feat.get('lattice_mismatch'),
                        vec_binder=physics_feat.get('vec_binder'),
                        mean_atomic_radius=physics_feat.get('mean_atomic_radius'),
                        binder_density=physics_feat.get('binder_density'),
                        # Matminer Simplified
                        magpie_mean_atomic_mass=matminer_feat.get('magpie_mean_atomic_mass'),
                        magpie_std_electronegativity=matminer_feat.get('magpie_std_electronegativity'),
                        # Matminer Full
                        ceramic_magpie_features=full_matminer.get('ceramic'),
                        binder_magpie_features=full_matminer.get('binder'),
                        # Metadata
                        has_matminer=features_dict.get('metadata', {}).get('has_matminer', False),
                        has_full_matminer=features_dict.get('metadata', {}).get('has_full_matminer', False)
                    )
                    session.add(feature)
                    
                except Exception as e:
                    logger.warning(f"Feature calculation failed for {raw_composition}: {e}")
                    # Don't fail the whole insert just because features failed
            
            session.commit()
            logger.info(f"Experiment added successfully: ID={experiment.id}")
            return experiment.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add experiment: {e}")
            raise
        finally:
            session.close()

    def get_experiment(self, exp_id: int) -> dict:
        """
        Retrieve full details for an experiment by ID.
        Returns a dictionary suitable for UI or analysis.
        """
        session = self.Session()
        try:
            exp = session.query(Experiment).filter_by(id=exp_id).first()
            if not exp:
                return None
            
            # Construct dictionary
            return {
                'id': exp.id,
                'source_id': exp.source_id,
                'raw_composition': exp.raw_composition,
                'sinter_temp_c': exp.sinter_temp_c,
                'grain_size_um': exp.grain_size_um,
                'composition': {
                    'binder_formula': exp.composition.binder_formula if exp.composition else None,
                    'binder_wt_pct': exp.composition.binder_wt_pct if exp.composition else None,
                    'ceramic_formula': exp.composition.ceramic_formula if exp.composition else None,
                    'is_hea': exp.composition.is_hea if exp.composition else None,
                } if exp.composition else {},
                'properties': {
                    'hv': exp.properties.hv if exp.properties else None,
                    'kic': exp.properties.kic if exp.properties else None,
                    'trs': exp.properties.trs if exp.properties else None,
                } if exp.properties else {},
                'features': {
                    'lattice_mismatch': exp.features.lattice_mismatch if exp.features else None,
                    'vec_binder': exp.features.vec_binder if exp.features else None,
                    'pred_formation_energy': exp.features.pred_formation_energy if exp.features else None
                } if exp.features else {}
            }
        finally:
            session.close()

    def get_statistics(self) -> dict:
        """Get summary statistics of the database."""
        session = self.Session()
        try:
            total_exp = session.query(Experiment).count()
            hea_count = session.query(Composition).filter_by(is_hea=True).count()
            trad_count = session.query(Composition).filter_by(is_hea=False).count()
            
            return {
                'total_experiments': total_exp,
                'hea_count': hea_count,
                'traditional_count': trad_count
            }
        finally:
            session.close()

# Alias for backward compatibility or simple usage
CermetDB = DatabaseManager
