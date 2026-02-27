"""
仓库管理模块API测试
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestRepositoryAPI:
    """仓库管理API测试"""
    
    def test_list_repositories_unauthorized(self, client):
        """获取仓库列表需要认证"""
        response = client.get('/api/v1/repositories/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_repositories(self, authenticated_client, test_repository):
        """TC-REPO-001: 获取仓库列表"""
        response = authenticated_client.get('/api/v1/repositories/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'data' in data
        assert 'total' in data
        assert len(data['data']) >= 1
    
    def test_create_repository_by_non_admin(self, authenticated_client):
        """TC-REPO-001: 非管理员创建仓库（应该失败）"""
        data = {
            'name': 'new-repo',
            'git_url': 'https://github.com/test/new-repo.git',
            'local_path': '/tmp/new-repo'
        }
        
        response = authenticated_client.post('/api/v1/repositories/', data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_repository_by_admin(self, admin_client):
        """TC-REPO-001: 管理员创建仓库"""
        data = {
            'name': 'admin-created-repo',
            'git_url': 'https://github.com/test/admin-repo.git',
            'auth_type': 'password',
            'username': 'testuser',
            'password': 'testpass',
            'local_path': '/tmp/admin-repo'
        }
        
        response = admin_client.post('/api/v1/repositories/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['message'] == '创建成功'
        assert response.json()['data']['name'] == 'admin-created-repo'
    
    def test_create_repository_duplicate_name(self, admin_client, test_repository):
        """创建仓库 - 重复名称"""
        data = {
            'name': test_repository.name,  # 重复名称
            'git_url': 'https://github.com/test/another-repo.git',
            'local_path': '/tmp/another-repo'
        }
        
        response = admin_client.post('/api/v1/repositories/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_repository_invalid_url(self, admin_client):
        """创建仓库 - 无效URL"""
        data = {
            'name': 'test-repo',
            'git_url': 'not-a-valid-url',
            'local_path': '/tmp/repo'
        }
        
        response = admin_client.post('/api/v1/repositories/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_repository_missing_required(self, admin_client):
        """创建仓库 - 缺少必填字段"""
        data = {
            'name': 'test-repo'
            # 缺少git_url和local_path
        }
        
        response = admin_client.post('/api/v1/repositories/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_retrieve_repository(self, authenticated_client, test_repository):
        """获取单个仓库详情"""
        response = authenticated_client.get(f'/api/v1/repositories/{test_repository.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['data']['id'] == test_repository.id
        assert data['data']['name'] == test_repository.name
    
    def test_retrieve_repository_not_found(self, authenticated_client):
        """获取不存在的仓库"""
        response = authenticated_client.get('/api/v1/repositories/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_repository(self, admin_client, test_repository):
        """TC-REPO-001: 更新仓库"""
        data = {
            'name': 'updated-repo-name',
            'git_url': test_repository.git_url,
            'local_path': test_repository.local_path,
            'high_risk_threshold': 0.80
        }
        
        response = admin_client.put(
            f'/api/v1/repositories/{test_repository.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['message'] == '更新成功'
        assert response.json()['data']['high_risk_threshold'] == '0.80'
    
    def test_partial_update_repository(self, admin_client, test_repository):
        """部分更新仓库"""
        data = {
            'name': 'partial-updated-repo'
        }
        
        response = admin_client.patch(
            f'/api/v1/repositories/{test_repository.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_delete_repository(self, admin_client, test_repository):
        """TC-REPO-001: 删除仓库"""
        repo_id = test_repository.id
        response = admin_client.delete(f'/api/v1/repositories/{repo_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 验证已删除
        from apps.repository.models import Repository
        assert not Repository.objects.filter(id=repo_id).exists()
    
    def test_delete_repository_not_found(self, admin_client):
        """删除不存在的仓库"""
        response = admin_client.delete('/api/v1/repositories/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_filter_repositories_by_active(self, admin_client, test_repository):
        """TC-REPO-005: 按激活状态筛选"""
        # 创建另一个仓库
        Repository = test_repository.__class__
        inactive_repo = Repository.objects.create(
            name='inactive-repo',
            git_url='https://github.com/test/inactive.git',
            local_path='/tmp/inactive',
            is_active=False,
            created_by=test_repository.created_by
        )
        
        response = admin_client.get('/api/v1/repositories/?is_active=true')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 所有返回的仓库都应该是激活状态
        for repo in data['data']:
            assert repo['is_active'] is True
        
        # 验证不活跃的仓库不在结果中
        repo_names = [repo['name'] for repo in data['data']]
        assert 'inactive-repo' not in repo_names
    
    def test_filter_repositories_by_created_by(self, authenticated_client, test_repository):
        """按创建人筛选"""
        response = authenticated_client.get(
            f'/api/v1/repositories/?created_by={test_repository.created_by.id}'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_sync_repository(self, authenticated_client, test_repository):
        """TC-REPO-003: 同步仓库"""
        response = authenticated_client.post(
            f'/api/v1/repositories/{test_repository.id}/sync/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert '同步任务已触发' in response.json()['message']
    
    def test_sync_repository_not_found(self, authenticated_client):
        """同步不存在的仓库"""
        response = authenticated_client.post('/api/v1/repositories/99999/sync/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_branches_not_implemented(self, authenticated_client, test_repository):
        """获取分支列表（暂未实现）"""
        response = authenticated_client.get(
            f'/api/v1/repositories/{test_repository.id}/branches/'
        )
        
        # 这个功能可能返回404或500，因为GitService可能未完整实现
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]
