from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from datetime import timedelta
from apps.code_review.models import CodeReview, RiskLevel, FeedbackStatus
from apps.prd_review.models import PRDReview, ReviewStatus as PRDReviewStatus
from apps.repository.models import Repository
from apps.test_case.models import TestCase, TestReport


class DashboardStatsView(views.APIView):
    """Dashboard统计视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取Dashboard统计数据"""
        time_range = request.query_params.get('time_range', 'today')  # today, week, month, year
        
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        
        # 根据时间范围获取日期范围
        date_ranges = {
            'today': (today, today),
            'week': (week_start, today),
            'month': (month_start, today),
            'year': (year_start, today)
        }
        
        start_date, end_date = date_ranges.get(time_range, date_ranges['today'])
        
        # 代码评审统计
        code_reviews = CodeReview.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        code_review_stats = {
            'total': code_reviews.count(),
            'high_risk': code_reviews.filter(risk_level=RiskLevel.HIGH).count(),
            'medium_risk': code_reviews.filter(risk_level=RiskLevel.MEDIUM).count(),
            'low_risk': code_reviews.filter(risk_level=RiskLevel.LOW).count(),
            'avg_risk_score': round(code_reviews.aggregate(Avg('risk_score'))['risk_score__avg'] or 0, 3)
        }
        
        # PRD评审统计
        prd_reviews = PRDReview.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        prd_review_stats = {
            'total': prd_reviews.count(),
            'approved': prd_reviews.filter(review_status=PRDReviewStatus.APPROVED).count(),
            'rejected': prd_reviews.filter(review_status=PRDReviewStatus.REJECTED).count(),
            'pending': prd_reviews.filter(review_status=PRDReviewStatus.PENDING).count(),
            'avg_overall_score': round(prd_reviews.aggregate(Avg('overall_score'))['overall_score__avg'] or 0, 3)
        }
        
        # 测试用例统计
        test_cases = TestCase.objects.all()
        test_case_stats = {
            'total': test_cases.count(),
            'approved': test_cases.filter(review_status='APPROVED').count(),
            'pending': test_cases.filter(review_status='PENDING').count(),
            'passed': test_cases.filter(last_execution_status='PASSED').count(),
            'failed': test_cases.filter(last_execution_status='FAILED').count(),
            'pass_rate': round(
                test_cases.filter(last_execution_status='PASSED').count() / test_cases.count() * 100, 2
            ) if test_cases.count() > 0 else 0
        }
        
        # 测试报告统计
        test_reports = TestReport.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        test_report_stats = {
            'total': test_reports.count(),
            'avg_pass_rate': round(test_reports.aggregate(Avg('pass_rate'))['pass_rate__avg'] or 0, 2),
            'total_cases': test_reports.aggregate(Sum('total_cases'))['total_cases__sum'] or 0,
            'total_passed': test_reports.aggregate(Sum('passed_cases'))['passed_cases__sum'] or 0,
            'total_failed': test_reports.aggregate(Sum('failed_cases'))['failed_cases__sum'] or 0
        }
        
        # 测试报告统计
        test_reports = TestReport.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        test_report_stats = {
            'total': test_reports.count(),
            'avg_pass_rate': round(test_reports.aggregate(Avg('pass_rate'))['pass_rate__avg'] or 0, 2),
            'total_cases': test_reports.aggregate(Sum('total_cases'))['total_cases__sum'] or 0,
            'total_passed': test_reports.aggregate(Sum('passed_cases'))['passed_cases__sum'] or 0,
            'total_failed': test_reports.aggregate(Sum('failed_cases'))['failed_cases__sum'] or 0
        }
        
        # 待反馈统计
        pending_feedback = CodeReview.objects.filter(
            feedback_status=FeedbackStatus.PENDING
        ).count()
        
        # 活跃仓库数
        active_repos = Repository.objects.filter(is_active=True).count()
        
        # AI准确率
        feedback_total = CodeReview.objects.exclude(
            feedback_status=FeedbackStatus.PENDING
        ).count()
        correct_feedback = CodeReview.objects.filter(
            feedback_status=FeedbackStatus.CORRECT
        ).count()
        accuracy_rate = (correct_feedback / feedback_total * 100) if feedback_total > 0 else 0
        
        # 知识库统计
        knowledge_stats = {
            'total_docs': 0,
            'total_entities': 0,
            'total_relationships': 0
        }
        
        try:
            from apps.knowledge_base.models import KnowledgeDocument, KnowledgeEntity, KnowledgeRelation
            knowledge_docs = KnowledgeDocument.objects.all()
            knowledge_entities = KnowledgeEntity.objects.all()
            knowledge_relations = KnowledgeRelation.objects.all()
            
            knowledge_stats = {
                'total_docs': knowledge_docs.count(),
                'total_entities': knowledge_entities.count(),
                'total_relationships': knowledge_relations.count()
            }
        except Exception as e:
            print(f"知识库统计错误: {e}")
            # 保持默认值
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'time_range': time_range,
                'code_reviews': code_review_stats,
                'prd_reviews': prd_review_stats,
                'test_cases': test_case_stats,
                'test_reports': test_report_stats,
                'pending_feedback': pending_feedback,
                'active_repositories': active_repos,
                'ai_accuracy_rate': round(accuracy_rate, 2),
                'knowledge_base': knowledge_stats
            }
        })


