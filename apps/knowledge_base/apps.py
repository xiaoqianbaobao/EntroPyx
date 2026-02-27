"""
知识库应用配置
Knowledge Base App Configuration
"""
from django.apps import AppConfig


class KnowledgeBaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.knowledge_base'
    verbose_name = '知识库管理'
    
    def ready(self):
        """应用启动时的初始化"""
        # 确保模型注册
        try:
            from . import models
        except ImportError:
            pass