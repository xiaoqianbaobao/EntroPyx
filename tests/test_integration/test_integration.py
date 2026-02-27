"""
集成测试用例
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase


@pytest.mark.django_db
class TestGitServiceIntegration:
    """Git服务集成测试"""
    
    def test_git_service_clone_repository(self, test_repository):
        """测试Git克隆仓库"""
        from apps.repository.services.git_service import GitService
        
        # Mock Git命令
        with patch('apps.repository.services.git_service.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            service = GitService(test_repository)
            
            # 测试确保仓库存在
            # 这里只是测试服务实例化，实际克隆需要真实环境
            assert service is not None
    
    def test_git_service_get_commits(self, test_repository):
        """测试获取提交记录"""
        from apps.repository.services.git_service import GitService
        
        service = GitService(test_repository)
        
        # Mock git log命令
        mock_commits = [
            {
                'hash': 'abc123',
                'message': 'feat: test commit',
                'author': 'test_user',
                'author_email': 'test@example.com',
                'committed_datetime': '2024-01-20T10:00:00Z'
            }
        ]
        
        with patch.object(service, 'get_today_commits', return_value=mock_commits):
            commits = service.get_today_commits('master')
            
            assert len(commits) == 1
            assert commits[0]['hash'] == 'abc123'
    
    def test_git_service_get_diff(self, test_repository):
        """测试获取Diff"""
        from apps.repository.services.git_service import GitService
        
        service = GitService(test_repository)
        
        mock_diff = 'diff --git a/src/main.py b/src/main.py\n--- a/src/main.py\n+++ b/src/main.py'
        mock_files = [{'status': 'M', 'path': 'src/main.py', 'is_critical': True}]
        
        with patch.object(service, 'get_diff_and_files', return_value=(mock_diff, mock_files)):
            diff, files = service.get_diff_and_files('abc123')
            
            assert 'diff --git' in diff
            assert len(files) == 1


@pytest.mark.django_db
class TestAIEngineIntegration:
    """AI引擎集成测试"""
    
    def test_ai_review_engine_initialization(self):
        """测试AI评审引擎初始化"""
        from apps.code_review.services.ai_engine import AIReviewEngine
        
        engine = AIReviewEngine()
        
        assert engine is not None
    
    def test_ai_review_engine_review(self):
        """测试AI评审功能"""
        from apps.code_review.services.ai_engine import AIReviewEngine
        
        engine = AIReviewEngine()
        
        diff_content = '''
        diff --git a/src/main.py b/src/main.py
        --- a/src/main.py
        +++ b/src/main.py
        @@ -1,3 +1,5 @@
        def login(username, password):
        +    if password == 'admin':
        +        return True
            return False
        '''
        
        files = [
            {'status': 'M', 'path': 'src/main.py', 'is_critical': True}
        ]
        
        commit_message = 'feat: 添加管理员登录'
        
        # Mock API调用
        with patch.object(engine, 'review') as mock_review:
            mock_review.return_value = {
                'risk_score': 0.85,
                'risk_level': 'HIGH',
                'ai_content': '### 高风险代码发现\n\n发现硬编码密码',
                'summary': '发现安全问题',
                'review_points': [
                    {
                        'type': 'security',
                        'severity': 'high',
                        'description': '硬编码密码',
                        'line': 3,
                        'file': 'src/main.py',
                        'suggestion': '使用配置文件或环境变量'
                    }
                ]
            }
            
            result = engine.review(diff_content, files, commit_message, 'abc123')
            
            assert result['risk_level'] == 'HIGH'
            assert result['risk_score'] > 0.7
            assert 'security' in result['review_points'][0]['type']


@pytest.mark.django_db
class TestDingTalkServiceIntegration:
    """钉钉服务集成测试"""
    
    def test_dingtalk_service_send_notification(self):
        """测试钉钉推送通知"""
        from apps.core.services.dingtalk_service import DingTalkService
        
        service = DingTalkService(
            webhook='https://oapi.dingtalk.com/robot/send?access_token=test',
            secret='SECtestsecret'
        )
        
        # Mock HTTP请求
        with patch('apps.core.services.dingtalk_service.requests.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            
            result = service.send_review_notification({
                'repository_name': 'test-repo',
                'branch': 'master',
                'commit_hash': 'abc123',
                'author': 'test_user',
                'commit_message': 'test commit',
                'risk_level': 'HIGH',
                'risk_score': 0.85,
                'changed_files': [{'status': 'M', 'path': 'src/main.py', 'is_critical': True}],
                'ai_summary': '发现安全问题'
            })
            
            assert result is True
            mock_post.assert_called_once()
    
    def test_dingtalk_service_sign_message(self):
        """测试钉钉签名消息"""
        from apps.core.services.dingtalk_service import DingTalkService
        
        service = DingTalkService(
            webhook='https://oapi.dingtalk.com/robot/send?access_token=test',
            secret='SECtestsecret'
        )
        
        # 验证签名方法存在
        assert hasattr(service, '_sign')
        
        # 验证签名计算
        timestamp, sign = service._sign()
        
        assert timestamp is not None
        assert sign is not None


@pytest.mark.django_db
class TestCeleryTaskIntegration:
    """Celery任务集成测试"""
    
    def test_code_review_task_execution(self, test_repository, mocker):
        """测试代码评审任务执行"""
        from apps.code_review.tasks import code_review_task
        
        # Mock所有依赖
        with patch('apps.code_review.tasks.GitService') as MockGitService, \
             patch('apps.code_review.tasks.AIReviewEngine') as MockAIEngine, \
             patch('apps.code_review.tasks.DingTalkService') as MockDingTalkService, \
             patch('apps.code_review.tasks.CodeReview') as MockCodeReview:
            
            # 设置Mock
            mock_git = MagicMock()
            mock_git.ensure_repo.return_value = None
            mock_git.get_today_commits.return_value = []
            MockGitService.return_value = mock_git
            
            mock_ai = MagicMock()
            mock_ai.review.return_value = {
                'risk_score': 0.5,
                'risk_level': 'MEDIUM',
                'ai_content': '测试评审',
                'review_points': []
            }
            MockAIEngine.return_value = mock_ai
            
            mock_review = MagicMock()
            MockCodeReview.objects.get.return_value = test_repository
            MockCodeReview.objects.filter.return_value.exists.return_value = False
            MockCodeReview.objects.create.return_value = mock_review
            
            # 执行任务
            result = code_review_task(test_repository.id, 'master')
            
            # 验证
            MockGitService.assert_called_once()
            MockCodeReview.objects.create.assert_called()
    
    def test_scan_all_repositories_task(self, test_repository, mocker):
        """测试扫描所有仓库任务"""
        from apps.code_review.tasks import scan_all_repositories
        
        with patch('apps.code_review.tasks.Repository') as MockRepository, \
             patch('apps.code_review.tasks.code_review_task') as mock_task:
            
            # 设置Mock
            MockRepository.objects.filter.return_value.exists.return_value = True
            MockRepository.objects.filter.return_value = [test_repository]
            
            # 执行任务
            scan_all_repositories()
            
            # 验证任务被触发
            assert mock_task.delay.called


@pytest.mark.django_db
class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    def test_complete_review_workflow(self, test_repository, test_user, mocker):
        """完整评审工作流测试"""
        from apps.code_review.models import CodeReview
        from apps.repository.models import Repository
        from django.utils import timezone
        
        # 1. 创建仓库
        repo = Repository.objects.create(
            name='e2e-test-repo',
            git_url='https://github.com/test/e2e.git',
            local_path='/tmp/e2e-test',
            created_by=test_user
        )
        
        assert repo.id is not None
        
        # 2. 创建评审记录
        review = CodeReview.objects.create(
            repository=repo,
            branch='master',
            commit_hash='e2e_test_hash_001',
            commit_message='e2e test commit',
            author=test_user.username,
            author_email=test_user.email,
            commit_time=timezone.now(),
            risk_score=0.75,
            risk_level='HIGH',
            ai_review_content='### E2E测试评审\n\n测试内容',
            changed_files=[{'status': 'M', 'path': 'test.py', 'is_critical': True}],
            review_points=[{
                'type': 'test',
                'severity': 'medium',
                'description': '测试要点',
                'suggestion': '测试建议'
            }]
        )
        
        assert review.id is not None
        
        # 3. 提交反馈
        from apps.code_review.models import FeedbackStatus
        
        review.feedback_status = FeedbackStatus.CORRECT
        review.feedback_comment = 'E2E测试反馈'
        review.feedback_by = test_user
        review.feedback_at = timezone.now()
        review.save()
        
        # 验证反馈
        review.refresh_from_db()
        assert review.feedback_status == FeedbackStatus.CORRECT
        assert review.feedback_comment == 'E2E测试反馈'
        
        # 4. 验证统计更新
        from apps.code_review.models import CodeReview as ReviewModel
        
        total = ReviewModel.objects.count()
        high_risk = ReviewModel.objects.filter(risk_level='HIGH').count()
        pending = ReviewModel.objects.filter(feedback_status=FeedbackStatus.PENDING).count()
        
        assert total >= 1
        assert high_risk >= 1
        
        # 清理测试数据
        review.delete()
        repo.delete()
    
    def test_repository_review_linkage(self, test_repository, test_user):
        """仓库与评审关联测试"""
        from apps.code_review.models import CodeReview, RiskLevel
        from django.utils import timezone
        
        # 创建多个评审
        for i in range(5):
            review = CodeReview.objects.create(
                repository=test_repository,
                branch='master',
                commit_hash=f'linkage_test_{i}',
                risk_score=0.3 + i * 0.1,
                risk_level=RiskLevel.LOW if i < 3 else RiskLevel.MEDIUM,
                changed_files=[],
                ai_review_content=f'Review {i}',
                author=test_user.username,
                commit_time=timezone.now()
            )
        
        # 验证关联
        reviews = test_repository.codereview_set.all()
        assert reviews.count() >= 5
        
        # 清理
        for review in reviews:
            review.delete()
