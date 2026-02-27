"""
知识库数据模型
Knowledge Base Models
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class KnowledgeDocument(models.Model):
    """知识库文档"""
    # 基本信息
    title = models.CharField(max_length=200, verbose_name='文档标题')
    description = models.TextField(blank=True, verbose_name='文档描述')
    file = models.FileField(upload_to='knowledge_docs/', verbose_name='文档文件')
    file_name = models.CharField(max_length=200, verbose_name='原始文件名')
    file_type = models.CharField(max_length=20, verbose_name='文件类型')
    file_size = models.IntegerField(verbose_name='文件大小（字节）')
    
    # 知识信息
    content = models.TextField(verbose_name='文档内容')
    structured_data = models.JSONField(default=dict, verbose_name='结构化数据')
    
    # 状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('processing', '处理中'),
            ('completed', '已完成'),
            ('failed', '处理失败')
        ],
        default='pending',
        verbose_name='处理状态'
    )
    
    # 统计信息
    section_count = models.IntegerField(default=0, verbose_name='章节数量')
    keyword_count = models.IntegerField(default=0, verbose_name='关键词数量')
    entity_count = models.IntegerField(default=0, verbose_name='实体数量')
    
    # 创建和更新
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='处理完成时间')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '知识库文档'
        verbose_name_plural = '知识库文档'
    
    def __str__(self):
        return self.title
    
    @property
    def is_processed(self):
        """是否已处理"""
        return self.status == 'completed'
    
    @property
    def content_preview(self):
        """内容预览"""
        preview_length = 100
        if len(self.content) <= preview_length:
            return self.content
        return self.content[:preview_length] + '...'


class KnowledgeEntity(models.Model):
    """知识实体"""
    # 实体信息
    name = models.CharField(max_length=100, verbose_name='实体名称')
    entity_type = models.CharField(max_length=50, verbose_name='实体类型')
    description = models.TextField(blank=True, verbose_name='实体描述')
    
    # 关联文档
    documents = models.ManyToManyField(
        KnowledgeDocument,
        through='KnowledgeEntityDocument',
        related_name='entities',
        verbose_name='关联文档'
    )
    
    # 知识图谱信息
    confidence = models.FloatField(default=0.0, verbose_name='置信度')
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    
    # 创建和更新
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        ordering = ['name']
        verbose_name = '知识实体'
        verbose_name_plural = '知识实体'
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"


class KnowledgeEntityDocument(models.Model):
    """知识实体-文档关联表"""
    entity = models.ForeignKey(KnowledgeEntity, on_delete=models.CASCADE)
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE)
    
    # 实体在文档中的位置信息
    position = models.JSONField(default=dict, verbose_name='位置信息')
    context = models.TextField(verbose_name='上下文')
    
    # 置信度
    confidence = models.FloatField(default=0.0, verbose_name='置信度')
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['entity', 'document']
        verbose_name = '实体-文档关联'
        verbose_name_plural = '实体-文档关联'


class KnowledgeRelation(models.Model):
    """知识关系"""
    # 关系信息
    source_entity = models.ForeignKey(
        KnowledgeEntity,
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name='源实体'
    )
    target_entity = models.ForeignKey(
        KnowledgeEntity,
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name='目标实体'
    )
    
    # 关系类型
    relation_type = models.CharField(max_length=50, verbose_name='关系类型')
    description = models.TextField(blank=True, verbose_name='关系描述')
    
    # 知识图谱信息
    confidence = models.FloatField(default=0.0, verbose_name='置信度')
    properties = models.JSONField(default=dict, verbose_name='关系属性')
    
    # 创建和更新
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        unique_together = ['source_entity', 'target_entity', 'relation_type']
        ordering = ['relation_type']
        verbose_name = '知识关系'
        verbose_name_plural = '知识关系'
    
    def __str__(self):
        return f"{self.source_entity.name} --{self.relation_type}--> {self.target_entity.name}"


class KnowledgeQuery(models.Model):
    """知识查询记录"""
    # 查询信息
    query_text = models.TextField(verbose_name='查询文本')
    response_text = models.TextField(blank=True, verbose_name='响应文本')
    
    # 关联文档
    related_documents = models.ManyToManyField(
        KnowledgeDocument,
        blank=True,
        verbose_name='相关文档'
    )
    
    # 搜索结果
    search_results = models.JSONField(default=list, verbose_name='搜索结果')
    confidence_score = models.FloatField(default=0.0, verbose_name='置信度')
    
    # 用户信息
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='查询用户'
    )
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '知识查询'
        verbose_name_plural = '知识查询'
    
    def __str__(self):
        return f"查询: {self.query_text[:50]}..."



class DocumentChunk(models.Model):
    """文档块"""
    # 关联文档
    document = models.ForeignKey(
        KnowledgeDocument,
        on_delete=models.CASCADE,
        related_name='chunks',
        verbose_name='所属文档'
    )
    
    # 块信息
    chunk_index = models.IntegerField(verbose_name='块索引')
    content = models.TextField(verbose_name='块内容')
    content_length = models.IntegerField(verbose_name='内容长度')
    
    # 向量化
    embedding = models.JSONField(default=list, verbose_name='向量表示')
    
    # 状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('embedding', '向量化中'),
            ('indexed', '已索引'),
            ('failed', '处理失败')
        ],
        default='pending',
        verbose_name='块状态'
    )
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        ordering = ['chunk_index']
        verbose_name = '文档块'
        verbose_name_plural = '文档块'
    
    def __str__(self):
        return f"{self.document.title} - 块 {self.chunk_index}"


class ChunkStatus:
    """块状态常量"""
    PENDING = 'pending'
    EMBEDDING = 'embedding'
    INDEXED = 'indexed'
    FAILED = 'failed'