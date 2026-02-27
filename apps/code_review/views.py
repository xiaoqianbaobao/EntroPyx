from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class CodeReviewViewSet(viewsets.ModelViewSet):
    """代码评审视图集"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.code_review.models import CodeReview
        return CodeReview.objects.all().order_by('-created_at')
        
    def get_serializer_class(self):
        from apps.code_review.serializers import CodeReviewSerializer
        return CodeReviewSerializer
    
    @action(detail=False, methods=['post'])
    def manual_trigger(self, request):
        """
        手动触发评审

        POST /api/v1/code-review/manual-trigger/

        请求体:
        {
            "repository_id": 1,
            "branch": "master",
            "all_branches": false
        }
        """
        from apps.code_review.models import ReviewTask, TaskStatus, TriggerMode
        from apps.code_review.tasks import code_review_task
        from apps.repository.models import Repository

        repository_id = request.data.get('repository_id')
        branch = request.data.get('branch', 'master')
        all_branches = request.data.get('all_branches', False)

        if not repository_id:
            return Response(
                {'error': 'repository_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 生成任务追踪ID
        task_id = f"manual_{repository_id}_{branch}_{timezone.now().strftime('%Y%m%d%H%M%S')}"

        # 创建任务记录
        repository = Repository.objects.get(id=repository_id)
        task = ReviewTask.objects.create(
            task_id=task_id,
            repository=repository,
            branch=branch,
            status=TaskStatus.PENDING,
            trigger_mode=TriggerMode.MANUAL,
            triggered_by=request.user,
            current_step='任务已创建，等待执行...'
        )

        # 在开发环境中同步执行，生产环境中异步执行
        from django.conf import settings
        if settings.DEBUG:
            # 开发环境：同步执行
            try:
                code_review_task(
                    repository_id=repository_id,
                    branch=branch,
                    task_id=task_id,
                    all_branches=all_branches,
                    trigger_mode='MANUAL',
                    triggered_by_id=request.user.id
                )
            except Exception as e:
                logger.error(f"代码评审任务执行失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            # 生产环境：异步执行
            code_review_task.delay(
                repository_id=repository_id,
                branch=branch,
                task_id=task_id,
                all_branches=all_branches,
                trigger_mode='MANUAL',
                triggered_by_id=request.user.id
            )

        return Response({
            'code': 0,
            'message': '评审任务已触发',
            'data': {
                'task_id': task_id
            }
        })
    
    @action(detail=False, methods=['post'], url_path='cancel_task')
    def cancel_task(self, request):
        """
        取消评审任务

        POST /api/v1/code-review/reviews/cancel_task/

        请求体:
        {
            "task_id": "xxx"
        }
        """
        from apps.code_review.models import ReviewTask, TaskStatus
        
        task_id = request.data.get('task_id')
        if not task_id:
            return Response(
                {'error': 'task_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task = ReviewTask.objects.get(task_id=task_id)
            
            # 只能取消运行中或等待中的任务
            if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.CLONING, 
                                  TaskStatus.FETCHING, TaskStatus.DIFFING, TaskStatus.REVIEWING]:
                return Response(
                    {'error': '只能取消运行中或等待中的任务'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 更新任务状态为已取消
            task.status = TaskStatus.CANCELLED
            task.current_step = '任务已被用户取消'
            task.progress = task.progress  # 保持当前进度
            task.save(update_fields=['status', 'current_step', 'updated_at'])
            
            logger.info(f"代码评审任务已取消: task_id={task_id}")
            
            return Response({
                'code': 0,
                'message': '任务已取消'
            })
        except ReviewTask.DoesNotExist:
            return Response(
                {'error': '任务不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='task_status')
    def task_status(self, request):
        """
        查询任务状态

        GET /api/v1/code-review/reviews/task_status/?task_id=xxx
        """
        from apps.code_review.models import ReviewTask

        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {'error': 'task_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            task = ReviewTask.objects.get(task_id=task_id)
            return Response({
                'code': 0,
                'data': {
                    'task_id': task.task_id,
                    'repository_name': task.repository.name,
                    'branch': task.branch,
                    'status': task.status,
                    'status_display': task.get_status_display(),
                    'current_step': task.current_step,
                    'progress': task.progress,
                    'total_commits': task.total_commits,
                    'processed_commits': task.processed_commits,
                    'high_risk_count': task.high_risk_count,
                    'medium_risk_count': task.medium_risk_count,
                    'low_risk_count': task.low_risk_count,
                    'dingtalk_notified_count': task.dingtalk_notified_count,
                    'error_message': task.error_message,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'duration_seconds': int(task.duration) if task.duration else 0,
                    'is_completed': task.is_completed
                }
            })
        except ReviewTask.DoesNotExist:
            return Response(
                {'code': 1, 'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='tasks')
    def tasks(self, request):
        """
        获取任务列表

        GET /api/v1/code-review/reviews/tasks/
        """
        from apps.code_review.models import ReviewTask

        tasks = ReviewTask.objects.select_related('repository').order_by('-created_at')[:50]
        return Response({
            'code': 0,
            'data': [
                {
                    'task_id': task.task_id,
                    'repository_name': task.repository.name,
                    'branch': task.branch,
                    'status': task.status,
                    'status_display': task.get_status_display(),
                    'progress': task.progress,
                    'total_commits': task.total_commits,
                    'processed_commits': task.processed_commits,
                    'high_risk_count': task.high_risk_count,
                    'medium_risk_count': task.medium_risk_count,
                    'low_risk_count': task.low_risk_count,
                    'created_at': task.created_at.isoformat() if task.created_at else None
                }
                for task in tasks
            ]
        })
    
    @action(detail=False, methods=['post'])
    def webhook_trigger(self, request):
        """
        Webhook触发评审（GitLab/GitHub推送时触发）
        
        POST /api/v1/code-review/webhook-trigger/
        
        请求体:
        {
            "repository_id": 1,
            "commit_hash": "abc123...",
            "branch": "master",
            "author": "张三",
            "author_email": "zhangsan@example.com",
            "commit_message": "fix bug"
        }
        """
        from apps.code_review.tasks import webhook_review_task
        
        repository_id = request.data.get('repository_id')
        commit_hash = request.data.get('commit_hash')
        branch = request.data.get('branch', 'master')
        author = request.data.get('author', '')
        author_email = request.data.get('author_email', '')
        commit_message = request.data.get('commit_message', '')
        
        if not repository_id or not commit_hash:
            return Response(
                {'error': 'repository_id and commit_hash are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 触发评审任务
        result = webhook_review_task.delay(
            repository_id=repository_id,
            commit_hash=commit_hash,
            branch=branch,
            author=author,
            author_email=author_email,
            commit_message=commit_message
        )
        
        return Response({
            'message': 'Webhook评审任务已触发',
            'status': result.get('status')
        })


    
    @action(detail=True, methods=['post'], url_path='feedback')
    def feedback(self, request, pk=None):
        """
        提交代码评审反馈
        """
        try:
            review = self.get_object()
            
            # 获取反馈状态
            feedback_status = request.data.get('feedback_status')
            comment = request.data.get('comment', '')
            
            if not feedback_status:
                return Response(
                    {'error': 'feedback_status is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from apps.code_review.models import FeedbackStatus
            # 验证反馈状态
            # 使用 FeedbackStatus.values 获取所有有效值
            valid_statuses = FeedbackStatus.values
            if feedback_status not in valid_statuses:
                return Response(
                    {'error': f'Invalid feedback_status. Valid values: {valid_statuses}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 更新反馈信息
            review.feedback_status = feedback_status
            review.feedback_comment = comment
            review.feedback_by = request.user
            review.feedback_at = timezone.now()
            review.save()
            
            logger.info(f"代码评审反馈已提交: review_id={review.id}, status={feedback_status}")
            
            return Response({
                'code': 0,
                'message': '反馈已提交',
                'data': {
                    'review_id': review.id,
                    'feedback_status': feedback_status,
                    'feedback_by': request.user.username,
                    'feedback_at': review.feedback_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"提交代码评审反馈失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': f'提交失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ScheduledReviewConfigViewSet(viewsets.ModelViewSet):
    """定时评审配置视图集"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.code_review.models import ScheduledReviewConfig
        return ScheduledReviewConfig.objects.all()
    
    def get_serializer_class(self):
        from apps.code_review.serializers import ScheduledReviewConfigSerializer
        return ScheduledReviewConfigSerializer
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """立即运行定时任务"""
        from apps.code_review.tasks import scheduled_review_task
        
        config = self.get_object()
        
        if not config.is_active:
            return Response(
                {'error': 'Config is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 触发定时任务
        scheduled_review_task.delay(config.id)
        
        return Response({
            'message': f'定时任务 {config.name} 已触发'
        })
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """启用/禁用定时任务"""
        config = self.get_object()
        config.is_active = not config.is_active
        config.save()
        
        return Response({
            'message': f'定时任务已{"启用" if config.is_active else "禁用"}',
            'is_active': config.is_active
        })



class RealtimeMonitorConfigViewSet(viewsets.ModelViewSet):
    """实时监控配置视图集"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.code_review.models import RealtimeMonitorConfig
        return RealtimeMonitorConfig.objects.all()
    
    def get_serializer_class(self):
        from apps.code_review.serializers import RealtimeMonitorConfigSerializer
        return RealtimeMonitorConfigSerializer
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """启用/禁用实时监控"""
        config = self.get_object()
        config.is_active = not config.is_active
        config.save()
        
        return Response({
            'message': f'实时监控已{"启用" if config.is_active else "禁用"}',
            'is_active': config.is_active
        })
    
    @action(detail=True, methods=['post'])
    def check_now(self, request, pk=None):
        """立即执行实时监控检查"""
        from apps.code_review.tasks import realtime_monitor_task
        
        config = self.get_object()
        
        if not config.is_active:
            return Response(
                {'error': 'Config is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取监控的分支列表
        branches = config.branches.split(',') if config.branches else ['master']
        
        # 触发监控任务
        for branch in branches:
            realtime_monitor_task.delay(
                config_id=config.id,
                branch=branch.strip()
            )
        
        return Response({
            'message': f'实时监控检查已触发: {config.repository.name}',
            'branches': branches
        })
