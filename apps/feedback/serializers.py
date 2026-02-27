from rest_framework import serializers
from .models import FeedbackRule, RuleType


class FeedbackRuleSerializer(serializers.ModelSerializer):
    """反馈规则序列化器"""
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FeedbackRule
        fields = [
            'id', 'rule_type', 'rule_type_display', 'pattern',
            'description', 'weight', 'feedback_count', 'accuracy_rate',
            'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'feedback_count']


class FeedbackRuleCreateSerializer(serializers.ModelSerializer):
    """反馈规则创建序列化器"""
    
    class Meta:
        model = FeedbackRule
        fields = ['rule_type', 'pattern', 'description', 'weight']
