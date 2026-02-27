from django.db import models
from django.conf import settings


class RuleType(models.TextChoices):
    """规则类型"""
    WHITELIST = 'WHITELIST', '白名单-忽略'
    BLACKLIST = 'BLACKLIST', '黑名单-加强检测'


class FeedbackRule(models.Model):
    """反馈优化规则表"""
    rule_type = models.CharField(
        max_length=20,
        choices=RuleType.choices,
        verbose_name='规则类型'
    )
    pattern = models.TextField(verbose_name='规则模式')
    description = models.TextField(blank=True, verbose_name='规则描述')
    weight = models.FloatField(default=1.0, verbose_name='权重')
    
    # 统计
    feedback_count = models.IntegerField(default=0, verbose_name='反馈次数')
    accuracy_rate = models.FloatField(default=0.0, verbose_name='准确率(%)')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'feedback_rule'
        verbose_name = '反馈规则'
        verbose_name_plural = '反馈规则管理'
        indexes = [
            models.Index(fields=['rule_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_rule_type_display()} - {self.pattern[:50]}"
