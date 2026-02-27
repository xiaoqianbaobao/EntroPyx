from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


class FileType(models.TextChoices):
    """文件类型"""
    WORD = 'word', 'Word文档'
    MARKDOWN = 'md', 'Markdown'
    PDF = 'pdf', 'PDF'


class ReviewStatus(models.TextChoices):
    """评审状态"""
    PENDING = 'PENDING', '待评审'
    APPROVED = 'APPROVED', '已通过'
    REJECTED = 'REJECTED', '需修改'


class PRDReview(models.Model):
    """PRD评审记录表"""
    title = models.CharField(max_length=200, verbose_name='PRD标题')
    description = models.TextField(blank=True, verbose_name='PRD描述')
    file = models.FileField(
        upload_to='prd/', 
        verbose_name='PRD文件',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'md', 'txt'])]
    )
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        verbose_name='文件类型'
    )
    file_size = models.IntegerField(verbose_name='文件大小(bytes)')
    
    # AI提取的结构化内容
    background = models.TextField(blank=True, verbose_name='背景描述')
    user_stories = models.JSONField(default=list, verbose_name='用户故事')
    requirements = models.JSONField(default=list, verbose_name='需求点')
    
    # 评审维度得分
    completeness_score = models.FloatField(verbose_name='完整性得分(0-1)')
    consistency_score = models.FloatField(verbose_name='一致性得分(0-1)')
    risk_score = models.FloatField(verbose_name='风险得分(0-1)')
    overall_score = models.FloatField(verbose_name='综合得分(0-1)')
    
    # AI建议
    ai_suggestions = models.TextField(verbose_name='AI改进建议')
    issues_found = models.JSONField(default=list, verbose_name='发现的问题')
    
    # 人工评审
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        verbose_name='评审状态'
    )
    review_comment = models.TextField(blank=True, verbose_name='评审意见')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prd_reviews',
        verbose_name='评审人'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='评审时间')
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_prds',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'prd_review'
        verbose_name = 'PRD评审'
        verbose_name_plural = 'PRD评审记录'
        indexes = [
            models.Index(fields=['created_by']),
            models.Index(fields=['review_status']),
            models.Index(fields=['overall_score']),
        ]
    
    def __str__(self):
        return self.title
