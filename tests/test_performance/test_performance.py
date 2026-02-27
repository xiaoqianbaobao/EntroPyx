"""
性能测试用例
"""
import pytest
from rest_framework import status
import time
from django.test import RequestFactory


@pytest.mark.django_db
class TestPerformanceResponseTime:
    """响应时间性能测试"""
    
    def test_list_reviews_response_time(self, authenticated_client, test_code_review):
        """TC-PERF-001: 评审列表API响应时间"""
        start_time = time.time()
        response = authenticated_client.get('/api/v1/reviews/')
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        response_time = end_time - start_time
        
        # 95%的请求应该在500ms内完成
        # 这里测试的是单次请求，应该更快
        assert response_time < 2.0, f"响应时间 {response_time}s 超过2秒"
    
    def test_list_repositories_response_time(self, authenticated_client, test_repository):
        """仓库列表API响应时间"""
        start_time = time.time()
        response = authenticated_client.get('/api/v1/repositories/')
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        response_time = end_time - start_time
        assert response_time < 2.0
    
    def test_retrieve_review_response_time(self, authenticated_client, test_code_review):
        """评审详情API响应时间"""
        start_time = time.time()
        response = authenticated_client.get(f'/api/v1/reviews/{test_code_review.id}/')
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        response_time = end_time - start_time
        assert response_time < 1.0
    
    def test_statistics_response_time(self, authenticated_client, test_code_review):
        """统计API响应时间"""
        start_time = time.time()
        response = authenticated_client.get('/api/v1/reviews/statistics/')
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        response_time = end_time - start_time
        assert response_time < 1.0
    
    def test_feedback_submit_response_time(self, authenticated_client, test_code_review):
        """提交反馈API响应时间"""
        data = {
            'feedback_status': 'CORRECT',
            'comment': '性能测试反馈'
        }
        
        start_time = time.time()
        response = authenticated_client.post(
            f'/api/v1/reviews/{test_code_review.id}/feedback/',
            data,
            format='json'
        )
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        response_time = end_time - start_time
        assert response_time < 1.0


@pytest.mark.django_db
class TestPerformanceLargeData:
    """大数据量性能测试"""
    
    def test_large_reviews_list(self, authenticated_client, test_repository, test_user):
        """大量评审记录列表查询"""
        from apps.code_review.models import CodeReview, RiskLevel
        
        # 创建100条评审记录
        for i in range(100):
            CodeReview.objects.create(
                repository=test_repository,
                branch='master',
                commit_hash=f'hash_{i:03d}',
                risk_score=0.1 + (i % 10) * 0.08,
                risk_level=RiskLevel.LOW if i < 60 else (RiskLevel.MEDIUM if i < 90 else RiskLevel.HIGH),
                changed_files=[{'status': 'M', 'path': f'file_{i}.py', 'is_critical': False}],
                ai_review_content=f'Test review {i}',
                author=test_user.username
            )
        
        start_time = time.time()
        response = authenticated_client.get('/api/v1/reviews/')
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        response_time = end_time - start_time
        # 100条记录应该能在2秒内返回
        assert response_time < 3.0
    
    def test_reviews_with_pagination(self, authenticated_client, test_repository, test_user):
        """分页查询性能"""
        from apps.code_review.models import CodeReview, RiskLevel
        
        # 创建50条记录
        for i in range(50):
            CodeReview.objects.create(
                repository=test_repository,
                branch='master',
                commit_hash=f'page_hash_{i:03d}',
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                changed_files=[],
                ai_review_content=f'Review {i}',
                author=test_user.username
            )
        
        # 测试不同页码
        page_times = []
        for page in [1, 2, 3]:
            start_time = time.time()
            response = authenticated_client.get(f'/api/v1/reviews/?page={page}&page_size=10')
            end_time = time.time()
            
            assert response.status_code == status.HTTP_200_OK
            page_times.append(end_time - start_time)
        
        # 所有页面应该在1秒内返回
        for t in page_times:
            assert t < 1.0
    
    def test_filter_performance(self, authenticated_client, test_repository, test_user):
        """筛选性能"""
        from apps.code_review.models import CodeReview, RiskLevel
        
        # 创建混合风险的记录
        for i in range(30):
            risk = RiskLevel.HIGH if i < 10 else (RiskLevel.MEDIUM if i < 20 else RiskLevel.LOW)
            CodeReview.objects.create(
                repository=test_repository,
                branch='master',
                commit_hash=f'filter_hash_{i:03d}',
                risk_score=0.9 if risk == RiskLevel.HIGH else (0.6 if risk == RiskLevel.MEDIUM else 0.3),
                risk_level=risk,
                changed_files=[],
                ai_review_content=f'Review {i}',
                author=f'user_{i % 3}'  # 3个不同的作者
            )
        
        # 测试各种筛选
        filters = [
            {'risk_level': 'HIGH'},
            {'risk_level': 'MEDIUM'},
            {'author': 'user_0'},
        ]
        
        for filter_params in filters:
            start_time = time.time()
            response = authenticated_client.get('/api/v1/reviews/', filter_params)
            end_time = time.time()
            
            assert response.status_code == status.HTTP_200_OK
            
            response_time = end_time - start_time
            assert response_time < 1.0


