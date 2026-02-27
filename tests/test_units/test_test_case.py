"""
测试用例模块单元测试
"""
import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestTestCaseModel:
    """测试用例模型测试"""
    
    def test_create_test_case(self, test_user, test_prd_review):
        """测试创建测试用例"""
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
        
        assert test_case.case_id == 'TC001'
        assert test_case.title == '用户登录-正常流程'
        assert test_case.type == CaseType.FUNCTION
        assert test_case.priority == CasePriority.P0
        assert test_case.pk is not None
    
    def test_test_case_str_representation(self, test_test_case):
        """测试用例字符串表示"""
        assert str(test_test_case) == 'TC001 - 用户登录-正常流程'
    
    def test_test_case_case_id_unique(self, test_test_case, test_user, test_prd_review):
        """测试用例ID唯一性"""
        from apps.test_case.models import TestCase, CaseType
        
        with pytest.raises(Exception):
            TestCase.objects.create(
                prd_review=test_prd_review,
                case_id='TC001',  # 重复ID
                title='Another Test',
                type=CaseType.FUNCTION,
                priority=CasePriority.P1,
                steps=[],
                expected_result='test',
                created_by=test_user
            )
    
    def test_test_case_type_choices(self, test_user, test_prd_review):
        """测试用例类型选项"""
        from apps.test_case.models import TestCase, CaseType
        
        for case_type in CaseType.values:
            test_case = TestCase.objects.create(
                prd_review=test_prd_review,
                case_id=f'TC_{case_type}',
                title=f'Test {case_type}',
                type=case_type,
                priority='P0',
                steps=['step1', 'step2'],
                expected_result='result',
                created_by=test_user
            )
            assert test_case.type == case_type
    
    def test_test_case_priority_choices(self, test_user, test_prd_review):
        """测试用例优先级选项"""
        from apps.test_case.models import TestCase, CasePriority
        
        for priority in CasePriority.values:
            test_case = TestCase.objects.create(
                prd_review=test_prd_review,
                case_id=f'TC_{priority}',
                title=f'Test {priority}',
                type='FUNCTION',
                priority=priority,
                steps=['step1'],
                expected_result='result',
                created_by=test_user
            )
            assert test_case.priority == priority
    
    def test_test_case_steps_json(self, test_user, test_prd_review):
        """测试用例步骤JSON字段"""
        from apps.test_case.models import TestCase
        
        steps = [
            '1. 打开登录页面 https://example.com/login',
            '2. 输入用户名：testuser',
            '3. 输入密码：password123',
            '4. 点击登录按钮',
            '5. 验证跳转到首页'
        ]
        
        test_case = TestCase.objects.create(
            prd_review=test_prd_review,
            case_id='TC_STEPS',
            title='Login Steps Test',
            type='FUNCTION',
            priority='P0',
            steps=steps,
            expected_result='登录成功，跳转首页',
            created_by=test_user
        )
        
        assert len(test_case.steps) == 5
        assert test_case.steps[0] == '1. 打开登录页面 https://example.com/login'
    
    def test_test_case_dubbo_config(self, test_user, test_prd_review):
        """测试用例Dubbo配置"""
        from apps.test_case.models import TestCase
        
        test_case = TestCase.objects.create(
            prd_review=test_prd_review,
            case_id='TC_DUBBO',
            title='Dubbo Test Case',
            type='FUNCTION',
            priority='P0',
            steps=['调用Dubbo接口'],
            expected_result='返回正确响应',
            dubbo_interface='com.example.service.UserService',
            dubbo_method='login',
            dubbo_params={'username': 'test', 'password': '123'},
            created_by=test_user
        )
        
        assert test_case.dubbo_interface == 'com.example.service.UserService'
        assert test_case.dubbo_method == 'login'
        assert test_case.dubbo_params['username'] == 'test'


@pytest.mark.django_db
class TestTestCaseSerializer:
    """测试用例序列化器测试"""
    
    def test_test_case_serializer_fields(self, test_test_case):
        """测试序列化器字段"""
        from apps.test_case.serializers import TestCaseSerializer
        
        serializer = TestCaseSerializer(test_test_case)
        data = serializer.data
        
        assert 'id' in data
        assert 'case_id' in data
        assert 'title' in data
        assert 'type' in data
        assert 'priority' in data
        assert 'steps' in data
        assert 'expected_result' in data
    
    def test_test_case_serialization(self, test_test_case):
        """测试用例数据序列化"""
        from apps.test_case.serializers import TestCaseSerializer
        
        serializer = TestCaseSerializer(test_test_case)
        
        assert serializer.data['case_id'] == test_test_case.case_id
        assert serializer.data['title'] == test_test_case.title


