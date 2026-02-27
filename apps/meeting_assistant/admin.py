"""
会议助手Admin配置
Meeting Assistant Admin Configuration
"""
from django.contrib import admin
from .models import (
    MeetingRecording,
    MeetingTranscript,
    MeetingSummary,
    ReviewOpinion,
    KnowledgeEntity,
    KnowledgeRelation
)


@admin.register(MeetingRecording)
class MeetingRecordingAdmin(admin.ModelAdmin):
    """会议录音Admin"""
    list_display = [
        'id', 'meeting_title', 'repository', 'meeting_date',
        'status', 'transcript_count', 'upload_time', 'created_by'
    ]
    list_filter = ['status', 'repository', 'upload_time']
    search_fields = ['meeting_title', 'participants']
    readonly_fields = ['upload_time', 'processed_at', 'transcript_count']
    date_hierarchy = 'upload_time'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('repository', 'meeting_title', 'meeting_date', 'participants')
        }),
        ('音频文件', {
            'fields': ('audio_file', 'audio_file_original_name', 'duration', 'file_size')
        }),
        ('处理状态', {
            'fields': ('status', 'transcript_count', 'upload_time', 'processed_at', 'error_message')
        }),
        ('创建信息', {
            'fields': ('created_by',)
        }),
    )


@admin.register(MeetingTranscript)
class MeetingTranscriptAdmin(admin.ModelAdmin):
    """会议转写Admin"""
    list_display = ['id', 'recording', 'speaker', 'start_time', 'end_time', 'confidence']
    list_filter = ['speaker', 'recording']
    search_fields = ['content']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recording', 'speaker_user')


@admin.register(MeetingSummary)
class MeetingSummaryAdmin(admin.ModelAdmin):
    """会议纪要Admin"""
    list_display = [
        'id', 'title', 'repository', 'recording',
        'status', 'generated_by', 'generated_at'
    ]
    list_filter = ['status', 'generated_by', 'repository']
    search_fields = ['title', 'summary_text']
    readonly_fields = ['generated_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('recording', 'repository', 'title', 'summary_text')
        }),
        ('结构化内容', {
            'fields': ('key_points', 'decisions', 'action_items')
        }),
        ('导出文件', {
            'fields': ('markdown_file', 'pdf_file', 'docx_file')
        }),
        ('状态信息', {
            'fields': ('status', 'generated_by', 'generated_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recording', 'repository')


@admin.register(ReviewOpinion)
class ReviewOpinionAdmin(admin.ModelAdmin):
    """评审意见Admin"""
    list_display = [
        'id', 'summary', 'opinion_type', 'content_preview',
        'speaker', 'priority', 'is_resolved', 'created_at'
    ]
    list_filter = ['opinion_type', 'priority', 'is_resolved']
    search_fields = ['content']
    readonly_fields = ['created_at', 'resolved_at']
    
    def content_preview(self, obj):
        """内容预览"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '内容'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('summary', 'speaker', 'transcript')
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        """批量标记为已解决"""
        from django.utils import timezone
        count = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'成功标记 {count} 条意见为已解决')
    mark_as_resolved.short_description = '标记为已解决'


@admin.register(KnowledgeEntity)
class KnowledgeEntityAdmin(admin.ModelAdmin):
    """知识实体Admin"""
    list_display = [
        'id', 'entity_name', 'entity_type', 'user', 
        'repository', 'meeting', 'confidence', 'created_at'
    ]
    list_filter = ['entity_type', 'created_at']
    search_fields = ['entity_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'repository', 'meeting')


@admin.register(KnowledgeRelation)
class KnowledgeRelationAdmin(admin.ModelAdmin):
    """知识关系Admin"""
    list_display = [
        'id', 'source', 'target', 'relation_type', 
        'confidence', 'created_at'
    ]
    list_filter = ['relation_type', 'created_at']
    search_fields = ['source__entity_name', 'target__entity_name']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('source', 'target', 'summary', 'transcript')