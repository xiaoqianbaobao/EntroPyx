from rest_framework import serializers
from apps.code_review.models import (
    ScheduledReviewConfig, 
    RealtimeMonitorConfig,
    CodeReview,
    ReviewTask
)


class ScheduledReviewConfigSerializer(serializers.ModelSerializer):
    """定时评审配置序列化器"""
    repository_names = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledReviewConfig
        fields = [
            'id', 'name', 'description', 'repositories', 'repository_names',
            'cron_expression', 'branches', 'review_all_branches', 
            'is_active', 'notify_on_complete', 'notify_webhook',
            'created_by', 'created_at', 'updated_at', 'last_run_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'last_run_at']
    
    def get_repository_names(self, obj):
        return [repo.name for repo in obj.repositories.all()]


class RealtimeMonitorConfigSerializer(serializers.ModelSerializer):
    """实时监控配置序列化器"""
    repository_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RealtimeMonitorConfig
        fields = [
            'id', 'repository', 'repository_name', 'is_active',
            'monitored_branches', 'check_interval', 'last_checked_commit',
            'last_checked_at', 'auto_review', 'notify_on_new_commit',
            'notify_level', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_checked_at']
    
    def get_repository_name(self, obj):
        return obj.repository.name if obj.repository else None


class CodeReviewSerializer(serializers.ModelSerializer):
    """代码评审序列化器"""
    repository_name = serializers.SerializerMethodField()
    trigger_mode_display = serializers.CharField(source='get_trigger_mode_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    triggered_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeReview
        fields = [
            'id', 'repository', 'repository_name', 'branch', 'commit_hash',
            'commit_message', 'author', 'author_email', 'commit_time',
            'trigger_mode', 'trigger_mode_display', 'triggered_by',
            'triggered_by_name', 'risk_score', 'risk_level', 'risk_level_display',
            'ai_review_content', 'ai_model', 'changed_files', 'diff_content',
            'lines_added', 'lines_deleted', 'lines_changed', 'review_points',
            'feedback_status', 'feedback_comment', 'feedback_by',
            'feedback_at', 'dingtalk_sent', 'dingtalk_sent_at', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_repository_name(self, obj):
        return obj.repository.name if obj.repository else None
    
    def get_triggered_by_name(self, obj):
        return obj.triggered_by.username if obj.triggered_by else None


class ReviewTaskSerializer(serializers.ModelSerializer):
    """评审任务序列化器"""
    repository_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    trigger_mode_display = serializers.CharField(source='get_trigger_mode_display', read_only=True)
    triggered_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewTask
        fields = [
            'id', 'task_id', 'repository', 'repository_name', 'branch',
            'status', 'status_display', 'current_step', 'progress',
            'total_commits', 'processed_commits', 'trigger_mode',
            'trigger_mode_display', 'triggered_by', 'triggered_by_name',
            'high_risk_count', 'medium_risk_count', 'low_risk_count',
            'dingtalk_notified_count', 'error_message', 'started_at',
            'completed_at', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_repository_name(self, obj):
        return obj.repository.name if obj.repository else None
    
    def get_triggered_by_name(self, obj):
        return obj.triggered_by.username if obj.triggered_by else None