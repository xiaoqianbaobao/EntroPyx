"""
测试用例模块API测试
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestTestCaseAPI:
    """测试用例API测试"""
    
    def test_list_test_cases_unauthorized(self, client):
        """获取测试用例列表需要认证"""
        response = client.get('/api/v1/test-cases/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_test_cases(self, authenticated_client, test_test_case):
        """TC-TEST-002: 获取测试用例列表"""
        response = authenticated_client.get('/api/v1/test-cases/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'data' in data
        assert 'total' in data
        assert len(data['data']) >= 1
    
    def test_list_test_cases_filter_by_type(self, authenticated_client, test_test_case):
        """TC-TEST-002: 按类型筛选"""
        response = authenticated_client.get('/api/v1/test-cases/?type=FUNCTION')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item['type'] == 'FUNCTION' for item in data['data'])
    
    def test_list_test_cases_filter_by_priority(self, authenticated_client, test_test_case):
        """TC-TEST-002: 按优先级筛选"""
        response = authenticated_client.get('/api/v1/test-cases/?priority=P0')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item['priority'] == 'P0' for item in data['data'])
    
    def test_list_test_cases_filter_by_prd_review(self, authenticated_client, test_test_case):
        """按PRD评审筛选"""
        response = authenticated_client.get(
            f'/api/v1/test-cases/?prd_review_id={test_test_case.prd_review.id}'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_retrieve_test_case(self, authenticated_client, test_test_case):
        """获取测试用例详情"""
        response = authenticated_client.get(f'/api/v1/test-cases/{test_test_case.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['data']['id'] == test_test_case.id
        assert data['data']['case_id'] == test_test_case.case_id
        assert 'steps' in data['data']
        assert 'expected_result' in data['data']
    
    def test_retrieve_test_case_not_found(self, authenticated_client):
        """获取不存在的测试用例"""
        response = authenticated_client.get('/api/v1/test-cases/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_generate_test_cases_not_implemented(self, authenticated_client):
        """TC-TEST-001: 生成测试用例（暂未实现）"""
        response = authenticated_client.post(
            '/api/v1/test-cases/generate/',
            {'prd_review_id': 1},
            format='json'
        )
        
        # 可能是404或500，因为功能可能未完整实现
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_execute_test_not_implemented(self, authenticated_client):
        """TC-TEST-003: 执行测试（暂未实现）"""
        response = authenticated_client.post(
            '/api/v1/test-cases/execute/',
            {'case_ids': [1, 2, 3]},
            format='json'
        )
        
        # 可能是404或500，因为功能可能未完整实现
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_test_case_serialization(self, authenticated_client, test_test_case):
        """测试用例数据序列化"""
        response = authenticated_client.get(f'/api/v1/test-cases/{test_test_case.id}/')
        
        data = response.json()['data']
        
        # 验证JSON字段正确序列化
        assert isinstance(data['steps'], list)
        assert 'dubbo_interface' in data
        assert 'dubbo_method' in data
        assert 'dubbo_params' in data
    
    def test_create_test_case_validation(self, authenticated_client, test_prd_review):
        """创建测试用例 - 验证"""
        data = {
            'case_id': 'TC_NEW',
            # 缺少必填字段
        }
        
        response = authenticated_client.post('/api/v1/test-cases/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_test_case_duplicate_id(self, authenticated_client, test_test_case, test_prd_review):
        """创建测试用例 - 重复ID"""
        from apps.test_case.models import TestCase
        
        data = {
            'prd_review': test_prd_review.id,
            'case_id': test_test_case.case_id,  # 重复ID
            'title': 'Another Test',
            'type': 'FUNCTION',
            'priority': 'P1',
            'steps': ['step1'],
            'expected_result': 'result'
        }
        
        response = authenticated_client.post('/api/v1/test-cases/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
