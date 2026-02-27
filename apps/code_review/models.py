from django.db import models
from django.conf import settings
from django.utils import timezone


class TaskStatus(models.TextChoices):
    """任务状态"""
    PENDING = 'PENDING', '等待中'
    RUNNING = 'RUNNING', '进行中'
    CLONING = 'CLONING', '克隆仓库中'
    FETCHING = 'FETCHING', '获取提交记录中'
    DIFFING = 'DIFFING', '分析代码差异中'
    REVIEWING = 'REVIEWING', 'AI评审中'
    SAVING = 'SAVING', '保存评审结果中'
    NOTIFYING = 'NOTIFYING', '发送钉钉通知中'
    COMPLETED = 'COMPLETED', '已完成'
    FAILED = 'FAILED', '失败'
    CANCELLED = 'CANCELLED', '已取消'


class RiskLevel(models.TextChoices):
    """风险等级"""
    HIGH = 'HIGH', '高风险'
    MEDIUM = 'MEDIUM', '中风险'
    LOW = 'LOW', '低风险'


class FeedbackStatus(models.TextChoices):
    """反馈状态"""
    PENDING = 'PENDING', '待反馈'
    CORRECT = 'CORRECT', '评审准确'
    FALSE_POSITIVE = 'FALSE_POSITIVE', '误报'
    MISSED = 'MISSED', '漏报'


class TriggerMode(models.TextChoices):
    """触发模式"""
    MANUAL = 'MANUAL', '手动触发'
    SCHEDULED = 'SCHEDULED', '定时任务'
    REALTIME = 'REALTIME', '实时监控'
    WEBHOOK = 'WEBHOOK', 'Webhook触发'


class CodeReview(models.Model):
    """代码评审记录表"""
    repository = models.ForeignKey(
        'repository.Repository',
        on_delete=models.CASCADE,
        verbose_name='仓库'
    )
    branch = models.CharField(max_length=100, verbose_name='分支')
    commit_hash = models.CharField(max_length=40, verbose_name='Commit Hash')
    commit_message = models.TextField(blank=True, verbose_name='提交信息')
    author = models.CharField(max_length=100, verbose_name='作者')
    author_email = models.EmailField(blank=True, verbose_name='作者邮箱')
    commit_time = models.DateTimeField(verbose_name='提交时间')
    
    # 触发信息
    trigger_mode = models.CharField(
        max_length=20,
        choices=TriggerMode.choices,
        default=TriggerMode.MANUAL,
        verbose_name='触发模式'
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_reviews',
        verbose_name='触发人'
    )
    
    # 评审结果
    risk_score = models.FloatField(verbose_name='风险评分(0-1)')
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        verbose_name='风险等级'
    )
    ai_review_content = models.TextField(verbose_name='AI评审内容')
    ai_model = models.CharField(
        max_length=50,
        default='deepseek-coder',
        verbose_name='使用的AI模型'
    )
    
    # 文件变更
    changed_files = models.JSONField(verbose_name='变更文件列表')
    diff_content = models.TextField(blank=True, verbose_name='Diff内容')
    
    # 代码行数统计
    lines_added = models.IntegerField(default=0, verbose_name='新增行数')
    lines_deleted = models.IntegerField(default=0, verbose_name='删除行数')
    lines_changed = models.IntegerField(default=0, verbose_name='变更总行数')
    
    # 评审要点
    review_points = models.JSONField(default=list, verbose_name='评审要点')
    
    # 反馈
    feedback_status = models.CharField(
        max_length=20,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.PENDING,
        verbose_name='反馈状态'
    )
    feedback_comment = models.TextField(blank=True, verbose_name='反馈评论')
    feedback_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks',
        verbose_name='反馈人'
    )
    feedback_at = models.DateTimeField(null=True, blank=True, verbose_name='反馈时间')
    
    # 推送状态
    dingtalk_sent = models.BooleanField(default=False, verbose_name='是否已推送钉钉')
    dingtalk_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='钉钉推送时间')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='评审时间')
    
    class Meta:
        db_table = 'code_review'
        verbose_name = '代码评审'
        verbose_name_plural = '代码评审记录'
        unique_together = ['repository', 'commit_hash']
        indexes = [
            models.Index(fields=['repository', 'branch']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['feedback_status']),
            models.Index(fields=['trigger_mode']),
        ]
    
    def __str__(self):
        return f"{self.repository.name} - {self.commit_hash[:8]}"


