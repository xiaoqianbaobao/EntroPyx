"""
AI对话序列化器
"""
from rest_framework import serializers
from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    """对话会话序列化器"""
    
    messages_count = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    knowledge_base_title = serializers.SerializerMethodField()
    repository_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'user', 'user_name', 'conversation_type',
            'knowledge_base', 'knowledge_base_title',
            'repository', 'repository_name',
            'is_active', 'messages_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'messages_count']
    
    def get_messages_count(self, obj):
        return obj.get_messages_count()
    
    def get_user_name(self, obj):
        return obj.user.username if obj.user else ''
    
    def get_knowledge_base_title(self, obj):
        return obj.knowledge_base.title if obj.knowledge_base else ''
    
    def get_repository_name(self, obj):
        return obj.repository.name if obj.repository else ''
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MessageSerializer(serializers.ModelSerializer):
    """对话消息序列化器"""
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'role', 'content',
            'knowledge_references', 'tokens_used',
            'response_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    """对话请求序列化器"""
    
    message = serializers.CharField(required=True, max_length=10000)
    conversation_id = serializers.IntegerField(required=False)
    conversation_type = serializers.ChoiceField(
        choices=Conversation.CONVERSATION_TYPES,
        default='general'
    )
    knowledge_base_id = serializers.IntegerField(required=False)
    repository_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        # 验证conversation_id
        if 'conversation_id' in data:
            from .models import Conversation
            try:
                conversation = Conversation.objects.get(id=data['conversation_id'])
                if conversation.user != self.context['request'].user:
                    raise serializers.ValidationError("无权访问该对话")
            except Conversation.DoesNotExist:
                raise serializers.ValidationError("对话不存在")
        
        return data


class ChatResponseSerializer(serializers.Serializer):
    """对话响应序列化器"""
    
    conversation_id = serializers.IntegerField()
    message_id = serializers.IntegerField()
    role = serializers.CharField()
    content = serializers.CharField()
    knowledge_references = serializers.ListField()
    tokens_used = serializers.IntegerField()
    response_time = serializers.FloatField()
