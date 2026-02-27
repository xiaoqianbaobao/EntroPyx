"""
PRD评审模块单元测试
"""
import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestPRDReviewModel:
    """PRD评审模型测试"""
    
    def test_create_prd_review(self, test_user):
        """测试创建PRD评审"""
        from apps.prd_review.models import PRDReview, FileType, ReviewStatus
        
        review = PRDReview.objects.create(
            title='测试PRD文档',
            file='prd/test_prd.md',
            file_type=FileType.MARKDOWN,
            file_size=1024,
            background='这是一个测试PRD',
            user_stories=[
                {'story': '用户登录', 'acceptance': '登录成功'}
            ],
            requirements=[
                {'id': 'REQ001', 'description': '用户登录功能', 'priority': 'P0'}
            ],
            completeness_score=0.80,
            consistency_score=0.85,
            risk_score=0.30,
            overall_score=0.75,
            ai_suggestions='PRD结构完整',
            issues_found=[
                {'type': 'completeness', 'severity': 'medium', 'description': '缺少异常流程'}
            ],
            review_status=ReviewStatus.PENDING,
            created_by=test_user
        )
        
        assert review.title == '测试PRD文档'
        assert review.file_type == FileType.MARKDOWN
        assert review.completeness_score == 0.80
        assert review.overall_score == 0.75
        assert review.pk is not None
    
    def test_prd_review_str_representation(self, test_prd_review):
        """测试PRD评审字符串表示"""
        assert str(test_prd_review) == '测试PRD文档'
    
    def test_prd_review_file_type_choices(self, test_user):
        """测试文件类型选项"""
        from apps.prd_review.models import PRDReview, FileType
        
        for file_type in FileType.values:
            review = PRDReview.objects.create(
                title=f'Test PRD {file_type}',
                file=f'prd/test_{file_type}.md',
                file_type=file_type,
                file_size=1024,
                completeness_score=0.5,
                consistency_score=0.5,
                risk_score=0.5,
                overall_score=0.5,
                ai_suggestions='test',
                created_by=test_user
            )
            assert review.file_type == file_type
    
    def test_prd_review_user_stories_json(self, test_user):
        """测试用户故事JSON字段"""
        from apps.prd_review.models import PRDReview
        
        stories = [
            {'story': '用户登录', 'acceptance': '登录成功，跳转首页'},
            {'story': '用户注册', 'acceptance': '注册成功，发送验证邮件'},
            {'story': '密码找回', 'acceptance': '收到重置邮件，可重置密码'}
        ]
        
        review = PRDReview.objects.create(
            title='User Stories Test',
            file='prd/user_stories.md',
            file_type='md',
            file_size=2048,
            user_stories=stories,
            completeness_score=0.8,
            consistency_score=0.8,
            risk_score=0.3,
            overall_score=0.7,
            ai_suggestions='用户故事完整',
            created_by=test_user
        )
        
        assert len(review.user_stories) == 3
        assert review.user_stories[0]['story'] == '用户登录'
        assert review.user_stories[0]['acceptance'] == '登录成功，跳转首页'
    
    def test_prd_review_requirements_json(self, test_user):
        """测试需求点JSON字段"""
        from apps.prd_review.models import PRDReview
        
        requirements = [
            {'id': 'REQ001', 'description': '用户登录功能', 'priority': 'P0'},
            {'id': 'REQ002', 'description': '用户注册功能', 'priority': 'P1'},
            {'id': 'REQ003', 'description': '密码找回功能', 'priority': 'P2'}
        ]
        
        review = PRDReview.objects.create(
            title='Requirements Test',
            file='prd/requirements.md',
            file_type='md',
            file_size=2048,
            requirements=requirements,
            completeness_score=0.8,
            consistency_score=0.8,
            risk_score=0.3,
            overall_score=0.7,
            ai_suggestions='需求点清晰',
            created_by=test_user
        )
        
        assert len(review.requirements) == 3
        assert review.requirements[0]['id'] == 'REQ001'
        assert review.requirements[0]['priority'] == 'P0'
    
    def test_prd_review_issues_found_json(self, test_user):
        """测试发现问题JSON字段"""
        from apps.prd_review.models import PRDReview
        
        issues = [
            {
                'type': 'completeness',
                'severity': 'high',
                'description': '缺少异常场景描述'
            },
            {
                'type': 'consistency',
                'severity': 'medium',
                'description': '前后描述不一致'
            }
        ]
        
        review = PRDReview.objects.create(
            title='Issues Test',
            file='prd/issues.md',
            file_type='md',
            file_size=1024,
            completeness_score=0.6,
            consistency_score=0.7,
            risk_score=0.5,
            overall_score=0.6,
            ai_suggestions='需要补充异常场景',
            issues_found=issues,
            created_by=test_user
        )
        
        assert len(review.issues_found) == 2
        assert review.issues_found[0]['type'] == 'completeness'
        assert review.issues_found[0]['severity'] == 'high'


@pytest.mark.django_db
class TestPRDReviewSerializer:
    """PRD评审序列化器测试"""
    
    def test_prd_review_serializer_fields(self, test_prd_review):
        """测试序列化器字段"""
        from apps.prd_review.serializers import PRDReviewSerializer
        
        serializer = PRDReviewSerializer(test_prd_review)
        data = serializer.data
        
        assert 'id' in data
        assert 'title' in data
        assert 'file' in data
        assert 'file_type' in data
        assert 'completeness_score' in data
        assert 'overall_score' in data
        assert 'user_stories' in data
        assert 'requirements' in data
        assert 'issues_found' in data
    
    def test_prd_review_serialization(self, test_prd_review):
        """测试PRD评审数据序列化"""
        from apps.prd_review.serializers import PRDReviewSerializer
        
        serializer = PRDReviewSerializer(test_prd_review)
        
        assert serializer.data['title'] == test_prd_review.title
        assert serializer.data['file_type'] == test_prd_review.file_type


@pytest.mark.django_db
class TestPRDReviewViews:
    """PRD评审视图测试"""
    
    def test_prd_review_list_requires_auth(self, client):
        """测试PRD评审列表需要认证"""
        response = client.get('/api/v1/prd-reviews/')
        assert response.status_code == 401
    
    def test_prd_review_list_authenticated(self, authenticated_client):
        """测试已认证用户获取PRD评审列表"""
        response = authenticated_client.get('/api/v1/prd-reviews/')
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert 'total' in data
    
    def test_prd_review_list_filter_by_status(self, authenticated_client, test_prd_review):
        """测试按评审状态筛选"""
        response = authenticated_client.get('/api/v1/prd-reviews/?review_status=PENDING')
        assert response.status_code == 200
        data = response.json()
        assert all(item['review_status'] == 'PENDING' for item in data['data'])
    
    def test_prd_review_detail(self, authenticated_client, test_prd_review):
        """测试获取PRD评审详情"""
        response = authenticated_client.get(f'/api/v1/prd-reviews/{test_prd_review.id}/')
        assert response.status_code == 200
        data = response.json()
        assert data['data']['id'] == test_prd_review.id
        assert 'user_stories' in data['data']
        assert 'requirements' in data['data']
