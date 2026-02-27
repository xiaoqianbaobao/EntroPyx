from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
import uuid
from .models import TestCase, TestExecution, TestReport, TestCaseGenerationTask, CasePriority, CaseType, GenerationTaskStatus
from .serializers import TestCaseSerializer, TestReportSerializer, TestCaseGenerationTaskSerializer


class GenerateTestCasesView(views.APIView):
    # ... 保持不变 ...
    """AI生成测试用例视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """查询生成任务状态"""
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({
                'code': 400,
                'message': '请提供task_id参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = TestCaseGenerationTask.objects.get(task_id=task_id)
            serializer = TestCaseGenerationTaskSerializer(task)
            return Response({
                'code': 0,
                'message': 'success',
                'data': serializer.data
            })
        except TestCaseGenerationTask.DoesNotExist:
            return Response({
                'code': 404,
                'message': '任务不存在'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request):
        """AI生成测试用例"""
        prd_review_id = request.data.get('prd_review_id')
        code_review_id = request.data.get('code_review_id')
        
        if not prd_review_id and not code_review_id:
            return Response({
                'code': 400,
                'message': '请提供PRD评审ID或代码评审ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 触发异步生成任务
        from .tasks import generate_test_cases_task
        
        # 为了调试，暂时同步执行任务
        # task = generate_test_cases_task.delay(
        #     prd_review_id=prd_review_id,
        #     code_review_id=code_review_id,
        #     user_id=request.user.id
        # )
        
        # 临时任务ID
        temp_task_id = str(uuid.uuid4())
        
        # 创建任务状态记录
        generation_task = TestCaseGenerationTask.objects.create(
            task_id=temp_task_id,
            status=GenerationTaskStatus.PENDING,
            prd_review_id=prd_review_id,
            code_review_id=code_review_id,
            created_by=request.user
        )
        
        # 同步调用任务逻辑（模拟request.id）
        try:
            # 这里的trick是我们需要模拟Celery task的request.id
            # 但实际上我们直接修改tasks.py可能更方便，或者在这里简单封装
            
            # 为了让任务能够找到记录，我们需要更新一下task_id
            # 但这里我们采用更简单的方法：修改tasks.py让它支持传入 task_id 参数
            
            # 暂时通过线程来异步执行，避免阻塞主线程太久导致前端超时，
            # 同时也能绕过 Celery 的问题
            import threading
            
            def run_sync_task():
                # 重新获取 task，防止线程安全问题
                from .tasks import generate_test_cases_task
                
                # 直接调用任务函数，不传 self (因为不是通过 Celery 调用)
                # 注意：这里需要修改 generate_test_cases_task 的定义或调用方式
                # 但由于它被 @shared_task 装饰，直接调用时它不会接收 self 参数
                
                generate_test_cases_task(
                    prd_review_id=prd_review_id,
                    code_review_id=code_review_id,
                    user_id=request.user.id,
                    task_id=temp_task_id
                )
                
            threading.Thread(target=run_sync_task).start()
            
        except Exception as e:
            print(f"Error starting thread: {e}")
        
        serializer = TestCaseGenerationTaskSerializer(generation_task)
        return Response({
            'code': 0,
            'message': '测试用例生成中',
            'data': serializer.data
        })


class TestCaseViewSet(viewsets.ModelViewSet):
    """测试用例视图集"""
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        prd_review_id = self.request.query_params.get('prd_review_id')
        case_type = self.request.query_params.get('type')
        priority = self.request.query_params.get('priority')
        
        if prd_review_id:
            queryset = queryset.filter(prd_review_id=prd_review_id)
        if case_type:
            queryset = queryset.filter(type=case_type)
        if priority:
            queryset = queryset.filter(priority=priority)
        
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
        # 生成用例编号
        last_case = TestCase.objects.order_by('-id').first()
        next_id = (last_case.id + 1) if last_case else 1
        case_id = f"TC{next_id:04d}"
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            case_id=case_id,
            created_by=request.user
        )
        
        return Response({
            'code': 0,
            'message': '创建成功',
            'data': TestCaseSerializer(instance).data
        }, status=status.HTTP_201_CREATED)
        
    def retrieve(self, request, *args, **kwargs):
        """
        获取测试用例详情
        重写默认的 retrieve 方法，返回统一的格式 {code: 0, data: ...}
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
        
    def update(self, request, *args, **kwargs):
        """更新测试用例（包括Dubbo配置）"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'code': 0,
            'message': '更新成功',
            'data': serializer.data
        })
        
    @action(detail=False, methods=['post'], url_path='batch_delete')
    def batch_delete(self, request):
        """批量删除测试用例"""
        case_ids = request.data.get('ids', [])
        
        if not case_ids:
            return Response({
                'code': 400,
                'message': '请选择要删除的测试用例'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # 过滤存在的ID
            cases = TestCase.objects.filter(id__in=case_ids)
            count = cases.count()
            
            # 执行删除
            cases.delete()
            
            return Response({
                'code': 0,
                'message': f'成功删除 {count} 个测试用例',
                'data': {
                    'deleted_count': count
                }
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'删除失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='batch_update')
    def batch_update(self, request):
        """批量更新测试用例（支持批量配置Dubbo接口和参数）"""
        case_ids = request.data.get('case_ids', [])
        update_data = request.data.get('update_data', {})
        
        if not case_ids:
            return Response({
                'code': 400,
                'message': '请选择要更新的测试用例'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not update_data:
             return Response({
                'code': 400,
                'message': '请提供更新数据'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # 过滤允许批量更新的字段
        allowed_fields = ['dubbo_service', 'dubbo_method', 'dubbo_params', 'priority', 'type']
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_data:
             return Response({
                'code': 400,
                'message': '没有有效的更新字段'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # 执行批量更新
        updated_count = TestCase.objects.filter(id__in=case_ids).update(**filtered_data)
        
        return Response({
            'code': 0,
            'message': f'成功更新 {updated_count} 个测试用例',
            'data': {
                'updated_count': updated_count
            }
        })


class TestReportViewSet(viewsets.ReadOnlyModelViewSet):
    """测试报告视图集"""
    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        batch_id = self.request.query_params.get('batch_id')
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
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
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })


class TestExecutionView(views.APIView):
    """测试执行视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """批量执行测试"""
        case_ids = request.data.get('case_ids', [])
        if not case_ids:
            return Response({
                'code': 400,
                'message': '请选择要执行的测试用例'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 生成批次号
        batch_id = f"BATCH_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        # 触发异步执行任务
        from .tasks import execute_test_cases_task
        execute_test_cases_task.delay(case_ids, batch_id, request.user.id)
        
        return Response({
            'code': 0,
            'message': '测试执行中',
            'data': {
                'batch_id': batch_id,
                'case_count': len(case_ids)
            }
        })
