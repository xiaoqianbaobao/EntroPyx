from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging
import uuid

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def code_review_task(self, repository_id: int, branch: str = 'master', task_id: str = None, 
                     all_branches: bool = False, trigger_mode: str = 'MANUAL', triggered_by_id: int = None):
    """
    代码评审任务

    Args:
        repository_id: 仓库ID
        branch: 分支名
        task_id: 任务追踪ID
        all_branches: 是否评审所有分支
        trigger_mode: 触发模式 (MANUAL/SCHEDULED/REALTIME/WEBHOOK)
        triggered_by_id: 触发人ID
    """
    from apps.repository.models import Repository
    from apps.repository.services.git_service import GitService
    from apps.code_review.models import CodeReview, ReviewTask, TaskStatus, TriggerMode
    from apps.code_review.services.ai_engine import AIReviewEngine
    from apps.core.services.dingtalk_service import DingTalkService
    
    task = None
    try:
        # 获取或创建任务记录
        if task_id:
            task = ReviewTask.objects.get(task_id=task_id)
            task.status = TaskStatus.RUNNING
            task.started_at = timezone.now()
            task.current_step = '开始评审任务...'
            task.save()
        
        # 1. 获取仓库配置
        repository = Repository.objects.get(id=repository_id)
        if task:
            task.current_step = f'准备评审仓库: {repository.name}'
            task.save()
        
        # 2. Git操作 - 克隆/更新仓库
        if task:
            task.status = TaskStatus.CLONING
            task.current_step = '正在克隆/更新仓库...'
            task.save()
        
        git_service = GitService(repository)
        git_service.ensure_repo()
        
        if task:
            task.current_step = '仓库准备完成'
            task.save()
        
        # 3. 获取今日提交
        if task:
            task.status = TaskStatus.FETCHING
            task.current_step = '正在获取提交记录...'
            task.save()
        
        commits = git_service.get_today_commits(branch, all_branches=all_branches)
        total_commits = len(commits)
        
        if task:
            task.total_commits = total_commits
            task.current_step = f'发现 {total_commits} 条待评审提交'
            task.save()
        
        logger.info(f"开始评审 {repository.name}, 发现 {total_commits} 条提交")
        
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        notified = 0
        
        for i, commit in enumerate(commits):
            commit_progress = int((i / total_commits) * 100) if total_commits > 0 else 0
            
            # 检查是否已评审
            if CodeReview.objects.filter(
                repository=repository,
                commit_hash=commit['hash']
            ).exists():
                if task:
                    task.increment_processed()
                    task.current_step = f'跳过已评审: {commit["hash"][:8]}'
                    task.save()
                continue
            
            # 4. 获取Diff
            if task:
                task.status = TaskStatus.DIFFING
                task.current_step = f'正在分析第 {i+1}/{total_commits} 条提交: {commit["hash"][:8]}'
                task.progress = commit_progress
                task.save()
            
            diff_content, files = git_service.get_diff_and_files(commit['hash'])
            
            # 5. AI评审
            if task:
                task.status = TaskStatus.REVIEWING
                task.current_step = f'正在AI评审: {commit["message"][:50]}...'
                task.save()
            
            ai_engine = AIReviewEngine()
            result = ai_engine.review(
                diff_content=diff_content,
                files=files,
                commit_message=commit['message'],
                commit_hash=commit['hash']
            )
            
            # 6. 保存评审记录
            if task:
                task.status = TaskStatus.SAVING
                task.current_step = f'正在保存评审结果: {commit["hash"][:8]}'
                task.save()

            # 统计代码行数
            lines_added = 0
            lines_deleted = 0
            for line in diff_content.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    lines_added += 1
                elif line.startswith('-') and not line.startswith('---'):
                    lines_deleted += 1

            # 检查记录是否已存在
            try:
                review = CodeReview.objects.get(
                    repository=repository,
                    commit_hash=commit['hash']
                )
                created = False
            except CodeReview.DoesNotExist:
                # 创建新记录
                review = CodeReview.objects.create(
                    repository=repository,
                    commit_hash=commit['hash'],
                    branch=commit.get('branch', branch),  # 使用 commit 实际所在的分支
                    commit_message=commit['message'],
                    author=commit['author'],
                    author_email=commit['author_email'],
                    commit_time=commit['committed_datetime'],
                    trigger_mode=trigger_mode,
                    triggered_by_id=triggered_by_id,
                    risk_score=result['risk_score'],
                    risk_level=result['risk_level'],
                    ai_review_content=result.get('ai_content', ''),
                    changed_files=files,
                    diff_content=diff_content,
                    review_points=result.get('review_points', []),
                    lines_added=lines_added,
                    lines_deleted=lines_deleted,
                    lines_changed=lines_added + lines_deleted
                )
                created = True

            # 如果记录已存在，跳过后续处理
            if not created:
                if task:
                    task.increment_processed()
                    # 更新进度显示
                    task.current_step = f'评审完成! 高风险:{high_risk} 中风险:{medium_risk} 低风险:{low_risk}'
                    task.save()
                    logger.info(f"评审记录已存在，跳过: {commit['hash'][:8]}")
                continue
            
            # 统计风险等级
            if result['risk_level'] == 'HIGH':
                high_risk += 1
            elif result['risk_level'] == 'MEDIUM':
                medium_risk += 1
            else:
                low_risk += 1
            
            # 更新task统计信息
            if task:
                task.current_step = f'评审完成! 高风险:{high_risk} 中风险:{medium_risk} 低风险:{low_risk}'
                task.save()
            
            # 7. 钉钉推送
            if repository.dingtalk_webhook:
                if task:
                    task.status = TaskStatus.NOTIFYING
                    task.current_step = f'正在发送钉钉通知: {commit["hash"][:8]}'
                    task.save()
                
                dingtalk = DingTalkService(
                    webhook=repository.dingtalk_webhook,
                    secret=repository.dingtalk_secret
                )
                
                success = dingtalk.send_review_notification({
                    'repository_name': repository.name,
                    'branch': review.branch,  # 使用实际存储的分支
                    'commit_hash': commit['hash'],
                    'author': commit['author'],
                    'commit_message': commit['message'],
                    'risk_level': result['risk_level'],
                    'risk_score': result['risk_score'],
                    'changed_files': files,
                    'ai_summary': result.get('summary', ''),
                    'review_id': review.id  # 添加review_id用于构建链接
                })
                
                if success:
                    review.dingtalk_sent = True
                    review.dingtalk_sent_at = timezone.now()
                    review.save()
                    notified += 1
            
            if task:
                task.increment_processed()
                logger.info(f"评审完成: {repository.name} - {commit['hash'][:8]}")
        
        # 更新最终状态
        if task:
            task.status = TaskStatus.COMPLETED
            task.current_step = f'评审完成! 高风险:{high_risk} 中风险:{medium_risk} 低风险:{low_risk}'
            task.progress = 100
            task.completed_at = timezone.now()
            task.high_risk_count = high_risk
            task.medium_risk_count = medium_risk
            task.low_risk_count = low_risk
            task.dingtalk_notified_count = notified
            task.save()
        
        logger.info(f"任务完成: {repository.name}, 高风险:{high_risk}, 中风险:{medium_risk}, 低风险:{low_risk}")
        
        return {
            'status': 'completed',
            'task_id': task_id,
            'summary': {
                'total': total_commits,
                'high_risk': high_risk,
                'medium_risk': medium_risk,
                'low_risk': low_risk,
                'notified': notified
            }
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"代码评审任务失败: {error_msg}")
        
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error_msg
            task.completed_at = timezone.now()
            task.save()
        
        raise self.retry(exc=e)


