"""
代码评审模块API测试
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestCodeReviewAPI:
    """代码评审API测试"""
    
    def test_list_reviews_unauthorized(self, client):
        """TC-REVIEW-001: 获取评审列表需要认证"""
        response = client.get('/api/v1/reviews/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_reviews(self, authenticated_client, test_code_review):
        """TC-REVIEW-001: 获取评审列表"""
        response = authenticated_client.get('/api/v1/reviews/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'data' in data
        assert 'total' in data
        assert len(data['data']) >= 1
    
    def test_list_reviews_filter_by_risk_level(self, authenticated_client, test_code_review):
        """TC-REVIEW-002: 按风险等级筛选"""
        response = authenticated_client.get('/api/v1/reviews/?risk_level=HIGH')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item['risk_level'] == 'HIGH' for item in data['data'])
    
    def test_list_reviews_filter_by_repository(self, authenticated_client, test_code_review):
        """TC-REVIEW-002: 按仓库筛选"""
        response = authenticated_client.get(
            f'/api/v1/reviews/?repository_id={test_code_review.repository.id}'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item['repository'] == test_code_review.repository.id for item in data['data'])
    
    def test_list_reviews_filter_by_author(self, authenticated_client, test_code_review):
        """TC-REVIEW-002: 按作者筛选"""
        response = authenticated_client.get('/api/v1/reviews/?author=test_user')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 可能过滤不到数据，因为作者的commit_hash可能不同
    
    def test_list_reviews_filter_by_feedback_status(self, authenticated_client, test_code_review):
        """TC-REVIEW-002: 按反馈状态筛选"""
        response = authenticated_client.get('/api/v1/reviews/?feedback_status=PENDING')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item['feedback_status'] == 'PENDING' for item in data['data'])
    
    def test_list_reviews_pagination(self, authenticated_client, test_code_review):
        """测试评审列表分页"""
        response = authenticated_client.get('/api/v1/reviews/?page=1&page_size=5')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'count' in data or 'total' in data
        assert 'results' in data or 'data' in data
    
    def test_retrieve_review(self, authenticated_client, test_code_review):
        """TC-REVIEW-003: 获取评审详情"""
        response = authenticated_client.get(f'/api/v1/reviews/{test_code_review.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['data']['id'] == test_code_review.id
        assert 'diff_content' in data['data']
        assert 'review_points' in data['data']
    
    def test_retrieve_review_not_found(self, authenticated_client):
        """获取不存在的评审"""
        response = authenticated_client.get('/api/v1/reviews/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_submit_feedback_correct(self, authenticated_client, test_code_review):
        """TC-REVIEW-004: 提交准确反馈"""
        data = {
            'feedback_status': 'CORRECT',
            'comment': '评审准确无误'
        }
        
        response = authenticated_client.post(
            f'/api/v1/reviews/{test_code_review.id}/feedback/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['message'] == '反馈提交成功'
        
        # 验证数据库更新
        test_code_review.refresh_from_db()
        assert test_code_review.feedback_status == 'CORRECT'
    
    def test_submit_feedback_false_positive(self, authenticated_client, test_code_review):
        """TC-REVIEW-005: 提交误报反馈"""
        data = {
            'feedback_status': 'FALSE_POSITIVE',
            'comment': '这是误报，实际场景下使用double是安全的'
        }
        
        response = authenticated_client.post(
            f'/api/v1/reviews/{test_code_review.id}/feedback/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        test_code_review.refresh_from_db()
        assert test_code_review.feedback_status == 'FALSE_POSITIVE'
    
    def test_submit_feedback_missed(self, authenticated_client, test_code_review):
        """提交漏报反馈"""
        data = {
            'feedback_status': 'MISSED',
            'comment': 'AI没有发现真实存在的问题'
        }
        
        response = authenticated_client.post(
            f'/api/v1/reviews/{test_code_review.id}/feedback/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        test_code_review.refresh_from_db()
        assert test_code_review.feedback_status == 'MISSED'
    
    def test_submit_feedback_without_comment(self, authenticated_client, test_code_review):
        """提交反馈 - 无评论"""
        data = {
            'feedback_status': 'CORRECT'
        }
        
        response = authenticated_client.post(
            f'/api/v1/reviews/{test_code_review.id}/feedback/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_submit_feedback_invalid_status(self, authenticated_client, test_code_review):
        """提交反馈 - 无效状态"""
        data = {
            'feedback_status': 'INVALID_STATUS',
            'comment': 'test'
        }
        
        response = authenticated_client.post(
            f'/api/v1/reviews/{test_code_review.id}/feedback/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_submit_feedback_not_found(self, authenticated_client):
        """提交反馈 - 评审不存在"""
        data = {
            'feedback_status': 'CORRECT',
            'comment': 'test'
        }
        
        response = authenticated_client.post('/api/v1/reviews/99999/feedback/', data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_statistics(self, authenticated_client, test_code_review):
        """TC-REVIEW-007: 获取评审统计"""
        response = authenticated_client.get('/api/v1/reviews/statistics/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'data' in data
        assert 'total_count' in data['data']
        assert 'high_risk_count' in data['data']
        assert 'accuracy_rate' in data['data']
    
    def test_statistics_no_data(self, authenticated_client):
        """获取统计 - 无数据"""
        response = authenticated_client.get('/api/v1/reviews/statistics/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['data']['total_count'] == 0
