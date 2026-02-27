from rest_framework import viewsets, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import PRDReview, ReviewStatus
from .serializers import PRDReviewSerializer, PRDReviewCreateSerializer


class PRDReviewViewSet(viewsets.ModelViewSet):
    """PRD评审视图集"""
    queryset = PRDReview.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PRDReviewCreateSerializer
        return PRDReviewSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        review_status = self.request.query_params.get('review_status')
        created_by = self.request.query_params.get('created_by')
        
        if review_status:
            queryset = queryset.filter(review_status=review_status)
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data,
            'total': queryset.count()
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)
        
        # 将PRD文档添加到知识库
        from apps.knowledge_base.models import KnowledgeDocument
        from apps.knowledge_base.tasks import embed_document_task
        
        knowledge_doc = KnowledgeDocument.objects.create(
            title=f"PRD: {instance.title}",
            file=instance.file,
            file_type='prd',
            file_size=instance.file_size,
            prd_review=instance,
            created_by=request.user
        )
        
        # 触发向量化任务
        embed_document_task.delay(knowledge_doc.id)
        
        # 注意：不再自动触发评审任务，需由前端单独调用触发
        # from .tasks import prd_review_task
        # prd_review_task.delay(instance.id)
        
        return Response({
            'code': 0,
            'message': '上传成功，请点击AI评审开始分析',
            'data': PRDReviewSerializer(instance).data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'code': 0,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'code': 0,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)

    from rest_framework.decorators import action
    @action(detail=False, methods=['post'], url_path='batch_delete')
    def batch_delete(self, request):
        """批量删除PRD文档"""
        prd_ids = request.data.get('ids', [])
        
        if not prd_ids:
            return Response({
                'code': 400,
                'message': '请选择要删除的PRD文档'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # 过滤存在的ID
            prds = PRDReview.objects.filter(id__in=prd_ids)
            count = prds.count()
            
            # 执行删除
            prds.delete()
            
            return Response({
                'code': 0,
                'message': f'成功删除 {count} 个PRD文档',
                'data': {
                    'deleted_count': count
                }
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'删除失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def update_content(self, request, pk=None):
        """更新PRD文档内容"""
        instance = self.get_object()
        
        title = request.data.get('title')
        content = request.data.get('content')
        
        if title:
            instance.title = title
            
        if content:
            # 将内容写回文件
            # 注意：这会覆盖原文件，建议只对 Markdown/Text 文件开放
            # 简单实现：覆盖原文件内容
            try:
                # 确保是文本模式
                with instance.file.open('w') as f:
                    f.write(content)
            except Exception as e:
                return Response({
                    'code': 500,
                    'message': f'写入文件失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        instance.save()
        
        return Response({
            'code': 0,
            'message': '更新成功'
        })


class PRDReviewStartView(views.APIView):
    """手动触发AI评审视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            prd_review = PRDReview.objects.get(pk=pk)
        except PRDReview.DoesNotExist:
            return Response({
                'code': 404,
                'message': 'PRD文档不存在'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # 触发异步评审任务
        from .tasks import prd_review_task
        prd_review_task.delay(prd_review.id)
        
        return Response({
            'code': 0,
            'message': 'AI评审任务已启动',
            'data': {
                'id': prd_review.id,
                'status': 'PROCESSING'
            }
        })

class PRDReviewApproveView(views.APIView):
    """PRD评审通过视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """人工评审通过"""
        try:
            prd_review = PRDReview.objects.get(pk=pk)
        except PRDReview.DoesNotExist:
            return Response({
                'code': 404,
                'message': 'PRD评审记录不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        prd_review.review_status = request.data.get('status', ReviewStatus.APPROVED)
        prd_review.review_comment = request.data.get('comment', '')
        prd_review.reviewed_by = request.user
        prd_review.reviewed_at = timezone.now()
        prd_review.save()
        
        return Response({
            'code': 0,
            'message': '评审完成',
            'data': {
                'review_status': prd_review.review_status,
                'reviewed_at': prd_review.reviewed_at
            }
        })