@shared_task
def scheduled_review_task(config_id: int):
    """
    定时评审任务（由Celery Beat调度）
    
    Args:
        config_id: 定时评审配置ID
    """
    from apps.code_review.models import ScheduledReviewConfig
    
    try:
        config = ScheduledReviewConfig.objects.get(id=config_id, is_active=True)
        
        # 更新最后运行时间
        config.last_run_at = timezone.now()
        config.save(update_fields=['last_run_at'])
        
        logger.info(f"执行定时评审任务: {config.name}")
        
        # 为每个仓库启动评审任务
        for repo in config.repositories.filter(is_active=True):
            task_id = f"scheduled_{config.id}_{repo.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            if config.review_all_branches:
                code_review_task.delay(
                    repository_id=repo.id,
                    branch='master',
                    task_id=task_id,
                    all_branches=True,
                    trigger_mode='SCHEDULED'
                )
            else:
                for branch in config.branches:
                    code_review_task.delay(
                        repository_id=repo.id,
                        branch=branch,
                        task_id=task_id,
                        all_branches=False,
                        trigger_mode='SCHEDULED'
                    )
        
        logger.info(f"定时评审任务完成: {config.name}")
        
    except ScheduledReviewConfig.DoesNotExist:
        logger.error(f"定时评审配置不存在或已禁用: {config_id}")
    except Exception as e:
        logger.error(f"定时评审任务失败: {str(e)}")


