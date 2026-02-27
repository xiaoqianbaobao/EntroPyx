"""
会议助手序列化器
Meeting Assistant Serializers
"""
from rest_framework import serializers
from .models import (
    MeetingRecording,
    MeetingTranscript,
    MeetingSummary,
    ReviewOpinion
)


class MeetingTranscriptSerializer(serializers.ModelSerializer):
    """会议转写序列化器"""
    speaker_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MeetingTranscript
        fields = [
            'id', 'speaker', 'speaker_user', 'content',
            'start_time', 'end_time', 'confidence', 'speaker_name'
        ]
    
    def get_speaker_name(self, obj):
        """获取说话人名称"""
        if obj.speaker_user:
            return obj.speaker_user.get_full_name() or obj.speaker_user.username
        return obj.speaker


class MeetingRecordingSerializer(serializers.ModelSerializer):
    """会议录音序列化器"""
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    transcript_count = serializers.ReadOnlyField()
    summary_title = serializers.SerializerMethodField()
    
    class Meta:
        model = MeetingRecording
        fields = [
            'id', 'repository', 'repository_name', 'meeting_title', 'meeting_date',
            'participants', 'audio_file', 'audio_file_original_name',
            'duration', 'file_size', 'status', 'transcript_count',
            'summary_title', 'upload_time', 'processed_at', 'error_message',
            'created_by'
        ]
        read_only_fields = ['upload_time', 'processed_at', 'transcript_count']
    
    def get_summary_title(self, obj):
        """获取关联的纪要标题"""
        if hasattr(obj, 'summary'):
            return obj.summary.title
        return None


class RecordingUploadSerializer(serializers.Serializer):
    """录音上传序列化器"""
    repository_id = serializers.IntegerField(required=True)
    meeting_title = serializers.CharField(max_length=200, required=False, default='会议录音')
    meeting_date = serializers.DateTimeField(required=False, allow_null=True)
    participants = serializers.CharField(required=False, allow_blank=True, default='')
    audio_file = serializers.FileField(required=True)
    template_type = serializers.CharField(required=False, allow_blank=True, default='会议纪要')
    notes = serializers.JSONField(required=False, default=list)
    todos = serializers.JSONField(required=False, default=list)


class ReviewOpinionSerializer(serializers.ModelSerializer):
    """评审意见序列化器"""
    speaker_name = serializers.SerializerMethodField()
    transcript_content = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewOpinion
        fields = [
            'id', 'summary', 'transcript', 'opinion_type', 'content',
            'speaker', 'speaker_name', 'transcript_content',
            'priority', 'is_resolved', 'resolved_at', 'created_at'
        ]
        read_only_fields = ['created_at', 'resolved_at']
    
    def get_speaker_name(self, obj):
        """获取说话人名称"""
        if obj.speaker:
            return obj.speaker.get_full_name() or obj.speaker.username
        return None
    
    def get_transcript_content(self, obj):
        """获取转写内容"""
        if obj.transcript:
            return obj.transcript.content
        return None


class MeetingSummarySerializer(serializers.ModelSerializer):
    """会议纪要序列化器"""
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    recording_title = serializers.CharField(source='recording.meeting_title', read_only=True)
    opinions = ReviewOpinionSerializer(many=True, read_only=True)
    transcripts = MeetingTranscriptSerializer(
        source='recording.transcripts',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = MeetingSummary
        fields = [
            'id', 'recording', 'recording_title', 'repository', 'repository_name',
            'title', 'summary_text', 'key_points', 'decisions', 'action_items',
            'markdown_file', 'pdf_file', 'docx_file', 'status',
            'generated_by', 'generated_at', 'updated_at',
            'opinions', 'transcripts'
        ]
        read_only_fields = ['generated_at', 'updated_at']


class SummaryGenerateSerializer(serializers.Serializer):
    """生成纪要序列化器"""
    force_regenerate = serializers.BooleanField(required=False, default=False)
    template_type = serializers.CharField(required=False, default='会议纪要')