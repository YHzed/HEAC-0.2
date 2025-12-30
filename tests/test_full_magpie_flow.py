
import sys
import os
import unittest
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.feature_engine import FeatureEngine
from core.db_models_v2 import CermetDatabaseV2, Experiment, CalculatedFeature, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestFullMagpieFlow(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Create a test database
        cls.test_db_path = 'test_magpie.db'
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
            
        cls.db = CermetDatabaseV2(cls.test_db_path)
        cls.engine = cls.db.engine
        cls.Session = cls.db.Session
        
        # Ensure tables are created
        Base.metadata.create_all(cls.engine)
        
        cls.fe = FeatureEngine()
        
    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except:
                pass

    def test_1_calculate_features(self):
        """Test calculation of full features"""
        print("\nTesting Feature Calculation...")
        
        features = self.fe.calculate_features(
            binder_formula="Co",
            ceramic_formula="WC",
            use_matminer=True
        )
        
        self.assertIn('full_matminer_features', features)
        self.assertIn('ceramic', features['full_matminer_features'])
        self.assertIn('binder', features['full_matminer_features'])
        
        ceramic_feat = features['full_matminer_features']['ceramic']
        binder_feat = features['full_matminer_features']['binder']
        
        print(f"Ceramic features count: {len(ceramic_feat)}")
        print(f"Binder features count: {len(binder_feat)}")
        
        # Check for specific Magpie feature
        self.assertTrue(any('MagpieData mean AtomicWeight' in k for k in ceramic_feat.keys()))
        self.assertGreater(len(ceramic_feat), 100)

    def test_2_save_and_query(self):
        """Test saving to DB and querying JSON fields"""
        print("\nTesting DB Save and Query...")
        session = self.Session()
        
        # Create dummy experiment
        exp = Experiment(
            source_id='TEST-001',
            raw_composition='WC-10Co'
        )
        session.add(exp)
        session.commit()
        
        # Calculate features
        features = self.fe.calculate_features(
            binder_formula="Co",
            ceramic_formula="WC",
            use_matminer=True
        )
        
        full_matminer = features.get('full_matminer_features', {})
        
        # Manually create CalculatedFeature (simulating Add Data logic)
        cf = CalculatedFeature(
            exp_id=exp.id,
            ceramic_magpie_features=full_matminer.get('ceramic'),
            binder_magpie_features=full_matminer.get('binder'),
            has_full_matminer=True,
            has_matminer=True
        )
        session.add(cf)
        session.commit()
        
        # Query back
        q_cf = session.query(CalculatedFeature).filter_by(exp_id=exp.id).first()
        
        self.assertIsNotNone(q_cf.ceramic_magpie_features)
        self.assertIsNotNone(q_cf.binder_magpie_features)
        
        # Verify JSON content
        c_feat = q_cf.ceramic_magpie_features
        print(f"Retrieved Ceramic features type: {type(c_feat)}")
        print(f"Retrieved Ceramic features keys: {list(c_feat.keys())[:3]}") # Show first 3
        
        self.assertTrue(isinstance(c_feat, dict))
        self.assertGreater(len(c_feat), 0)
        
        session.close()

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
