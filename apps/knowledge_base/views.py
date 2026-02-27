"""
知识库视图
Knowledge Base Views
"""
import os
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import (
    KnowledgeDocument,
    KnowledgeEntity,
    KnowledgeRelation,
    KnowledgeQuery
)
from .serializers import (
    KnowledgeDocumentSerializer,
    KnowledgeQuerySerializer,
    KnowledgeEntitySerializer,
    KnowledgeRelationSerializer
)
from .services.knowledge_processor import KnowledgeProcessor

logger = logging.getLogger(__name__)


# ==================== 页面视图 ====================

@login_required
def knowledge_base_list(request):
    """知识库列表页面"""
    documents = KnowledgeDocument.objects.all().order_by('-created_at')
    return render(request, 'knowledge_base/list.html', {
        'documents': documents
    })


@login_required
def knowledge_base_detail(request, pk):
    """知识库详情页面"""
    document = get_object_or_404(KnowledgeDocument, pk=pk)
    return render(request, 'knowledge_base/detail.html', {
        'document': document
    })


@login_required
def knowledge_base_upload(request):
    """知识库上传页面"""
    return render(request, 'knowledge_base/upload.html')


@login_required
def knowledge_base_chat(request):
    """知识库问答页面"""
    documents = KnowledgeDocument.objects.filter(status='completed')
    return render(request, 'knowledge_base/chat.html', {
        'documents': documents
    })


# ==================== API视图 ====================

class KnowledgeDocumentListView(generics.ListAPIView):
    """知识库文档列表API"""
    serializer_class = KnowledgeDocumentSerializer
    
    def get_queryset(self):
        return KnowledgeDocument.objects.all().order_by('-created_at')


class KnowledgeDocumentDetailView(generics.RetrieveAPIView):
    """知识库文档详情API"""
    serializer_class = KnowledgeDocumentSerializer
    
    def get_queryset(self):
        return KnowledgeDocument.objects.all()


@method_decorator(csrf_exempt, name='dispatch')
class KnowledgeDocumentUploadView(APIView):
    """上传知识库文档"""
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # 获取上传的文件
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return Response(
                    {'error': '请上传文件'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 获取文件信息
            file_name = uploaded_file.name
            file_type = file_name.split('.')[-1] if '.' in file_name else ''
            
            # 保存文件
            file_path = default_storage.save(
                f'knowledge_docs/{file_name}',
                uploaded_file
            )
            
            # 处理文档
            processor = KnowledgeProcessor()
            result = processor.process_document(
                default_storage.path(file_path),
                file_name,
                file_type
            )
            
            if not result['success']:
                # 删除已保存的文件
                default_storage.delete(file_path)
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 创建文档记录
            document = KnowledgeDocument.objects.create(
                title=file_name,
                file=file_path,
                file_name=file_name,
                file_type=file_type,
                file_size=uploaded_file.size,
                content=result['content'],
                structured_data=result['structured_data'],
                status='completed',
                section_count=len(result['structured_data'].get('sections', [])),
                keyword_count=len(result['structured_data'].get('keywords', [])),
                entity_count=len(result['structured_data'].get('entities', [])),
                processed_at=timezone.now()
            )
            
            logger.info(f"知识库文档上传成功: {file_name}")
            
            return Response({
                'document_id': document.id,
                'status': 'success',
                'message': '文档上传成功'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"上传知识库文档失败: {str(e)}")
            return Response(
                {'error': f'上传失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KnowledgeDocumentDeleteView(APIView):
    """删除知识库文档"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            document = get_object_or_404(KnowledgeDocument, pk=pk)
            
            # 删除文件
            if default_storage.exists(document.file):
                default_storage.delete(document.file)
            
            # 删除记录
            document.delete()
            
            logger.info(f"知识库文档删除成功: {pk}")
            
            return Response({
                'status': 'success',
                'message': '文档删除成功'
            })
            
        except Exception as e:
            logger.error(f"删除知识库文档失败: {str(e)}")
            return Response(
                {'error': f'删除失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KnowledgeDocumentSearchView(APIView):
    """搜索知识库文档"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        document_id = request.query_params.get('document_id')
        
        if not query:
            return Response(
                {'error': '请提供搜索关键词'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 构建搜索查询
            from django.db.models import Q
            
            # 搜索文档
            documents = KnowledgeDocument.objects.all()
            if document_id:
                documents = documents.filter(pk=document_id)
            
            # 执行搜索
            results = []
            for document in documents:
                if query.lower() in document.content.lower():
                    # 提取匹配的片段
                    content = document.content
                    start = content.lower().find(query.lower())
                    if start >= 0:
                        # 提取前后各50个字符
                        snippet_start = max(0, start - 50)
                        snippet_end = min(len(content), start + len(query) + 50)
                        snippet = content[snippet_start:snippet_end]
                        
                        results.append({
                            'document_id': document.id,
                            'document_title': document.title,
                            'snippet': snippet,
                            'position': start
                        })
            
            return Response({
                'count': len(results),
                'results': results
            })
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {str(e)}")
            return Response(
                {'error': f'搜索失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KnowledgeQueryView(APIView):
    """知识库查询API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = KnowledgeQuerySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            query_text = serializer.validated_data['query_text']
            
            # 这里应该调用DeepSeek API进行智能问答
            # 暂时使用简单的关键词匹配
            response_text = self._simple_query(query_text)
            
            # 创建查询记录
            query = KnowledgeQuery.objects.create(
                query_text=query_text,
                response_text=response_text,
                confidence_score=0.7
            )
            
            logger.info(f"知识库查询成功: {query_text}")
            
            return Response({
                'query_id': query.id,
                'response': response_text,
                'confidence_score': 0.7
            })
            
        except Exception as e:
            logger.error(f"知识库查询失败: {str(e)}")
            return Response(
                {'error': f'查询失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _simple_query(self, query_text):
        """简单的查询处理（后续应该集成DeepSeek API）"""
        # 这里应该集成DeepSeek API进行智能问答
        # 暂时返回模拟结果
        return f"这是对'{query_text}'的智能回答。由于当前未配置DeepSeek API，这是模拟结果。请在settings.py中配置DEEPSEEK_API_KEY以启用智能问答功能。"


class KnowledgeEntityListView(generics.ListAPIView):
    """知识实体列表API"""
    serializer_class = KnowledgeEntitySerializer
    
    def get_queryset(self):
        return KnowledgeEntity.objects.all().order_by('name')


class KnowledgeRelationListView(generics.ListAPIView):
    """知识关系列表API"""
    serializer_class = KnowledgeRelationSerializer
    
    def get_queryset(self):
        return KnowledgeRelation.objects.all().order_by('relation_type')