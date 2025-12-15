"""
HEAC Core Module
提供高熵合金和金属陶瓷的计算、分析和数据管理功能
"""

# === 核心计算器 ===
from .hea_calculator import HEACalculator, hea_calc
from .hea_cermet import MaterialProcessor

# === 数据库和数据管理 ===
from .material_database import MaterialDatabase, db
from .dataset_manager import DatasetManager

# === 数据处理和分析 ===
try:
    from .data_processor import DataProcessor
    from .analysis import Analyzer
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False
    DataProcessor = None
    Analyzer = None

# === 机器学习模型 ===
try:
    from .models import ModelFactory, ModelTrainer
    from .optimization import Optimizer
    _HAS_ML = True
except ImportError:
    _HAS_ML = False
    ModelFactory = None
    ModelTrainer = None
    Optimizer = None

# === 模型管理 ===
from .model_manager import ModelManager

# === 配置和工具 ===
from .config import Config, config
from .localization import get_text

# === Streamlit相关（可选）===
try:
    from .activity_logger import ActivityLogger
    from .session import initialize_session_state
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False
    ActivityLogger = None
    initialize_session_state = None

# === Materials Project客户端 ===
try:
    from .materials_project_client import MaterialsProjectClient
    _HAS_MP_API = True
except ImportError:
    _HAS_MP_API = False
    MaterialsProjectClient = None

# === 其他工具 ===
try:
    from .converter import FormatConverter
    _HAS_CONVERTER = True
except ImportError:
    _HAS_CONVERTER = False
    FormatConverter = None

__all__ = [
    # 计算器
    'HEACalculator',
    'hea_calc',
    'MaterialProcessor',
    
    # 数据库
    'MaterialDatabase',
    'db',
    'DatasetManager',
    
    # 数据处理和分析
    'DataProcessor',
    'Analyzer',
    
    # 机器学习
    'ModelFactory',
    'ModelTrainer',
    'Optimizer',
    'ModelManager',
    
    # 工具
    'Config',
    'config',
    'get_text',
    'ActivityLogger',
    'initialize_session_state',
    'FormatConverter',
    
    # Materials Project
    'MaterialsProjectClient',
    
    # 特性标志
    '_HAS_SKLEARN',
    '_HAS_ML',
    '_HAS_MP_API',
    '_HAS_CONVERTER',
    '_HAS_STREAMLIT',
]

__version__ = '0.2.0'

