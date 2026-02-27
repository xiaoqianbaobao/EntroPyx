from rest_framework import viewsets, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Repository
from .serializers import RepositorySerializer, RepositoryCreateSerializer
from apps.core.mixins import (
    CreateModelMixin, UpdateModelMixin, ListModelMixin,
    RetrieveModelMixin, DestroyModelMixin
)


class RepositoryViewSet(
    CreateModelMixin, UpdateModelMixin, ListModelMixin,
    RetrieveModelMixin, DestroyModelMixin, viewsets.GenericViewSet
):
    """仓库视图集"""
    queryset = Repository.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RepositoryCreateSerializer
        return RepositorySerializer
    
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
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)
        return Response({
            'code': 0,
            'message': '创建成功',
            'data': RepositorySerializer(instance).data
        }, status=status.HTTP_201_CREATED)
    
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


class RepositorySyncView(views.APIView):
    """仓库同步视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """手动触发仓库同步"""
        try:
            repository = Repository.objects.get(pk=pk)
            # 这里会触发Celery任务进行仓库同步
            from apps.code_review.tasks import code_review_task
            code_review_task.delay(repository.id, 'master')
            return Response({
                'code': 0,
                'message': '同步任务已触发',
                'data': {'repository_id': repository.id}
            })
        except Repository.DoesNotExist:
            return Response({
                'code': 404,
                'message': '仓库不存在'
            }, status=status.HTTP_404_NOT_FOUND)


class RepositoryBranchesView(views.APIView):
    """仓库分支视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """获取仓库分支列表"""
        try:
            repository = Repository.objects.get(pk=pk)
            from .services.git_service import GitService
            git_service = GitService(repository)
            branches = git_service.get_all_branches()
            return Response({
                'code': 0,
                'message': 'success',
                'data': {'branches': branches}
            })
        except Repository.DoesNotExist:
            return Response({
                'code': 404,
                'message': '仓库不存在'
            }, status=status.HTTP_404_NOT_FOUND)