class ReviewTask(models.Model):
    """评审任务进度追踪表"""
    task_id = models.CharField(max_length=100, unique=True, verbose_name='Celery任务ID')
    repository = models.ForeignKey(
        'repository.Repository',
        on_delete=models.CASCADE,
        verbose_name='仓库'
    )
    branch = models.CharField(max_length=100, verbose_name='分支')
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
        verbose_name='任务状态'
    )
    current_step = models.CharField(max_length=200, blank=True, verbose_name='当前步骤')
    progress = models.IntegerField(default=0, verbose_name='进度百分比')
    total_commits = models.IntegerField(default=0, verbose_name='总提交数')
    processed_commits = models.IntegerField(default=0, verbose_name='已处理提交数')
    
    # 触发信息
    trigger_mode = models.CharField(
        max_length=20,
        choices=TriggerMode.choices,
        default=TriggerMode.MANUAL,
        verbose_name='触发模式'
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='触发人'
    )
    
    # 评审结果
    high_risk_count = models.IntegerField(default=0, verbose_name='高风险提交数')
    medium_risk_count = models.IntegerField(default=0, verbose_name='中风险提交数')
    low_risk_count = models.IntegerField(default=0, verbose_name='低风险提交数')
    dingtalk_notified_count = models.IntegerField(default=0, verbose_name='钉钉通知数')
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 元数据
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'review_task'
        verbose_name = '评审任务'
        verbose_name_plural = '评审任务进度'
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['status']),
            models.Index(fields=['repository']),
            models.Index(fields=['created_at']),
            models.Index(fields=['trigger_mode']),
        ]
    
    def __str__(self):
        return f"{self.repository.name} - {self.task_id[:8]} ({self.status})"
    
    @property
    def is_completed(self):
        """是否完成"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
    
    @property
    def duration(self):
        """任务耗时"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (timezone.now() - self.started_at).total_seconds()
        return 0
    
    def update_progress(self, status: str, current_step: str = '', progress: int = None):
        """更新任务进度"""
        self.status = status
        self.current_step = current_step
        if progress is not None:
            self.progress = progress
        self.save(update_fields=['status', 'current_step', 'progress', 'updated_at'])
    
    def increment_processed(self):
        """增加已处理提交数"""
        self.processed_commits += 1
        if self.total_commits > 0:
            self.progress = int(self.processed_commits / self.total_commits * 100)
        self.save(update_fields=['processed_commits', 'progress'])


class ScheduledReviewConfig(models.Model):
    """定时评审配置表"""
    name = models.CharField(max_length=100, verbose_name='配置名称')
    description = models.TextField(blank=True, verbose_name='描述')
    
    # 仓库配置
    repositories = models.ManyToManyField(
        'repository.Repository',
        verbose_name='关联仓库'
    )
    
    # 调度配置
    cron_expression = models.CharField(
        max_length=100,
        verbose_name='Cron表达式',
        help_text='例如: 0 12 * * * (每天中午12点)'
    )
    
    # 分支配置
    branches = models.JSONField(
        default=list,
        verbose_name='评审分支',
        help_text='例如: ["master", "develop"]'
    )
    
    # 是否评审所有分支
    review_all_branches = models.BooleanField(
        default=False,
        verbose_name='评审所有分支'
    )
    
    # 是否启用
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 钉钉通知配置
    notify_on_complete = models.BooleanField(
        default=True,
        verbose_name='完成后通知'
    )
    notify_webhook = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='通知Webhook'
    )
    
    # 创建者
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='创建人'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    last_run_at = models.DateTimeField(null=True, blank=True, verbose_name='最后运行时间')
    
    class Meta:
        db_table = 'scheduled_review_config'
        verbose_name = '定时评审配置'
        verbose_name_plural = '定时评审配置'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['last_run_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.cron_expression})"


class RealtimeMonitorConfig(models.Model):
    """实时监控配置表"""
    repository = models.OneToOneField(
        'repository.Repository',
        on_delete=models.CASCADE,
        verbose_name='仓库'
    )
    
    # 是否启用实时监控
    is_active = models.BooleanField(default=False, verbose_name='是否启用')
    
    # 监控分支
    monitored_branches = models.JSONField(
        default=list,
        verbose_name='监控分支',
        help_text='例如: ["master", "develop"]'
    )
    
    # 监控间隔（秒）
    check_interval = models.IntegerField(
        default=60,
        verbose_name='检查间隔（秒）',
        help_text='多久检查一次新提交'
    )
    
    # 最后检查的commit
    last_checked_commit = models.CharField(
        max_length=40,
        blank=True,
        verbose_name='最后检查的Commit'
    )
    last_checked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后检查时间'
    )
    
    # 是否自动评审
    auto_review = models.BooleanField(
        default=True,
        verbose_name='自动评审'
    )
    
    # 是否发送钉钉通知
    notify_on_new_commit = models.BooleanField(
        default=True,
        verbose_name='新提交时通知'
    )
    
    # 通知级别（只通知高风险，还是所有）
    notify_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM,
        verbose_name='通知级别'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'realtime_monitor_config'
        verbose_name = '实时监控配置'
        verbose_name_plural = '实时监控配置'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['last_checked_at']),
        ]
    
    def __str__(self):
        return f"{self.repository.name} - {'启用' if self.is_active else '禁用'}"