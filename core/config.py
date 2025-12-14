"""
配置管理模块
用于加载和管理项目配置，包括 Materials Project API 设置
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """项目配置类"""
    
    # Materials Project API 配置
    MP_API_KEY: Optional[str] = os.getenv('MP_API_KEY')
    MP_CACHE_ENABLED: bool = os.getenv('MP_CACHE_ENABLED', 'true').lower() == 'true'
    MP_CACHE_DIR: str = os.getenv('MP_CACHE_DIR', 'core/data/mp_cache')
    MP_CACHE_TTL_DAYS: int = int(os.getenv('MP_CACHE_TTL_DAYS', '30'))
    MP_RATE_LIMIT: int = int(os.getenv('MP_RATE_LIMIT', '10'))
    
    @classmethod
    def validate(cls) -> bool:
        """
        验证必需的配置项是否存在
        
        Returns:
            bool: 如果所有必需配置都存在则返回 True
        """
        if not cls.MP_API_KEY:
            print("警告: 未设置 MP_API_KEY。请在 .env 文件中配置您的 Materials Project API key。")
            return False
        return True
    
    @classmethod
    def get_cache_path(cls) -> Path:
        """
        获取缓存目录的完整路径
        
        Returns:
            Path: 缓存目录路径
        """
        base_path = Path(__file__).parent.parent
        cache_path = base_path / cls.MP_CACHE_DIR
        
        # 确保缓存目录存在
        if cls.MP_CACHE_ENABLED:
            cache_path.mkdir(parents=True, exist_ok=True)
        
        return cache_path


# 创建全局配置实例
config = Config()
