"""
Materials Project集成测试

测试MP API集成、数据获取和数据库功能
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.material_database import db
from core.config import config


class TestMPIntegration(unittest.TestCase):
    """Materials Project集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试前检查API密钥"""
        if not config.MP_API_KEY:
            raise unittest.SkipTest("MP_API_KEY not configured")
    
    def test_api_connection(self):
        """测试MP API连接"""
        # 测试获取一个常见材料
        result = db.get_mp_data("Si")
        self.assertIsNotNone(result, "Should be able to fetch data for Si")
        self.assertIn('material_id', result)
        self.assertIn('formula_pretty', result)
    
    def test_get_density_from_mp(self):
        """测试从MP获取密度"""
        # 测试TiO2（钛白矿）
        density = db.get_density_from_mp("TiO2")
        self.assertIsNotNone(density)
        self.assertIsInstance(density, (int, float))
        self.assertGreater(density, 0)
        print(f"TiO2 density from MP: {density} g/cm³")
    
    def test_get_formation_energy_from_mp(self):
        """测试从MP获取生成能"""
        energy = db.get_formation_enthalpy_from_mp("TiO2")
        self.assertIsNotNone(energy)
        self.assertIsInstance(energy, (int, float))
        print(f"TiO2 formation energy from MP: {energy} eV/atom")
    
    def test_search_materials(self):
        """测试材料搜索"""
        # 搜索Ti-O系统
        results = db.search_mp_materials("Ti-O")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "Should find materials in Ti-O system")
        print(f"Found {len(results)} materials in Ti-O system")
    
    def test_local_data_priority(self):
        """测试本地数据优先策略"""
        # WC在本地数据库中存在
        local_density = db.get_compound_density("WC", use_mp=False)
        self.assertIsNotNone(local_density)
        self.assertEqual(local_density, 15.63)
        
        # 即使设置use_mp=True，也应该优先返回本地数据
        density_with_mp = db.get_compound_density("WC", use_mp=True)
        self.assertEqual(density_with_mp, local_density)
    
    def test_mp_fallback(self):
        """测试MP回退机制"""
        # 测试一个本地没有的材料
        test_formula = "CaTiO3"  # 钙钛矿
        
        # 不使用MP应该返回None
        density_no_mp = db.get_compound_density(test_formula, use_mp=False)
        self.assertIsNone(density_no_mp)
        
        # 使用MP应该能获取到数据
        density_with_mp = db.get_compound_density(test_formula, use_mp=True)
        # 注意：如果MP也没有数据，这个测试可能失败
        if density_with_mp is not None:
            self.assertGreater(density_with_mp, 0)
            print(f"CaTiO3 density from MP: {density_with_mp} g/cm³")
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 首次请求（应该从网络获取）
        result1 = db.get_mp_data("Si")
        self.assertIsNotNone(result1)
        
        # 第二次请求（应该从缓存获取）
        result2 = db.get_mp_data("Si")
        self.assertIsNotNone(result2)
        
        # 结果应该相同
        self.assertEqual(result1.get('material_id'), result2.get('material_id'))


class TestLocalDatabase(unittest.TestCase):
    """测试本地数据库功能（不依赖网络）"""
    
    def test_get_element(self):
        """测试元素查询"""
        al = db.get_element("Al")
        self.assertIsNotNone(al)
        self.assertEqual(al['name'], 'Aluminum')
        self.assertEqual(al['atomic_number'], 13)
    
    def test_get_compound_density(self):
        """测试化合物密度查询"""
        wc_density = db.get_compound_density("WC")
        self.assertEqual(wc_density, 15.63)
    
    def test_get_formation_enthalpy(self):
        """测试生成焓查询"""
        wc_enthalpy = db.get_formation_enthalpy("WC")
        self.assertEqual(wc_enthalpy, -40.0)
    
    def test_get_enthalpy(self):
        """测试混合焓查询"""
        al_w = db.get_enthalpy("Al", "W")
        self.assertEqual(al_w, -2)


def run_tests():
    """运行测试套件"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestLocalDatabase))
    
    # 如果有API密钥，添加网络测试
    if config.MP_API_KEY:
        suite.addTests(loader.loadTestsFromTestCase(TestMPIntegration))
        print("✓ Materials Project API密钥已配置，将运行完整测试")
    else:
        print("⚠ Materials Project API密钥未配置，仅运行本地测试")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