@shared_task
def realtime_monitor_task():
    """
    实时监控任务（每分钟执行一次）
    检查所有启用实时监控的仓库是否有新提交
    """
    from apps.code_review.models import RealtimeMonitorConfig
    from apps.repository.services.git_service import GitService
    
    try:
        configs = RealtimeMonitorConfig.objects.filter(is_active=True)
        
        for config in configs:
            try:
                repo = config.repository
                git_service = GitService(repo)
                git_service.ensure_repo()
                
                # 获取最新提交
                latest_commit = git_service.get_latest_commit()
                
                if not latest_commit:
                    continue
                
                # 检查是否有新提交
                if config.last_checked_commit != latest_commit['hash']:
                    logger.info(f"发现新提交: {repo.name} - {latest_commit['hash'][:8]}")
                    
                    # 更新最后检查的commit
                    config.last_checked_commit = latest_commit['hash']
                    config.last_checked_at = timezone.now()
                    config.save(update_fields=['last_checked_commit', 'last_checked_at'])
                    
                    # 如果启用自动评审，触发评审任务
                    if config.auto_review:
                        task_id = f"realtime_{repo.id}_{latest_commit['hash'][:8]}"
                        
                        # 评审监控的分支
                        for branch in config.monitored_branches:
                            code_review_task.delay(
                                repository_id=repo.id,
                                branch=branch,
                                task_id=task_id,
                                all_branches=False,
                                trigger_mode='REALTIME'
                            )
                            
                            logger.info(f"触发实时评审: {repo.name} - {branch}")
                
            except Exception as e:
                logger.error(f"实时监控失败: {config.repository.name} - {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"实时监控任务失败: {str(e)}")


@shared_task(bind=True)
def trigger_manual_review(self, repository_id: int, branch: str = 'master',
                          all_branches: bool = False, triggered_by_id: int = None):
    """
    手动触发评审

    Args:
        repository_id: 仓库ID
        branch: 分支名
        all_branches: 是否评审所有分支
        triggered_by_id: 触发人ID
    """
    from apps.code_review.models import ReviewTask, TaskStatus, TriggerMode
    from apps.repository.models import Repository

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
        triggered_by_id=triggered_by_id,
        current_step='任务已创建，等待执行...'
    )

    # 异步执行评审任务
    code_review_task.delay(
        repository_id=repository_id,
        branch=branch,
        task_id=task_id,
        all_branches=all_branches,
        trigger_mode='MANUAL',
        triggered_by_id=triggered_by_id
    )

    # 返回任务ID用于追踪
    return {'task_id': task_id, 'status': 'triggered'}


@shared_task
def webhook_review_task(repository_id: int, commit_hash: str, branch: str, 
                        author: str, author_email: str, commit_message: str):
    """
    Webhook触发评审（GitLab/GitHub等平台推送时触发）
    
    Args:
        repository_id: 仓库ID
        commit_hash: Commit Hash
        branch: 分支名
        author: 作者
        author_email: 作者邮箱
        commit_message: 提交信息
    """
    from apps.code_review.models import CodeReview
    from apps.code_review.models import TriggerMode
    
    # 检查是否已评审
    if CodeReview.objects.filter(
        repository_id=repository_id,
        commit_hash=commit_hash
    ).exists():
        logger.info(f"Commit已评审: {commit_hash[:8]}")
        return {'status': 'already_reviewed'}
    
    # 生成任务追踪ID
    task_id = f"webhook_{repository_id}_{commit_hash[:8]}"
    
    # 触发评审任务
    code_review_task.delay(
        repository_id=repository_id,
        branch=branch,
        task_id=task_id,
        all_branches=False,
        trigger_mode='WEBHOOK'
    )
    
    logger.info(f"Webhook触发评审: {commit_hash[:8]}")
    return {'status': 'triggered'}