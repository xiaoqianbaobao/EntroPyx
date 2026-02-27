"""
代码评审模块单元测试
"""
import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestCodeReviewModel:
    """代码评审模型测试"""
    
    def test_create_code_review(self, test_repository):
        """测试创建代码评审"""
        from apps.code_review.models import CodeReview, RiskLevel, FeedbackStatus
        
        review = CodeReview.objects.create(
            repository=test_repository,
            branch='master',
            commit_hash='a1b2c3d4e5f6g7h8i9j0',
            commit_message='feat: 测试提交',
            author='test_user',
            author_email='test@example.com',
            commit_time=timezone.now(),
            risk_score=0.75,
            risk_level=RiskLevel.HIGH,
            ai_review_content='### 评审结果\n\n高风险代码变更',
            ai_model='deepseek-coder',
            changed_files=[
                {'status': 'M', 'path': 'src/main.py', 'is_critical': True}
            ],
            diff_content='diff --git a/src/main.py b/src/main.py',
            feedback_status=FeedbackStatus.PENDING
        )
        
        assert review.commit_hash == 'a1b2c3d4e5f6g7h8i9j0'
        assert review.risk_score == 0.75
        assert review.risk_level == RiskLevel.HIGH
        assert review.feedback_status == FeedbackStatus.PENDING
        assert review.pk is not None
    
    def test_code_review_str_representation(self, test_code_review):
        """测试评审字符串表示"""
        expected = 'test-repository - a1b2c3d'
        assert str(test_code_review) == expected
    
    def test_review_risk_level_choices(self, test_repository):
        """测试风险等级选项"""
        from apps.code_review.models import CodeReview, RiskLevel
        
        for level in [RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
            review = CodeReview.objects.create(
                repository=test_repository,
                branch='master',
                commit_hash=f'hash_{level}',
                risk_score=0.5 if level == RiskLevel.MEDIUM else (0.8 if level == RiskLevel.HIGH else 0.2),
                risk_level=level,
                changed_files=[],
                ai_review_content='test'
            )
            assert review.risk_level == level
    
    def test_review_feedback_status_choices(self, test_repository):
        """测试反馈状态选项"""
        from apps.code_review.models import CodeReview, FeedbackStatus
        
        for status in FeedbackStatus.values:
            review = CodeReview.objects.create(
                repository=test_repository,
                branch='master',
                commit_hash=f'hash_{status}',
                risk_score=0.5,
                risk_level='MEDIUM',
                changed_files=[],
                ai_review_content='test',
                feedback_status=status
            )
            assert review.feedback_status == status
    
    def test_review_unique_constraint(self, test_code_review, test_repository):
        """测试仓库+commit_hash唯一性约束"""
        from apps.code_review.models import CodeReview
        
        with pytest.raises(Exception):  # 数据库层面的唯一性约束
            CodeReview.objects.create(
                repository=test_repository,
                branch='master',
                commit_hash=test_code_review.commit_hash,  # 重复commit
                risk_score=0.5,
                risk_level='MEDIUM',
                changed_files=[],
                ai_review_content='duplicate'
            )
    
    def test_review_changed_files_json(self, test_repository):
        """测试变更文件JSON字段"""
        from apps.code_review.models import CodeReview
        
        files = [
            {'status': 'A', 'path': 'src/new_file.py', 'is_critical': True},
            {'status': 'M', 'path': 'src/existing.py', 'is_critical': False},
            {'status': 'D', 'path': 'src/old.py', 'is_critical': False}
        ]
        
        review = CodeReview.objects.create(
            repository=test_repository,
            branch='feature',
            commit_hash='hash_files_test',
            risk_score=0.3,
            risk_level='LOW',
            changed_files=files,
            ai_review_content='test'
        )
        
        assert len(review.changed_files) == 3
        assert review.changed_files[0]['status'] == 'A'
        assert review.changed_files[0]['is_critical'] is True
    
    def test_review_points_json(self, test_repository):
        """测试评审要点JSON字段"""
        from apps.code_review.models import CodeReview
        
        points = [
            {
                'type': 'security',
                'line': 45,
                'file': 'AccountService.java',
                'severity': 'high',
                'description': '金额计算使用double类型',
                'suggestion': '改用BigDecimal'
            }
        ]
        
        review = CodeReview.objects.create(
            repository=test_repository,
            branch='master',
            commit_hash='hash_points_test',
            risk_score=0.85,
            risk_level='HIGH',
            changed_files=[],
            ai_review_content='test',
            review_points=points
        )
        
        assert len(review.review_points) == 1
        assert review.review_points[0]['type'] == 'security'
        assert review.review_points[0]['severity'] == 'high'


@pytest.mark.django_db
class TestCodeReviewSerializer:
    """代码评审序列化器测试"""
    
    def test_code_review_serializer_fields(self, test_code_review):
        """测试序列化器字段"""
        from apps.code_review.serializers import CodeReviewSerializer
        
        serializer = CodeReviewSerializer(test_code_review)
        data = serializer.data
        
        assert 'id' in data
        assert 'repository' in data
        assert 'branch' in data
        assert 'commit_hash' in data
        assert 'risk_score' in data
        assert 'risk_level' in data
        assert 'ai_review_content' in data
        assert 'changed_files' in data
        assert 'feedback_status' in data
    
    def test_code_review_serialization(self, test_code_review):
        """测试评审数据序列化"""
        from apps.code_review.serializers import CodeReviewSerializer
        
        serializer = CodeReviewSerializer(test_code_review)
        
        assert serializer.data['branch'] == test_code_review.branch
        assert serializer.data['commit_hash'] == test_code_review.commit_hash
        assert serializer.data['risk_score'] == test_code_review.risk_score
    
    def test_changed_files_count(self, test_code_review):
        """测试变更文件计数"""
        from apps.code_review.serializers import CodeReviewSerializer
        
        serializer = CodeReviewSerializer(test_code_review)
        
        # changed_files_count是计算字段
        assert 'changed_files_count' in serializer.data
    
    def test_feedback_serializer_valid(self):
        """测试反馈序列化器 - 有效数据"""
        from apps.code_review.serializers import FeedbackSerializer
        
        data = {
            'feedback_status': 'CORRECT',
            'comment': '评审准确'
        }
        
        serializer = FeedbackSerializer(data=data)
        assert serializer.is_valid()
    
    def test_feedback_serializer_invalid_status(self):
        """测试反馈序列化器 - 无效状态"""
        from apps.code_review.serializers import FeedbackSerializer
        
        data = {
            'feedback_status': 'INVALID_STATUS',
            'comment': 'test'
        }
        
        serializer = FeedbackSerializer(data=data)
        assert not serializer.is_valid()
        assert 'feedback_status' in serializer.errors


@pytest.mark.django_db
class TestCodeReviewViews:
    """代码评审视图测试"""
    
    def test_review_list_requires_auth(self, client):
        """测试评审列表需要认证"""
        response = client.get('/api/v1/reviews/')
        assert response.status_code == 401
    
    def test_review_list_authenticated(self, authenticated_client):
        """测试已认证用户获取评审列表"""
        response = authenticated_client.get('/api/v1/reviews/')
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert 'total' in data
    
    def test_review_list_filter_by_risk_level(self, authenticated_client, test_code_review):
        """测试按风险等级筛选"""
        response = authenticated_client.get('/api/v1/reviews/?risk_level=HIGH')
        assert response.status_code == 200
        data = response.json()
        assert all(item['risk_level'] == 'HIGH' for item in data['data'])
    
    def test_review_list_filter_by_repository(self, authenticated_client, test_code_review):
        """测试按仓库筛选"""
        response = authenticated_client.get(
            f'/api/v1/reviews/?repository_id={test_code_review.repository.id}'
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item['repository'] == test_code_review.repository.id for item in data['data'])
    
    def test_review_detail(self, authenticated_client, test_code_review):
        """测试获取评审详情"""
        response = authenticated_client.get(f'/api/v1/reviews/{test_code_review.id}/')
        assert response.status_code == 200
        data = response.json()
        assert data['data']['id'] == test_code_review.id
        assert 'diff_content' in data['data']
    
    def test_review_feedback_submit(self, authenticated_client, test_code_review, test_user):
        """测试提交反馈"""
        from apps.code_review.models import FeedbackStatus
        
        data = {
            'feedback_status': 'CORRECT',
            'comment': '评审准确无误'
        }
        
        response = authenticated_client.post(
            f'/api/v1/reviews/{test_code_review.id}/feedback/',
            data,
            format='json'
        )
        
        assert response.status_code == 200
        assert response.json()['message'] == '反馈提交成功'
        
        # 验证数据库更新
        test_code_review.refresh_from_db()
        assert test_code_review.feedback_status == FeedbackStatus.CORRECT
        assert test_code_review.feedback_by == test_user
    
    def test_review_feedback_not_found(self, authenticated_client):
        """测试反馈不存在的评审"""
        data = {
            'feedback_status': 'CORRECT',
            'comment': 'test'
        }
        
        response = authenticated_client.post('/api/v1/reviews/99999/feedback/', data)
        assert response.status_code == 404
    
    def test_review_stats(self, authenticated_client, test_code_review):
        """测试评审统计"""
        response = authenticated_client.get('/api/v1/reviews/statistics/')
        assert response.status_code == 200
        data = response.json()
        assert 'total_count' in data
        assert 'high_risk_count' in data
        assert 'accuracy_rate' in data


@pytest.mark.django_db
class TestCodeReviewTasks:
    """代码评审任务测试"""
    
    def test_scan_all_repositories_task(self, test_repository, mocker):
        """测试扫描所有仓库任务"""
        from apps.code_review.tasks import scan_all_repositories
        
        # Mock code_review_task
        mock_task = mocker.patch('apps.code_review.tasks.code_review_task.delay')
        
        # 执行任务
        scan_all_repositories()
        
        # 验证任务被调用
        mock_task.assert_called()
    
    def test_manual_review_trigger(self, test_repository, mocker):
        """测试手动触发评审"""
        from apps.code_review.tasks import trigger_manual_review
        
        mock_task = mocker.patch('apps.code_review.tasks.code_review_task.delay')
        
        # 执行任务
        trigger_manual_review(test_repository.id, 'master')
        
        # 验证任务被调用
        mock_task.assert_called_once()