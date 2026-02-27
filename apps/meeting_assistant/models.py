"""
会议助手数据模型
Meeting Assistant Models
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator


class RecordingStatus(models.TextChoices):
    """录音状态"""
    UPLOADED = 'uploaded', '已上传'
    PROCESSING = 'processing', '处理中'
    COMPLETED = 'completed', '已完成'
    FAILED = 'failed', '失败'


class SummaryStatus(models.TextChoices):
    """纪要状态"""
    GENERATING = 'generating', '生成中'
    COMPLETED = 'completed', '已完成'
    FAILED = 'failed', '失败'


class OpinionType(models.TextChoices):
    """评审意见类型"""
    ISSUE = 'issue', '问题'
    SUGGESTION = 'suggestion', '建议'
    DECISION = 'decision', '决策'
    RISK = 'risk', '风险'
    POSITIVE = 'positive', '肯定意见'


class MeetingRecording(models.Model):
    """会议录音记录"""
    # 关联到仓库（因为现有系统没有ReviewMeeting模型，我们关联到Repository）
    repository = models.ForeignKey(
        'repository.Repository',
        on_delete=models.CASCADE,
        verbose_name='仓库',
        related_name='recordings'
    )
    
    # 基本信息
    meeting_title = models.CharField(max_length=200, verbose_name='会议标题')
    meeting_date = models.DateTimeField(default=timezone.now, verbose_name='会议时间')
    participants = models.TextField(verbose_name='参会人员（逗号分隔的用户名）')
    
    # 音频文件信息
    # 注意：这里 audio_file 是 CharField 而不是 FileField，可能是为了兼容外部存储路径
    # 如果是 FileField，可以直接加 validators。如果是 CharField，需要在 Form/Serializer 层校验
    # 假设这里是文件路径，我们在上传接口处进行校验
    audio_file = models.CharField(max_length=500, verbose_name='音频文件路径')
    audio_file_original_name = models.CharField(max_length=200, verbose_name='原始文件名')
    duration = models.IntegerField(default=0, help_text="时长(秒)", verbose_name='时长')
    file_size = models.BigIntegerField(default=0, help_text="文件大小(字节)", verbose_name='文件大小')
    
    # 处理状态
    status = models.CharField(
        max_length=20,
        choices=RecordingStatus.choices,
        default=RecordingStatus.UPLOADED,
        verbose_name='状态'
    )
    
    # 处理结果
    transcript_count = models.IntegerField(default=0, verbose_name='转写条数')
    
    # 创建者
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='创建人'
    )
    
    # 时间戳
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='处理完成时间')
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    class Meta:
        db_table = 'meeting_recording'
        verbose_name = '会议录音'
        verbose_name_plural = '会议录音'
        ordering = ['-upload_time']
        indexes = [
            models.Index(fields=['repository', '-upload_time']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.meeting_title} - {self.upload_time.strftime('%Y-%m-%d %H:%M')}"


class MeetingTranscript(models.Model):
    """会议转写文本"""
    recording = models.ForeignKey(
        MeetingRecording,
        on_delete=models.CASCADE,
        related_name='transcripts',
        verbose_name='录音'
    )
    
    # 说话人信息
    speaker = models.CharField(max_length=50, verbose_name="说话人标识", help_text="如 spk0, spk1")
    speaker_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联用户",
        help_text="可以手动关联到系统用户"
    )
    
    # 转写内容
    content = models.TextField(verbose_name="转写内容")
    
    # 时间信息
    start_time = models.FloatField(help_text="开始时间(秒)", verbose_name='开始时间')
    end_time = models.FloatField(help_text="结束时间(秒)", verbose_name='结束时间')
    
    # 置信度
    confidence = models.FloatField(default=0.0, help_text="识别置信度(0-1)", verbose_name='置信度')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'meeting_transcript'
        verbose_name = '会议转写'
        verbose_name_plural = '会议转写'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['recording', 'start_time']),
            models.Index(fields=['speaker']),
        ]
    
    def __str__(self):
        preview = self.content[:30] + '...' if len(self.content) > 30 else self.content
        return f"{self.speaker}: {preview} ({self.start_time}s)"


class MeetingSummary(models.Model):
    """会议纪要"""
    recording = models.OneToOneField(
        MeetingRecording,
        on_delete=models.CASCADE,
        related_name='summary',
        verbose_name='录音'
    )
    repository = models.ForeignKey(
        'repository.Repository',
        on_delete=models.CASCADE,
        verbose_name='仓库',
        related_name='meeting_summaries'
    )
    
    # 基本信息
    title = models.CharField(max_length=200, verbose_name='纪要标题')
    summary_text = models.TextField(verbose_name="会议摘要")
    template_type = models.CharField(max_length=50, default='会议纪要', verbose_name='模板类型')
    
    # 结构化内容(JSON存储)
    key_points = models.JSONField(default=list, help_text="讨论要点", verbose_name='讨论要点')
    decisions = models.JSONField(default=list, help_text="决策事项", verbose_name='决策事项')
    action_items = models.JSONField(default=list, help_text="待办任务", verbose_name='待办任务')
    
    # 用户输入
    user_notes = models.JSONField(default=list, help_text="用户笔记", verbose_name='用户笔记')
    user_todos = models.JSONField(default=list, help_text="用户待办", verbose_name='用户待办')
    
    # 导出的文档路径
    markdown_file = models.CharField(max_length=500, blank=True, verbose_name='Markdown文件')
    pdf_file = models.CharField(max_length=500, blank=True, verbose_name='PDF文件')
    docx_file = models.CharField(max_length=500, blank=True, verbose_name='Word文件')
    image_file = models.CharField(max_length=500, blank=True, verbose_name='图片文件')  # 新增：图文纪要图片
    
    # 状态信息
    status = models.CharField(
        max_length=20,
        choices=SummaryStatus.choices,
        default=SummaryStatus.COMPLETED,
        verbose_name='状态'
    )
    
    # 创建者信息
    generated_by = models.CharField(
        max_length=20,
        choices=[('auto', '自动生成'), ('manual', '人工编辑')],
        default='auto',
        verbose_name='生成方式'
    )
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'meeting_summary'
        verbose_name = '会议纪要'
        verbose_name_plural = '会议纪要'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['recording']),
            models.Index(fields=['repository', '-generated_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title


class ReviewOpinion(models.Model):
    """评审意见(从会议中提取)"""
    summary = models.ForeignKey(
        MeetingSummary,
        on_delete=models.CASCADE,
        related_name='opinions',
        verbose_name='会议纪要'
    )
    transcript = models.ForeignKey(
        MeetingTranscript,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="转写片段",
        help_text="对应的转写片段"
    )
    
    # 意见类型和内容
    opinion_type = models.CharField(
        max_length=20,
        choices=OpinionType.choices,
        verbose_name='意见类型'
    )
    content = models.TextField(verbose_name="意见内容")
    
    # 说话人信息
    speaker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='说话人'
    )
    
    # 优先级
    priority = models.CharField(
        max_length=10,
        choices=[('high', '高'), ('medium', '中'), ('low', '低')],
        default='medium',
        verbose_name='优先级'
    )
    
    # 状态
    is_resolved = models.BooleanField(default=False, verbose_name='是否已解决')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='解决时间')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'review_opinion'
        verbose_name = '评审意见'
        verbose_name_plural = '评审意见'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['summary', 'opinion_type']),
            models.Index(fields=['speaker']),
            models.Index(fields=['is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.get_opinion_type_display()}: {self.content[:30]}..."


# ========== 知识图谱相关模型 ==========

class EntityType(models.TextChoices):
    """实体类型"""
    PERSON = 'person', '人员'
    PROJECT = 'project', '项目'
    TOPIC = 'topic', '主题'
    ISSUE = 'issue', '问题'
    TECHNOLOGY = 'technology', '技术'
    DECISION = 'decision', '决策'


class RelationType(models.TextChoices):
    """关系类型"""
    ATTENDED = 'attended', '参会'
    DISCUSSED = 'discussed', '讨论'
    RAISED = 'raised', '提出'
    RESOLVED = 'resolved', '解决'
    RELATED_TO = 'related_to', '相关'
    MENTIONED = 'mentioned', '提及'
    DECIDED = 'decided', '决定'


class KnowledgeEntity(models.Model):
    """知识图谱实体"""
    entity_type = models.CharField(
        max_length=20,
        choices=EntityType.choices,
        verbose_name='实体类型'
    )
    entity_name = models.CharField(max_length=200, verbose_name='实体名称')
    
    # 关联到Django对象
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联用户'
    )
    repository = models.ForeignKey(
        'repository.Repository',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联仓库'
    )
    meeting = models.ForeignKey(
        MeetingRecording,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联会议'
    )
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    confidence = models.FloatField(default=1.0, verbose_name='置信度')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'knowledge_entity'
        verbose_name = '知识实体'
        verbose_name_plural = '知识实体'
        unique_together = ['entity_type', 'entity_name']
        indexes = [
            models.Index(fields=['entity_type', 'entity_name']),
            models.Index(fields=['user']),
            models.Index(fields=['repository']),
            models.Index(fields=['meeting']),
        ]
    
    def __str__(self):
        return f"{self.get_entity_type_display()}: {self.entity_name}"


class KnowledgeRelation(models.Model):
    """知识图谱关系"""
    source = models.ForeignKey(
        KnowledgeEntity,
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name='源实体'
    )
    target = models.ForeignKey(
        KnowledgeEntity,
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name='目标实体'
    )
    
    relation_type = models.CharField(
        max_length=20,
        choices=RelationType.choices,
        verbose_name='关系类型'
    )
    
    # 关系属性
    properties = models.JSONField(default=dict, verbose_name='关系属性')
    confidence = models.FloatField(default=1.0, verbose_name='置信度')
    
    # 关联到具体的内容
    summary = models.ForeignKey(
        MeetingSummary,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联纪要'
    )
    transcript = models.ForeignKey(
        MeetingTranscript,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联转写'
    )
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'knowledge_relation'
        verbose_name = '知识关系'
        verbose_name_plural = '知识关系'
        unique_together = ['source', 'target', 'relation_type']
        indexes = [
            models.Index(fields=['source', 'target']),
            models.Index(fields=['relation_type']),
            models.Index(fields=['summary']),
        ]
    
    def __str__(self):
        return f"{self.source.entity_name} -[{self.get_relation_type_display()}]-> {self.target.entity_name}"