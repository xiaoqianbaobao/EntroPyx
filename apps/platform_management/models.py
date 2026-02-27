from django.db import models

class LLMConfig(models.Model):
    """大模型配置"""
    name = models.CharField(max_length=100, default='default', verbose_name='配置名称')
    api_base = models.CharField(max_length=255, verbose_name='API地址', default='https://api.deepseek.com/v1')
    api_key = models.CharField(max_length=255, verbose_name='API密钥')
    model_name = models.CharField(max_length=100, verbose_name='模型名称', default='deepseek-chat')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '大模型配置'
        verbose_name_plural = '大模型配置'
        db_table = 'platform_llm_config'

    def __str__(self):
        return f"{self.name} ({self.model_name})"

