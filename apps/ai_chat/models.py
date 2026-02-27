"""
AI对话模型
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Conversation(models.Model):
    """对话会话"""
    
    CONVERSATION_TYPES = [
        ('code_review', '代码评审'),
        ('prd_review', 'PRD评审'),
        ('test_case', '测试用例'),
        ('knowledge', '知识库问答'),
        ('general', '通用对话'),
    ]
    
    title = models.CharField(max_length=255, verbose_name='对话标题')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    conversation_type = models.CharField(
        max_length=20, 
        choices=CONVERSATION_TYPES, 
        default='general',
        verbose_name='对话类型'
    )
    knowledge_base = models.ForeignKey(
        'knowledge_base.KnowledgeDocument', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='关联知识库'
    )
    repository = models.ForeignKey(
        'repository.Repository', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='关联仓库'
    )
    current_mode = models.CharField(
        max_length=50,
        default='chat',
        verbose_name='当前模式',
        help_text='chat, code_review_flow, agent_rag'
    )
    context_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='上下文数据',
        help_text='存储多轮对话的槽位数据'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '对话会话'
        verbose_name_plural = '对话会话'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"
    
    def get_messages_count(self):
        """获取消息数量"""
        return self.messages.count()


class Message(models.Model):
    """对话消息"""
    
    MESSAGE_ROLES = [
        ('user', '用户'),
        ('assistant', '助手'),
        ('system', '系统'),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name='对话会话'
    )
    role = models.CharField(
        max_length=10, 
        choices=MESSAGE_ROLES, 
        verbose_name='消息角色'
    )
    content = models.TextField(verbose_name='消息内容')
    knowledge_references = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name='知识库引用'
    )
    tokens_used = models.IntegerField(default=0, verbose_name='使用的Token数')
    response_time = models.FloatField(default=0.0, verbose_name='响应时间（秒）')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '对话消息'
        verbose_name_plural = '对话消息'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.conversation.title} - {self.role}"