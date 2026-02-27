from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def prd_review_task(self, prd_review_id: int):
    """
    PRD评审任务
    
    Args:
        prd_review_id: PRD评审ID
    """
    from .models import PRDReview
    from apps.core.ai_services import PRDAnalyzer
    
    try:
        prd_review = PRDReview.objects.get(id=prd_review_id)
        
        # 获取文件路径
        file_path = prd_review.file.path
        
        # 调用AI进行评审
        prd_analyzer = PRDAnalyzer()
        result = prd_analyzer.analyze_file(file_path, prd_review.file_type)
        
        # 更新评审结果
        prd_review.completeness_score = result.get('completeness_score', 0.5)
        prd_review.consistency_score = result.get('consistency_score', 0.5)
        prd_review.risk_score = result.get('risk_score', 0.5)
        prd_review.overall_score = result.get('overall_score', 0.5)
        prd_review.ai_suggestions = result.get('suggestions', '')
        prd_review.issues_found = result.get('issues', [])
        prd_review.background = result.get('background', '')
        prd_review.user_stories = result.get('user_stories', [])
        prd_review.requirements = result.get('requirements', [])
        prd_review.save()
        
        logger.info(f"PRD评审完成: {prd_review.title}, 综合得分: {prd_review.overall_score}")
        
    except Exception as e:
        logger.error(f"PRD评审任务失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise self.retry(exc=e)
