from rest_framework import serializers
from .models import Repository


class RepositorySerializer(serializers.ModelSerializer):
    """仓库序列化器"""
    clone_status = serializers.BooleanField(read_only=True)
    auth_type_display = serializers.CharField(source='get_auth_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Repository
        fields = [
            'id', 'name', 'git_url', 'auth_type', 'auth_type_display',
            'username', 'local_path', 'clone_status',
            'dingtalk_webhook', 'dingtalk_secret',
            'high_risk_threshold', 'medium_risk_threshold',
            'review_branch', 'review_all_branches',
            'critical_patterns', 'ignore_patterns',
            'enable_manual_review', 'enable_scheduled_review',
            'scheduled_review_cron', 'enable_realtime_monitor',
            'realtime_monitor_interval', 'realtime_monitor_branches',
            'auto_review_on_new_commit', 'notify_on_review_complete',
            'notify_risk_threshold',
            'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'clone_status', 'created_at', 'updated_at']
        extra_kwargs = {
            'password_encrypted': {'write_only': True},
            'ssh_key_encrypted': {'write_only': True},
            'dingtalk_secret': {'write_only': True}
        }


class RepositoryCreateSerializer(serializers.ModelSerializer):
    """仓库创建序列化器"""
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ssh_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    local_path = serializers.CharField(required=False, allow_blank=True, help_text='本地存储路径，不提供则自动生成')

    class Meta:
        model = Repository
        fields = [
            'name', 'git_url', 'auth_type', 'username', 'password', 'ssh_key',
            'local_path',
            'dingtalk_webhook', 'dingtalk_secret',
            'high_risk_threshold', 'medium_risk_threshold',
            'review_branch', 'review_all_branches',
            'critical_patterns', 'ignore_patterns',
            'enable_manual_review', 'enable_scheduled_review',
            'scheduled_review_cron', 'enable_realtime_monitor',
            'realtime_monitor_interval', 'realtime_monitor_branches',
            'auto_review_on_new_commit', 'notify_on_review_complete',
            'notify_risk_threshold'
        ]

    def create(self, validated_data):
        # 加密存储密码
        password = validated_data.pop('password', None)
        ssh_key = validated_data.pop('ssh_key', None)
        local_path = validated_data.pop('local_path', None)

        if password:
            validated_data['password_encrypted'] = self._encrypt_password(password)
        if ssh_key:
            validated_data['ssh_key_encrypted'] = self._encrypt_key(ssh_key)

        # 自动生成local_path如果未提供
        if not local_path:
            import os
            from django.conf import settings
            name = validated_data.get('name', 'repo')
            # 清理仓库名称，移除不安全字符
            safe_name = "".join(c if c.isalnum() or c in ('-', '_', '.') else '_' for c in name)
            local_path = os.path.join(settings.BASE_DIR, 'repos', safe_name)
        validated_data['local_path'] = local_path

        return Repository.objects.create(**validated_data)
    
    def _encrypt_password(self, password):
        """简单加密密码（生产环境应使用更安全的方式）"""
        import base64
        return base64.b64encode(password.encode()).decode()
    
    def _encrypt_key(self, key):
        """简单加密SSH Key"""
        import base64
        return base64.b64encode(key.encode()).decode()


class RepositoryTestSerializer(serializers.Serializer):
    """测试连接序列化器"""
    repository_id = serializers.IntegerField()
