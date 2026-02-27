"""
测试夹具（Fixtures）
提供测试所需的常用数据和对象
"""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone


@pytest.fixture
def test_user(db):
    """创建测试用户"""
    from apps.users.models import User, UserRole
    
    user = User.objects.create_user(
        username='test_developer',
        email='test@example.com',
        password='test_password123',
        role=UserRole.DEVELOPER,
        department='测试部门'
    )
    return user


@pytest.fixture
def test_admin(db):
    """创建管理员用户"""
    from apps.users.models import User, UserRole
    
    user = User.objects.create_user(
        username='test_admin',
        email='admin@example.com',
        password='admin_password123',
        role=UserRole.ADMIN,
        department='管理部'
    )
    return user


@pytest.fixture
def test_leader(db):
    """创建团队负责人用户"""
    from apps.users.models import User, UserRole
    
    user = User.objects.create_user(
        username='test_leader',
        email='leader@example.com',
        password='leader_password123',
        role=UserRole.LEADER,
        department='研发部'
    )
    return user


@pytest.fixture
def test_tester(db):
    """创建测试工程师用户"""
    from apps.users.models import User, UserRole
    
    user = User.objects.create_user(
        username='test_tester',
        email='tester@example.com',
        password='tester_password123',
        role=UserRole.TESTER,
        department='测试部'
    )
    return user


@pytest.fixture
def authenticated_client(client, test_user):
    """返回已认证的Django客户端"""
    from rest_framework.test import APIClient
    
    client = APIClient()
    response = client.post('/api/v1/auth/login/', {
        'username': 'test_developer',
        'password': 'test_password123'
    })
    
    if response.status_code == 200:
        token = response.data.get('access')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    return client


@pytest.fixture
def admin_client(client, test_admin):
    """返回管理员认证的客户端"""
    from rest_framework.test import APIClient
    
    client = APIClient()
    response = client.post('/api/v1/auth/login/', {
        'username': 'test_admin',
        'password': 'admin_password123'
    })
    
    if response.status_code == 200:
        token = response.data.get('access')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    return client


@pytest.fixture
def test_repository(db, test_user):
    """创建测试仓库"""
    from apps.repository.models import Repository
    
    repository = Repository.objects.create(
        name='test-repository',
        git_url='https://github.com/test/test-repo.git',
        auth_type='password',
        username='testuser',
        password_encrypted='encrypted_password',
        local_path='/tmp/test-repo',
        high_risk_threshold=0.70,
        medium_risk_threshold=0.40,
        is_active=True,
        created_by=test_user
    )
    return repository


@pytest.fixture
def test_code_review(db, test_repository, test_user):
    """创建测试评审记录"""
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
        feedback_status=FeedbackStatus.PENDING,
        dingtalk_sent=False
    )
    return review


@pytest.fixture
def test_prd_review(db, test_user):
    """创建测试PRD评审记录"""
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
        ai_suggestions='PRD结构完整，建议增加异常场景描述',
        issues_found=[
            {'type': 'completeness', 'severity': 'medium', 'description': '缺少异常流程描述'}
        ],
        review_status=ReviewStatus.PENDING,
        created_by=test_user
    )
    return review


@pytest.fixture
def test_test_case(db, test_user, test_prd_review):
    """创建测试用例"""
    from apps.test_case.models import TestCase, CaseType, CasePriority
    
    test_case = TestCase.objects.create(
        prd_review=test_prd_review,
        case_id='TC001',
        title='用户登录-正常流程',
        type=CaseType.FUNCTION,
        priority=CasePriority.P0,
        precondition='用户未登录',
        steps=['1. 打开登录页面', '2. 输入用户名密码', '3. 点击登录按钮'],
        expected_result='登录成功，跳转首页',
        review_status='PENDING',
        created_by=test_user
    )
    return test_case


@pytest.fixture
def jwt_token(test_user):
    """生成JWT Token"""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh = RefreshToken.for_user(test_user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


@pytest.fixture
def sample_diff_content():
    """返回示例Diff内容"""
    return '''diff --git a/src/main/java/com/example/AccountService.java b/src/main/java/com/example/AccountService.java
index 1234567..89abcdef 100644
--- a/src/main/java/com/example/AccountService.java
+++ b/src/main/java/com/example/AccountService.java
@@ -45,7 +45,7 @@ public class AccountService {
     public void recharge(Long userId, double amount) {
         // 金额计算使用double，存在精度丢失风险
-        double balance = getBalance(userId);
+        BigDecimal balance = getBalance(userId);
         balance += amount;
         updateBalance(userId, balance);
     }
'''


@pytest.fixture
def sample_ai_response():
    """返回示例AI响应"""
    return {
        'risk_score': 0.85,
        'risk_level': 'HIGH',
        'ai_content': '''### 评审结果\n\n**风险评分: 85% (高风险)**\n\n### 发现的问题\n\n1. **[严重] 金额计算使用double类型**\n   - 位置: AccountService.java:45\n   - 描述: 充值金额使用double存储，存在精度丢失风险\n   - 建议: 改用 BigDecimal\n''',
        'summary': '高风险：金额计算存在精度问题',
        'review_points': [
            {
                'type': 'security',
                'line': 45,
                'file': 'AccountService.java',
                'severity': 'high',
                'description': '金额计算使用double类型，存在精度丢失风险',
                'suggestion': '改用BigDecimal'
            }
        ]
    }