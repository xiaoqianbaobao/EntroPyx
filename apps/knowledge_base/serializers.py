"""
知识库序列化器
Knowledge Base Serializers
"""
from rest_framework import serializers
from .models import (
    KnowledgeDocument,
    KnowledgeEntity,
    KnowledgeRelation,
    KnowledgeQuery
)


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    """知识库文档序列化器"""
    
    class Meta:
        model = KnowledgeDocument
        fields = [
            'id', 'title', 'description', 'file_name', 'file_type',
            'file_size', 'content', 'structured_data', 'status',
            'section_count', 'keyword_count', 'entity_count',
            'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'content', 'structured_data', 'created_at',
            'updated_at', 'processed_at'
        ]


class KnowledgeEntitySerializer(serializers.ModelSerializer):
    """知识实体序列化器"""
    
    class Meta:
        model = KnowledgeEntity
        fields = [
            'id', 'name', 'entity_type', 'description',
            'confidence', 'metadata', 'created_at', 'updated_at'
        ]


class KnowledgeRelationSerializer(serializers.ModelSerializer):
    """知识关系序列化器"""
    
    class Meta:
        model = KnowledgeRelation
        fields = [
            'id', 'source_entity', 'target_entity', 'relation_type',
            'description', 'confidence', 'properties', 'created_at',
            'updated_at'
        ]


class KnowledgeQuerySerializer(serializers.ModelSerializer):
    """知识查询序列化器"""
    
    class Meta:
        model = KnowledgeQuery
        fields = [
            'id', 'query_text', 'response_text', 'confidence_score',
            'created_at'
        ]
        read_only_fields = [
            'id', 'response_text', 'confidence_score', 'created_at'
        ]
    
    def validate_query_text(self, value):
        """验证查询文本"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("查询文本至少需要2个字符")
        if len(value.strip()) > 1000:
            raise serializers.ValidationError("查询文本不能超过1000个字符")
        return value.strip()