from django.db import models
from django.conf import settings


class AuthType(models.TextChoices):
    """认证方式"""
    PASSWORD = 'password', '用户名密码'
    SSH = 'ssh', 'SSH Key'


class Repository(models.Model):
    """
    Git仓库配置表
    """
    name = models.CharField(max_length=100, verbose_name='仓库名称')
    git_url = models.URLField(verbose_name='Git仓库地址')
    auth_type = models.CharField(
        max_length=20,
        choices=AuthType.choices,
        default=AuthType.PASSWORD,
        verbose_name='认证方式'
    )
    username = models.CharField(max_length=100, blank=True, verbose_name='用户名')
    password_encrypted = models.CharField(max_length=500, blank=True, verbose_name='密码（加密）')
    ssh_key_encrypted = models.TextField(blank=True, verbose_name='SSH Key（加密）')
    local_path = models.CharField(max_length=500, verbose_name='本地克隆路径')
    
    # 钉钉配置
    dingtalk_webhook = models.URLField(blank=True, verbose_name='钉钉Webhook')
    dingtalk_secret = models.CharField(max_length=200, blank=True, verbose_name='钉钉Secret')
    
    # 评审配置
    high_risk_threshold = models.FloatField(default=0.70, verbose_name='高风险阈值')
    medium_risk_threshold = models.FloatField(default=0.40, verbose_name='中风险阈值')
    review_branch = models.CharField(
        max_length=100,
        default='master',
        verbose_name='评审分支',
        help_text='指定要评审的分支,设置为"all"则评审所有分支'
    )
    review_all_branches = models.BooleanField(
        default=False,
        verbose_name='评审所有分支',
        help_text='是否评审所有分支的提交'
    )

    # 代码评审触发模式配置
    enable_manual_review = models.BooleanField(
        default=True,
        verbose_name='启用手动触发',
        help_text='允许用户手动触发代码评审'
    )
    enable_scheduled_review = models.BooleanField(
        default=False,
        verbose_name='启用定时评审',
        help_text='按照定时规则自动触发代码评审'
    )
    scheduled_review_cron = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='定时评审Cron表达式',
        help_text='例如: 0 12 * * * 表示每天中午12点'
    )
    enable_realtime_monitor = models.BooleanField(
        default=False,
        verbose_name='启用实时监控',
        help_text='实时监控代码提交，发现新提交立即触发评审'
    )
    realtime_monitor_interval = models.IntegerField(
        default=60,
        verbose_name='实时监控间隔（秒）',
        help_text='检查新提交的间隔时间，默认60秒'
    )
    realtime_monitor_branches = models.JSONField(
        default=list,
        verbose_name='实时监控分支',
        help_text='要监控的分支列表，例如: ["master", "develop"]'
    )
    auto_review_on_new_commit = models.BooleanField(
        default=True,
        verbose_name='新提交自动评审',
        help_text='实时监控发现新提交时自动触发评审'
    )
    notify_on_review_complete = models.BooleanField(
        default=True,
        verbose_name='评审完成通知',
        help_text='评审完成后发送钉钉通知'
    )
    notify_risk_threshold = models.CharField(
        max_length=20,
        default='MEDIUM',
        verbose_name='通知风险阈值',
        help_text='风险等级达到此级别时才发送通知: HIGH/MEDIUM/LOW'
    )
    
    # 关键文件规则
    critical_patterns = models.JSONField(
        default=list,
        verbose_name='关键文件规则',
        help_text='[{"pattern": "**/Controller.java", "level": "critical"}]'
    )
    ignore_patterns = models.JSONField(
        default=list,
        verbose_name='忽略规则',
        help_text='[{"pattern": "**/*.md", "type": "ignore"}]'
    )
    
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
        db_table = 'repository'
        verbose_name = 'Git仓库'
        verbose_name_plural = '仓库管理'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def clone_status(self):
        """获取克隆状态"""
        from pathlib import Path
        return Path(self.local_path).exists()