class RiskTrendView(views.APIView):
    """风险趋势视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取近30天趋势数据"""
        today = timezone.now().date()
        data = []
        
        for i in range(30):
            date = today - timedelta(days=29 - i)
            
            # 代码评审数据
            day_code_reviews = CodeReview.objects.filter(created_at__date=date)
            
            # PRD评审数据
            day_prd_reviews = PRDReview.objects.filter(created_at__date=date)
            
            # 测试用例数据
            day_test_cases = TestCase.objects.filter(created_at__date=date)
            
            data.append({
                'date': str(date),
                'prd_count': day_prd_reviews.count(),
                'code_count': day_code_reviews.count(),
                'test_count': day_test_cases.count(),
                'code_high': day_code_reviews.filter(risk_level=RiskLevel.HIGH).count(),
                'code_medium': day_code_reviews.filter(risk_level=RiskLevel.MEDIUM).count(),
                'code_low': day_code_reviews.filter(risk_level=RiskLevel.LOW).count(),
                'prd_approved': day_prd_reviews.filter(review_status=PRDReviewStatus.APPROVED).count(),
                'prd_rejected': day_prd_reviews.filter(review_status=PRDReviewStatus.REJECTED).count()
            })
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': data
        })


class RepositoryRankingView(views.APIView):
    """仓库排名视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取仓库风险排名"""
        rankings = []
        
        repos = Repository.objects.filter(is_active=True)
        for repo in repos:
            reviews = CodeReview.objects.filter(repository=repo)
            avg_score = reviews.aggregate(Avg('risk_score'))['risk_score__avg'] or 0
            high_risk_count = reviews.filter(risk_level=RiskLevel.HIGH).count()
            
            rankings.append({
                'repository_id': repo.id,
                'repository_name': repo.name,
                'total_reviews': reviews.count(),
                'avg_risk_score': round(avg_score, 3),
                'high_risk_count': high_risk_count
            })
        
        # 按平均风险分排序
        rankings.sort(key=lambda x: x['avg_risk_score'], reverse=True)
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': rankings[:20]  # 只返回前20
        })


class DeveloperRankingView(views.APIView):
    """开发者排名视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取开发者代码质量排名"""
        rankings = []
        
        authors = CodeReview.objects.values('author').distinct()
        for author_data in authors:
            author = author_data['author']
            reviews = CodeReview.objects.filter(author=author)
            
            avg_score = reviews.aggregate(Avg('risk_score'))['risk_score__avg'] or 0
            total = reviews.count()
            high_risk = reviews.filter(risk_level=RiskLevel.HIGH).count()
            
            # 代码行数统计
            lines_added = reviews.aggregate(Sum('lines_added'))['lines_added__sum'] or 0
            lines_deleted = reviews.aggregate(Sum('lines_deleted'))['lines_deleted__sum'] or 0
            lines_changed = reviews.aggregate(Sum('lines_changed'))['lines_changed__sum'] or 0
            
            # 准确率
            feedback = reviews.exclude(feedback_status=FeedbackStatus.PENDING)
            correct = reviews.filter(feedback_status=FeedbackStatus.CORRECT).count()
            accuracy = (correct / feedback.count() * 100) if feedback.count() > 0 else 0
            
            rankings.append({
                'author': author,
                'total_commits': total,
                'lines_added': lines_added,
                'lines_deleted': lines_deleted,
                'lines_changed': lines_changed,
                'avg_risk_score': round(avg_score, 3),
                'high_risk_count': high_risk,
                'accuracy_rate': round(accuracy, 2)
            })
        
        # 按提交次数排序
        rankings.sort(key=lambda x: x['total_commits'], reverse=True)
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': rankings[:20]
        })
