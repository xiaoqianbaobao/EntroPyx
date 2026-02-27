"""
会议助手视图
Meeting Assistant Views
"""
import os
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework import viewsets
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import (
    MeetingRecording,
    MeetingTranscript,
    MeetingSummary,
    ReviewOpinion,
    RecordingStatus,
    KnowledgeEntity
)
from .serializers import (
    MeetingRecordingSerializer,
    MeetingSummarySerializer,
    ReviewOpinionSerializer,
    RecordingUploadSerializer,
    SummaryGenerateSerializer
)
from .tasks import process_audio_task, generate_summary_task, export_document_task

logger = logging.getLogger(__name__)


# ==================== 页面视图 ====================

@login_required
def meeting_list(request):
    """会议列表页面"""
    # 获取筛选参数
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    # 基础查询集
    queryset = MeetingRecording.objects.select_related('repository', 'created_by').all().order_by('-upload_time')
    
    # 应用筛选
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if search_query:
        queryset = queryset.filter(meeting_title__icontains=search_query)
        
    # 分页处理
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10) # 默认每页10条
    try:
        per_page = int(per_page)
        if per_page < 1: per_page = 10
        if per_page > 100: per_page = 100 # 限制最大每页显示数
    except ValueError:
        per_page = 10
        
    paginator = Paginator(queryset, per_page)
    
    try:
        recordings = paginator.page(page)
    except PageNotAnInteger:
        recordings = paginator.page(1)
    except EmptyPage:
        recordings = paginator.page(paginator.num_pages)
        
    return render(request, 'meeting_assistant/meeting_list.html', {
        'recordings': recordings,
        'status_filter': status_filter,
        'search_query': search_query,
        'per_page': per_page,
        'total_count': paginator.count # 传递总记录数
    })


@login_required
def meeting_detail(request, pk):
    """会议详情页面"""
    recording = get_object_or_404(
        MeetingRecording.objects.select_related('repository', 'created_by'),
        pk=pk
    )
    transcripts = recording.transcripts.all().order_by('start_time')
    
    # 获取纪要（如果存在）
    summary = None
    if hasattr(recording, 'summary'):
        summary = recording.summary
    
    return render(request, 'meeting_assistant/meeting_detail.html', {
        'recording': recording,
        'transcripts': transcripts,
        'summary': summary
    })


@login_required
def meeting_upload(request):
    """会议上传页面"""
    from apps.repository.models import Repository
    repositories = Repository.objects.filter(is_active=True)
    
    return render(request, 'meeting_assistant/meeting_upload.html', {
        'repositories': repositories
    })


@login_required
def realtime_record(request):
    """实时录音页面"""
    from apps.repository.models import Repository
    repositories = Repository.objects.filter(is_active=True)
    
    return render(request, 'meeting_assistant/meeting_record_realtime.html', {
        'repositories': repositories
    })


@login_required
def summary_detail(request, pk):
    """纪要详情页面"""
    summary = get_object_or_404(
        MeetingSummary.objects.select_related('recording', 'repository'),
        pk=pk
    )
    return render(request, 'meeting_assistant/summary_detail.html', {
        'summary': summary
    })


# ==================== API视图 ====================

class RecordingListView(generics.ListAPIView):
    """录音列表API"""
    serializer_class = MeetingRecordingSerializer
    
    def get_queryset(self):
        queryset = MeetingRecording.objects.select_related('repository', 'created_by').all()
        
        # 筛选条件
        repository_id = self.request.query_params.get('repository_id')
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.order_by('-upload_time')


class RecordingDetailView(generics.RetrieveAPIView):
    """录音详情API"""
    serializer_class = MeetingRecordingSerializer
    
    def get_queryset(self):
        return MeetingRecording.objects.select_related('repository', 'created_by').all()


