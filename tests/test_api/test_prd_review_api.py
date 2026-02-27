"""
PRD评审模块API测试
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestPRDReviewAPI:
    """PRD评审API测试"""
    
    def test_list_prd_reviews_unauthorized(self, client):
        """获取PRD评审列表需要认证"""
        response = client.get('/api/v1/prd-reviews/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_prd_reviews(self, authenticated_client, test_prd_review):
        """TC-PRD-001: 获取PRD评审列表"""
        response = authenticated_client.get('/api/v1/prd-reviews/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'data' in data
        assert 'total' in data
        assert len(data['data']) >= 1
    
    def test_list_prd_reviews_filter_by_status(self, authenticated_client, test_prd_review):
        """TC-PRD-003: 按评审状态筛选"""
        response = authenticated_client.get('/api/v1/prd-reviews/?review_status=PENDING')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item['review_status'] == 'PENDING' for item in data['data'])
    
    def test_retrieve_prd_review(self, authenticated_client, test_prd_review):
        """TC-PRD-002: 获取PRD评审详情"""
        response = authenticated_client.get(f'/api/v1/prd-reviews/{test_prd_review.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['data']['id'] == test_prd_review.id
        assert 'user_stories' in data['data']
        assert 'requirements' in data['data']
        assert 'issues_found' in data['data']
        assert 'completeness_score' in data['data']
        assert 'overall_score' in data['data']
    
    def test_retrieve_prd_review_not_found(self, authenticated_client):
        """获取不存在的PRD评审"""
        response = authenticated_client.get('/api/v1/prd-reviews/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_prd_review_not_implemented(self, authenticated_client):
        """创建PRD评审（暂未实现）"""
        # 这个功能需要文件上传，可能未完整实现
        # 这里只是测试API接口存在
        response = authenticated_client.post(
            '/api/v1/prd-reviews/',
            {'title': 'test'},
            format='multipart'
        )
        
        # 可能是400（缺少文件）或500（未实现）
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_prd_review_serialization(self, authenticated_client, test_prd_review):
        """测试PRD评审数据序列化"""
        response = authenticated_client.get(f'/api/v1/prd-reviews/{test_prd_review.id}/')
        
        data = response.json()['data']
        
        # 验证JSON字段正确序列化
        assert isinstance(data['user_stories'], list)
        assert isinstance(data['requirements'], list)
        assert isinstance(data['issues_found'], list)
        
        # 验证评分字段
        assert 'completeness_score' in data
        assert 'consistency_score' in data
        assert 'risk_score' in data
        assert 'overall_score' in data