@pytest.mark.django_db
class TestTestCaseViews:
    """测试用例视图测试"""
    
    def test_test_case_list_requires_auth(self, client):
        """测试用例列表需要认证"""
        response = client.get('/api/v1/test-cases/')
        assert response.status_code == 401
    
    def test_test_case_list_authenticated(self, authenticated_client):
        """测试已认证用户获取用例列表"""
        response = authenticated_client.get('/api/v1/test-cases/')
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert 'total' in data
    
    def test_test_case_list_filter_by_type(self, authenticated_client, test_test_case):
        """测试按类型筛选"""
        response = authenticated_client.get('/api/v1/test-cases/?type=FUNCTION')
        assert response.status_code == 200
        data = response.json()
        assert all(item['type'] == 'FUNCTION' for item in data['data'])
    
    def test_test_case_list_filter_by_priority(self, authenticated_client, test_test_case):
        """测试按优先级筛选"""
        response = authenticated_client.get('/api/v1/test-cases/?priority=P0')
        assert response.status_code == 200
        data = response.json()
        assert all(item['priority'] == 'P0' for item in data['data'])


@pytest.mark.django_db
class TestTestExecution:
    """测试执行记录测试"""
    
    def test_create_test_execution(self, test_test_case):
        """测试创建测试执行记录"""
        from apps.test_case.models import TestExecution, ExecutionStatus
        
        execution = TestExecution.objects.create(
            test_case=test_test_case,
            execution_batch='BATCH_20260120_001',
            status=ExecutionStatus.PASSED,
            request_data={'username': 'test', 'password': '123'},
            response_data={'code': 0, 'message': 'success'},
            execution_time=0.5
        )
        
        assert execution.status == ExecutionStatus.PASSED
        assert execution.execution_time == 0.5
        assert execution.pk is not None
    
    def test_test_execution_status_choices(self, test_test_case):
        """测试执行状态选项"""
        from apps.test_case.models import TestExecution, ExecutionStatus
        
        for status in ExecutionStatus.values:
            execution = TestExecution.objects.create(
                test_case=test_test_case,
                execution_batch=f'BATCH_{status}',
                status=status,
                execution_time=0.1
            )
            assert execution.status == status
    
    def test_test_execution_with_error(self, test_test_case):
        """测试带错误的执行记录"""
        from apps.test_case.models import TestExecution, ExecutionStatus
        
        execution = TestExecution.objects.create(
            test_case=test_test_case,
            execution_batch='BATCH_ERROR',
            status=ExecutionStatus.FAILED,
            execution_time=0.1,
            error_message='Connection timeout',
            stack_trace='Traceback (most recent call last):...'
        )
        
        assert execution.status == ExecutionStatus.FAILED
        assert 'Connection timeout' in execution.error_message


@pytest.mark.django_db
class TestTestReport:
    """测试报告测试"""
    
    def test_create_test_report(self, test_user):
        """测试创建测试报告"""
        from apps.test_case.models import TestReport
        
        report = TestReport.objects.create(
            batch_id='BATCH_20260120_001',
            total_cases=100,
            passed_cases=85,
            failed_cases=10,
            error_cases=5,
            pass_rate=85.0,
            start_time=timezone.now(),
            end_time=timezone.now(),
            duration=120.5,
            report_file='reports/batch_001.html',
            created_by=test_user
        )
        
        assert report.batch_id == 'BATCH_20260120_001'
        assert report.total_cases == 100
        assert report.pass_rate == 85.0
        assert report.pk is not None
    
    def test_test_report_batch_id_unique(self, test_user):
        """测试报告批次ID唯一性"""
        from apps.test_case.models import TestReport
        
        TestReport.objects.create(
            batch_id='UNIQUE_BATCH',
            total_cases=10,
            passed_cases=10,
            failed_cases=0,
            error_cases=0,
            pass_rate=100.0,
            start_time=timezone.now(),
            end_time=timezone.now(),
            duration=10.0,
            report_file='reports/batch_001.html',
            created_by=test_user
        )
        
        with pytest.raises(Exception):
            TestReport.objects.create(
                batch_id='UNIQUE_BATCH',  # 重复
                total_cases=20,
                passed_cases=20,
                failed_cases=0,
                error_cases=0,
                pass_rate=100.0,
                start_time=timezone.now(),
                end_time=timezone.now(),
                duration=20.0,
                report_file='reports/batch_002.html',
                created_by=test_user
            )
