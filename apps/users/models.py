from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class UserRole(models.TextChoices):
    """用户角色"""
    PRODUCT_MANAGER = 'pm', '产品经理'
    DEVELOPER = 'developer', '开发工程师'
    TESTER = 'tester', '测试工程师'
    LEADER = 'leader', '团队负责人'
    ADMIN = 'admin', '管理员'


class User(AbstractUser):
    """
    扩展Django内置User模型
    """
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.DEVELOPER,
        verbose_name='角色'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='部门'
    )
    dingtalk_user_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='钉钉用户ID'
    )
    avatar_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='头像URL'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='手机号'
    )
    
    # 统计字段
    total_reviews = models.IntegerField(
        default=0,
        verbose_name='评审次数'
    )
    feedback_count = models.IntegerField(
        default=0,
        verbose_name='反馈次数'
    )
    last_active_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后活跃时间'
    )
    
    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'
    
    def __str__(self):
        return f"{self.username}({self.get_role_display()})"