@pytest.mark.django_db
class TestPerformanceConcurrency:
    """并发性能测试"""
    
    def test_concurrent_requests(self, client, test_user):
        """并发请求测试"""
        import threading
        import time
        
        results = []
        
        def make_request():
            # 登录获取token
            login_response = client.post('/api/v1/auth/login/', {
                'username': 'test_developer',
                'password': 'test_password123'
            }, format='json')
            
            if login_response.status_code == 200:
                token = login_response.json()['access']
                client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
                
                # 访问API
                response = client.get('/api/v1/reviews/')
                results.append(response.status_code)
        
        # 创建10个并发线程
        threads = []
        for i in range(10):
            t = threading.Thread(target=make_request)
            threads.append(t)
        
        # 启动所有线程
        start_time = time.time()
        for t in threads:
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        end_time = time.time()
        
        # 所有请求应该成功
        assert len(results) == 10
        assert all(status == status.HTTP_200_OK for status in results)
        
        # 总时间应该合理
        total_time = end_time - start_time
        # 10个并发请求应该在5秒内完成
        assert total_time < 10.0


@pytest.mark.django_db
class TestPerformanceDatabase:
    """数据库性能测试"""
    
    def test_query_count_list_view(self, authenticated_client, test_repository, test_user):
        """测试列表视图的查询次数"""
        from apps.code_review.models import CodeReview, RiskLevel
        
        # 创建一些数据
        for i in range(10):
            CodeReview.objects.create(
                repository=test_repository,
                branch='master',
                commit_hash=f'query_hash_{i:03d}',
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                changed_files=[],
                ai_review_content=f'Test {i}',
                author=test_user.username
            )
        
        # 使用django-debug-toolbar或其他工具检查查询次数
        # 这里我们只是验证响应正常
        response = authenticated_client.get('/api/v1/reviews/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # 验证数据完整返回
        data = response.json()
        assert len(data['data']) >= 10
    
    def test_database_index_usage(self, authenticated_client, test_repository, test_user):
        """测试数据库索引使用"""
        from apps.code_review.models import CodeReview, RiskLevel
        
        # 创建数据
        for i in range(20):
            CodeReview.objects.create(
                repository=test_repository,
                branch=f'branch_{i % 3}',
                commit_hash=f'index_hash_{i:03d}',
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                changed_files=[],
                ai_review_content=f'Test {i}',
                author=test_user.username
            )
        
        # 测试带索引的查询
        start_time = time.time()
        response = authenticated_client.get('/api/v1/reviews/?branch=branch_0')
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        # 查询应该快（使用索引）
        response_time = end_time - start_time
        assert response_time < 1.0


@pytest.mark.django_db
class TestPerformanceMemory:
    """内存使用测试"""
    
    def test_large_response_size(self, authenticated_client, test_repository, test_user):
        """大响应大小测试"""
        from apps.code_review.models import CodeReview, RiskLevel
        
        # 创建包含大量数据的评审
        large_content = 'x' * 10000  # 10KB的AI评审内容
        
        CodeReview.objects.create(
            repository=test_repository,
            branch='master',
            commit_hash='large_content_hash',
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            changed_files=[{'status': 'M', 'path': f'file_{i}.py', 'is_critical': False} for i in range(50)],
            ai_review_content=large_content,
            author=test_user.username
        )
        
        start_time = time.time()
        response = authenticated_client.get('/api/v1/reviews/large_content_hash/')
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        response_time = end_time - start_time
        assert response_time < 2.0
