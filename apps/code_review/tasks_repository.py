"""
基于Repository配置的代码评审任务
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_all_realtime_monitors():
    """
    检查所有启用了实时监控的仓库，发现新提交后触发评审
    
    这个任务每分钟执行一次
    """
    from apps.repository.models import Repository
    from apps.repository.services.git_service import GitService
    from apps.code_review.models import CodeReview, ReviewTask, TaskStatus, TriggerMode
    from apps.code_review.tasks import code_review_task
    
    # 获取所有启用了实时监控的仓库
    repositories = Repository.objects.filter(
        is_active=True,
        enable_realtime_monitor=True
    )
    
    for repo in repositories:
        try:
            # 更新最后检查时间
            repo.save(update_fields=['updated_at'])
            
            git_service = GitService(repo)
            git_service.ensure_repo()
            
            # 获取监控的分支
            monitored_branches = repo.realtime_monitor_branches or [repo.review_branch]
            
            for branch in monitored_branches:
                # 获取最新的提交
                commits = git_service.get_today_commits(branch, all_branches=False)
                
                for commit in commits:
                    # 检查是否已经评审过
                    if CodeReview.objects.filter(
                        repository=repo,
                        commit_hash=commit['hash']
                    ).exists():
                        continue
                    
                    # 如果启用了自动评审，则触发评审任务
                    if repo.auto_review_on_new_commit:
                        task_id = f"realtime_{repo.id}_{branch}_{commit['hash'][:8]}"
                        code_review_task.delay(
                            repository_id=repo.id,
                            branch=branch,
                            task_id=task_id,
                            all_branches=False,
                            triggered_by_id=None,
                            trigger_mode=TriggerMode.REALTIME
                        )
                        
                        logger.info(f"实时监控触发评审: {repo.name} - {commit['hash'][:8]}")
        
        except Exception as e:
            logger.error(f"实时监控检查失败: {repo.name} - {str(e)}")


@shared_task
def run_scheduled_review_for_repository(repository_id: int):
    """
    为指定仓库执行定时评审
    
    Args:
        repository_id: 仓库ID
    """
    from apps.repository.models import Repository
    from apps.code_review.tasks import code_review_task, TriggerMode
    
    try:
        repo = Repository.objects.get(id=repository_id)
        
        if not repo.enable_scheduled_review or not repo.scheduled_review_cron:
            logger.warning(f"仓库 {repo.name} 未启用定时评审或未配置Cron表达式")
            return
        
        # 触发评审任务
        task_id = f"scheduled_{repo.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        code_review_task.delay(
            repository_id=repo.id,
            branch=repo.review_branch,
            task_id=task_id,
            all_branches=repo.review_all_branches,
            triggered_by_id=None,
            trigger_mode=TriggerMode.SCHEDULED
        )
        
        logger.info(f"定时评审任务已触发: {repo.name}")
    
    except Repository.DoesNotExist:
        logger.error(f"仓库不存在: {repository_id}")
    except Exception as e:
        logger.error(f"定时评审任务失败: {str(e)}")


@shared_task
def sync_scheduled_reviews():
    """
    同步定时评审配置到Celery Beat
    
    这个任务应该由Celery Beat调度，定期执行以更新定时任务配置
    """
    from apps.repository.models import Repository
    from celery import current_app
    
    # 获取所有启用了定时评审的仓库
    repositories = Repository.objects.filter(
        is_active=True,
        enable_scheduled_review=True
    ).exclude(scheduled_review_cron='')
    
    # 为每个仓库创建定时任务
    for repo in repositories:
        try:
            task_name = f'scheduled-review-{repo.id}'
            
            # 检查是否已经存在该任务
            if task_name in current_app.conf.beat_schedule:
                # 更新任务配置
                current_app.conf.beat_schedule[task_name]['schedule'] = repo.scheduled_review_cron
            else:
                # 创建新任务
                current_app.conf.beat_schedule[task_name] = {
                    'task': 'apps.code_review.tasks_repository.run_scheduled_review_for_repository',
                    'schedule': repo.scheduled_review_cron,
                    'args': (repo.id,),
                }
            
            logger.info(f"同步定时评审配置: {repo.name} - {repo.scheduled_review_cron}")
        
        except Exception as e:
            logger.error(f"同步定时评审配置失败: {repo.name} - {str(e)}")