class RecordingBulkDeleteView(APIView):
    """批量删除录音API"""
    
    def post(self, request):
        recording_ids = request.data.get('ids', [])
        if not recording_ids or not isinstance(recording_ids, list):
            return Response({
                'error': '请提供有效的录音ID列表'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # 过滤存在的ID
            recordings = MeetingRecording.objects.filter(id__in=recording_ids)
            count = recordings.count()
            
            # 删除相关文件（如果有的话，通常Django FileField会自动处理，或者需要在delete信号中处理）
            # 这里简单调用 delete() 方法，触发级联删除
            recordings.delete()
            
            return Response({
                'message': f'成功删除 {count} 条录音记录',
                'deleted_count': count
            })
        except Exception as e:
            logger.error(f"批量删除录音失败: {str(e)}")
            return Response({
                'error': f'删除失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class RecordingUploadView(APIView):
    """上传会议录音"""
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]  # 暂时允许未认证用户上传，生产环境应改为IsAuthenticated
    
    def post(self, request):
        serializer = RecordingUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 保存音频文件
            audio_file = serializer.validated_data['audio_file']
            
            # 手动校验文件后缀（因为 audio_file 是 CharField，Model 层的 validator 可能未生效或被绕过，且这里是上传逻辑）
            # 注意：如果 serializer 中 audio_file 是 FileField，则可以在 serializer 中校验
            # 这里为了保险，增加一层手动校验
            valid_extensions = ['mp3', 'wav', 'm4a', 'ogg', 'aac', 'flac']
            ext = os.path.splitext(audio_file.name)[1][1:].lower()
            if ext not in valid_extensions:
                return Response(
                    {'error': f'不支持的音频格式: {ext}。请上传 {", ".join(valid_extensions)} 格式的文件。'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 创建保存路径
            upload_dir = f'meeting_audios/{serializer.validated_data["repository_id"]}'
            file_path = default_storage.save(
                os.path.join(upload_dir, audio_file.name),
                audio_file
            )
            
            # 获取模板类型和笔记/待办
            template_type = serializer.validated_data.get('template_type', '会议纪要')
            notes = serializer.validated_data.get('notes', [])
            todos = serializer.validated_data.get('todos', [])
            
            # 创建录音记录
            from django.utils import timezone
            recording = MeetingRecording.objects.create(
                repository_id=serializer.validated_data['repository_id'],
                meeting_title=serializer.validated_data['meeting_title'],
                meeting_date=serializer.validated_data.get('meeting_date') or timezone.now(),
                participants=serializer.validated_data.get('participants', ''),
                audio_file=file_path,
                audio_file_original_name=audio_file.name,
                file_size=audio_file.size,
                status=RecordingStatus.UPLOADED,
                created_by=request.user if request.user.is_authenticated else None
            )
            
            # 异步处理音频，传递模板类型和笔记/待办
            process_audio_task.delay(
                recording.id,
                template_type=template_type,
                notes=notes,
                todos=todos
            )
            
            return Response({
                'recording_id': recording.id,
                'status': 'processing',
                'template_type': template_type,
                'message': f'音频上传成功，正在生成{template_type}...'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error uploading recording: {str(e)}")
            return Response({
                'error': f'上传失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecordingAudioPlayView(APIView):
    """播放录音API"""
    
    def get(self, request, pk):
        recording = get_object_or_404(MeetingRecording, pk=pk)
        
        try:
            # 从存储中获取文件
            if default_storage.exists(recording.audio_file):
                audio_file = default_storage.open(recording.audio_file, 'rb')
                response = HttpResponse(audio_file.read(), content_type='audio/mpeg')
                response['Content-Disposition'] = f'inline; filename="{recording.audio_file_original_name}"'
                return response
            else:
                return Response(
                    {'error': '音频文件不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error playing audio: {str(e)}")
            return Response(
                {'error': f'播放失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SummaryListView(generics.ListAPIView):
    """纪要列表API"""
    serializer_class = MeetingSummarySerializer
    
    def get_queryset(self):
        queryset = MeetingSummary.objects.select_related(
            'recording', 'repository'
        ).prefetch_related('opinions').all()
        
        # 筛选条件
        repository_id = self.request.query_params.get('repository_id')
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        
        return queryset.order_by('-generated_at')


class SummaryDetailView(generics.RetrieveAPIView):
    """纪要详情API"""
    serializer_class = MeetingSummarySerializer
    
    def get_queryset(self):
        return MeetingSummary.objects.select_related(
            'recording', 'repository'
        ).prefetch_related('opinions', 'recording__transcripts').all()


class GenerateSummaryView(APIView):
    """生成会议纪要"""
    
    def post(self, request, recording_id):
        recording = get_object_or_404(MeetingRecording, pk=recording_id)
        
        if recording.status != RecordingStatus.COMPLETED:
            return Response(
                {'error': '转写尚未完成，请稍后再试'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SummaryGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        force_regenerate = serializer.validated_data.get('force_regenerate', False)
        template_type = serializer.validated_data.get('template_type', '会议纪要')
        
        # 检查是否已有纪要
        if hasattr(recording, 'summary') and not force_regenerate:
            return Response({
                'summary_id': recording.summary.id,
                'status': 'already_exists',
                'message': '纪要已存在'
            })
        
        # 异步生成纪要，传递模板类型
        task = generate_summary_task.delay(
            recording.id,
            template_type=template_type,
            notes=[],
            todos=[]
        )
        
        return Response({
            'task_id': task.id,
            'status': 'generating',
            'template_type': template_type,
            'message': f'{template_type}生成中，请稍后查看'
        })


class ExportSummaryView(APIView):
    """导出纪要文档"""
    
    def get(self, request, pk):
        summary = get_object_or_404(MeetingSummary, pk=pk)
        format_type = request.query_params.get('format', 'markdown')
        
        if format_type not in ['markdown', 'pdf', 'docx']:
            return Response(
                {'error': '不支持的格式，仅支持: markdown, pdf, docx'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查文件是否已存在
        file_field_map = {
            'markdown': summary.markdown_file,
            'pdf': summary.pdf_file,
            'docx': summary.docx_file
        }
        
        existing_file = file_field_map.get(format_type)
        
        if existing_file and default_storage.exists(existing_file):
            # 返回已存在的文件
            file_obj = default_storage.open(existing_file, 'rb')
            content_type_map = {
                'markdown': 'text/markdown',
                'pdf': 'application/pdf',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            
            response = HttpResponse(file_obj.read(), content_type=content_type_map[format_type])
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(existing_file)}"'
            return response
        
        # 异步生成文档
        task = export_document_task.delay(summary.id, format_type)
        
        return Response({
            'task_id': task.id,
            'status': 'generating',
            'message': f'{format_type.upper()}文档生成中，请稍后下载'
        })
    
    def post(self, request, pk):
        """检查导出任务状态"""
        summary = get_object_or_404(MeetingSummary, pk=pk)
        format_type = request.data.get('format', 'markdown')
        
        # 这里应该检查Celery任务状态，暂时返回默认状态
        # 实际使用时可以使用 celery.result.AsyncResult(task_id)
        return Response({
            'status': 'generating',
            'message': '文档正在生成中...'
        })


class OpinionListView(generics.ListAPIView):
    """评审意见列表API"""
    serializer_class = ReviewOpinionSerializer
    
    def get_queryset(self):
        queryset = ReviewOpinion.objects.select_related(
            'summary', 'speaker', 'transcript'
        ).all()
        
        # 筛选条件
        summary_id = self.request.query_params.get('summary_id')
        if summary_id:
            queryset = queryset.filter(summary_id=summary_id)
        
        opinion_type = self.request.query_params.get('opinion_type')
        if opinion_type:
            queryset = queryset.filter(opinion_type=opinion_type)
        
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        return queryset.order_by('-created_at')


class OpinionDetailView(generics.RetrieveUpdateAPIView):
    """评审意见详情API"""
    serializer_class = ReviewOpinionSerializer
    
    def get_queryset(self):
        return ReviewOpinion.objects.select_related('summary', 'speaker').all()
    
    def perform_update(self, serializer):
        """更新意见状态"""
        instance = serializer.save()
        # 如果标记为已解决，设置解决时间
        if instance.is_resolved and not instance.resolved_at:
            from django.utils import timezone
            instance.resolved_at = timezone.now()
            instance.save()


class RecordingStatusView(APIView):
    """获取录音处理状态"""
    
    def get(self, request, pk):
        recording = get_object_or_404(MeetingRecording, pk=pk)
        
        status_data = {
            'id': recording.id,
            'status': recording.status,
            'upload_time': recording.upload_time,
            'processed_at': recording.processed_at,
            'transcript_count': recording.transcript_count,
            'has_summary': hasattr(recording, 'summary'),
            'error_message': recording.error_message
        }
        
        return Response(status_data)


# ==================== 知识图谱视图 ====================

@login_required
def knowledge_graph(request):
    """知识图谱页面"""
    return render(request, 'meeting_assistant/knowledge_graph.html')


class KGSearchView(APIView):
    """知识图谱搜索API"""
    
    def get(self, request):
        keyword = request.query_params.get('keyword', '')
        entity_type = request.query_params.get('entity_type')
        
        if not keyword:
            return Response({
                'error': '请提供搜索关键词'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .services.kg_service import get_kg_service
            kg_service = get_kg_service()
            
            entities = kg_service.search_entities(keyword, entity_type)
            
            serializer_data = [{
                'id': entity.id,
                'name': entity.entity_name,
                'type': entity.entity_type,
                'user_id': entity.user_id,
                'repository_id': entity.repository_id,
                'meeting_id': entity.meeting_id,
                'metadata': entity.metadata
            } for entity in entities]
            
            return Response({
                'count': len(serializer_data),
                'results': serializer_data
            })
            
        except Exception as e:
            logger.error(f"知识图谱搜索失败: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KGEntityDetailView(APIView):
    """知识图谱实体详情API"""
    
    def get(self, request, entity_id):
        try:
            from .services.kg_service import get_kg_service
            kg_service = get_kg_service()
            
            entity = get_object_or_404(KnowledgeEntity, pk=entity_id)
            
            # 获取关系
            relations = kg_service.get_entity_relations(entity_id)
            
            # 获取相关会议
            related_meetings = kg_service.get_related_meetings(entity_id)
            
            # 获取子图
            graph = kg_service.get_entity_graph(entity_id, depth=2)
            
            return Response({
                'entity': {
                    'id': entity.id,
                    'name': entity.entity_name,
                    'type': entity.entity_type,
                    'user_id': entity.user_id,
                    'repository_id': entity.repository_id,
                    'meeting_id': entity.meeting_id,
                    'metadata': entity.metadata,
                    'confidence': entity.confidence,
                    'created_at': entity.created_at
                },
                'relations': [{
                    'id': rel.id,
                    'source': rel.source.entity_name,
                    'source_id': rel.source_id,
                    'target': rel.target.entity_name,
                    'target_id': rel.target_id,
                    'type': rel.relation_type,
                    'properties': rel.properties,
                    'confidence': rel.confidence
                } for rel in relations],
                'related_meetings': [{
                    'id': meeting.id,
                    'title': meeting.meeting_title,
                    'date': meeting.meeting_date,
                    'repository': meeting.repository.name
                } for meeting in related_meetings],
                'graph': graph
            })
            
        except Exception as e:
            logger.error(f"获取实体详情失败: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)