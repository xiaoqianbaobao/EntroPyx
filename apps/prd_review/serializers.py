from rest_framework import serializers
from .models import PRDReview, FileType, ReviewStatus


class PRDReviewSerializer(serializers.ModelSerializer):
    """PRD评审序列化器"""
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    review_status_display = serializers.CharField(source='get_review_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    
    class Meta:
        model = PRDReview
        fields = [
            'id', 'title', 'file', 'file_type', 'file_type_display',
            'file_size', 'background', 'user_stories', 'requirements',
            'completeness_score', 'consistency_score', 'risk_score',
            'overall_score', 'ai_suggestions', 'issues_found',
            'review_status', 'review_status_display', 'review_comment',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'file_type', 'file_size', 'completeness_score',
            'consistency_score', 'risk_score', 'overall_score',
            'ai_suggestions', 'issues_found', 'created_at'
        ]


class PRDReviewCreateSerializer(serializers.ModelSerializer):
    """PRD评审创建序列化器"""
    class Meta:
        model = PRDReview
        fields = ['title', 'description', 'file']
    
    def create(self, validated_data):
        # 自动识别文件类型
        file = validated_data['file']
        file_name = file.name.lower()
        
        if file_name.endswith('.md'):
            validated_data['file_type'] = FileType.MARKDOWN
        elif file_name.endswith('.pdf'):
            validated_data['file_type'] = FileType.PDF
        else:
            validated_data['file_type'] = FileType.WORD
        
        validated_data['file_size'] = file.size
        
        # 设置默认分数
        validated_data['completeness_score'] = 0.0
        validated_data['consistency_score'] = 0.0
        validated_data['risk_score'] = 0.0
        validated_data['overall_score'] = 0.0
        
        return super().create(validated_data)
