"""
AI智能评审平台 - 测试框架配置

Author: 测试团队
Version: 1.0
"""
import os
import sys
import django
from pathlib import Path

# 添加项目根目录到Python路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# 配置Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 初始化Django
django.setup()

# pytest配置
pytest_plugins = [
    'pytest_django',
]

# pytest-asyncio配置
import pytest_asyncio

# 默认测试配置
def pytest_configure(config):
    """pytest配置"""
    # 设置测试数据库
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # 创建测试数据库（如果需要）
    from django.core.management import call_command
    from django.conf import settings
    
    # 使用SQLite进行测试以提高速度
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


def pytest_collection_modifyitems(items):
    """修改测试用例收集"""
    # 按优先级排序测试用例
    priority_order = {
        'P0': 0,
        'P1': 1,
        'P2': 2,
    }
    
    for item in items:
        # 添加优先级标记
        if hasattr(item, 'obj') and hasattr(item.obj, 'pytestmark'):
            for mark in item.obj.pytestmark:
                if mark.name in priority_order:
                    item.add_marker(pytest.mark.priority(mark.name))
                    break


# 测试标记
def pytest_configure(config):
    """配置测试标记"""
    config.addinivalue_line(
        "markers", "P0: 核心功能测试"
    )
    config.addinivalue_line(
        "markers", "P1: 重要功能测试"
    )
    config.addinivalue_line(
        "markers", "P2: 一般功能测试"
    )
    config.addinivalue_line(
        "markers", "api: API接口测试"
    )
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试"
    )
    config.addinivalue_line(
        "markers", "security: 安全测试"
    )
