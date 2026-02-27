from rest_framework import serializers
from .models import TestCase, TestExecution, TestReport, TestCaseGenerationTask


class TestCaseGenerationTaskSerializer(serializers.ModelSerializer):
    """测试用例生成任务序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    prd_review_title = serializers.CharField(source='prd_review.title', read_only=True)
    code_review_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = TestCaseGenerationTask
        fields = [
            'id', 'task_id', 'status', 'status_display',
            'progress', 'current_step',
            'prd_review', 'prd_review_title',
            'code_review', 'code_review_info',
            'total_cases', 'generated_cases',
            'error_message',
            'created_by', 'created_by_name',
            'created_at', 'updated_at', 'completed_at'
        ]
    
    def get_code_review_info(self, obj):
        if obj.code_review:
            return f"{obj.code_review.repository.name} - {obj.code_review.branch}"
        return None


class TestCaseSerializer(serializers.ModelSerializer):
    """测试用例序列化器"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    review_status_display = serializers.CharField(source='get_review_status_display', read_only=True)
    
    class Meta:
        model = TestCase
        fields = [
            'id', 'prd_review', 'code_review', 'case_id', 'title',
            'type', 'type_display', 'priority', 'priority_display',
            'precondition', 'steps', 'expected_result',
            'dubbo_interface', 'dubbo_method', 'dubbo_params',
            'dubbo_group', 'dubbo_version',
            'review_status', 'review_status_display', 'review_comment',
            'reviewed_by', 'reviewed_at',
            'execution_count', 'last_execution_status', 'last_executed_at',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'execution_count']


class TestExecutionSerializer(serializers.ModelSerializer):
    """测试执行序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    test_case_id = serializers.CharField(source='test_case.case_id', read_only=True)
    
    class Meta:
        model = TestExecution
        fields = [
            'id', 'test_case', 'test_case_id', 'execution_batch',
            'status', 'status_display', 'request_data', 'response_data',
            'execution_time', 'error_message', 'stack_trace', 'executed_at'
        ]


class TestReportSerializer(serializers.ModelSerializer):
    """测试报告序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TestReport
        fields = [
            'id', 'batch_id', 'total_cases', 'passed_cases',
            'failed_cases', 'error_cases', 'skipped_cases', 'pass_rate',
            'start_time', 'end_time', 'duration', 'report_file',
            'environment', 'failed_details',
            'created_by', 'created_by_name', 'created_at'
        ]
