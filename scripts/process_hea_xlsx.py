#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向后兼容性重定向文件

HEADataProcessor 已移至 core.hea_data_processor 模块。
此文件保留以维持向后兼容性。

新代码请使用:
    from core.hea_data_processor import HEADataProcessor

或:
    from core import HEADataProcessor

作者: HEAC 0.2 项目组
日期: 2025-12-22
"""

import warnings

# 发出弃用警告
warnings.warn(
    "从 scripts.process_hea_xlsx 导入 HEADataProcessor 已弃用。"
    "请改用: from core.hea_data_processor import HEADataProcessor",
    DeprecationWarning,
    stacklevel=2
)

# 从新位置导入
from core.hea_data_processor import HEADataProcessor

__all__ = ['HEADataProcessor']
