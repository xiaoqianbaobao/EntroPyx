"""
仓库管理模块单元测试
"""
import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestRepositoryModel:
    """仓库模型测试"""
    
    def test_create_repository(self, test_user):
        """测试创建仓库"""
        from apps.repository.models import Repository, AuthType
        
        repo = Repository.objects.create(
            name='test-repo',
            git_url='https://github.com/test/test-repo.git',
            auth_type=AuthType.PASSWORD,
            username='testuser',
            password_encrypted='encrypted_password',
            local_path='/tmp/test-repo',
            high_risk_threshold=0.70,
            medium_risk_threshold=0.40,
            is_active=True,
            created_by=test_user
        )
        
        assert repo.name == 'test-repo'
        assert repo.git_url == 'https://github.com/test/test-repo.git'
        assert repo.auth_type == AuthType.PASSWORD
        assert repo.is_active is True
        assert repo.pk is not None
    
    def test_repository_str_representation(self, test_repository):
        """测试仓库字符串表示"""
        assert str(test_repository) == 'test-repository'
    
    def test_repository_clone_status_exists(self, test_repository):
        """测试仓库克隆状态 - 已存在"""
        # 模拟仓库目录存在
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repository.local_path = tmpdir
            test_repository.save()
            
            assert test_repository.clone_status is True
    
    def test_repository_clone_status_not_exists(self, test_repository):
        """测试仓库克隆状态 - 不存在"""
        test_repository.local_path = '/non/existent/path'
        test_repository.save()
        
        assert test_repository.clone_status is False
    
    def test_repository_default_thresholds(self, test_user):
        """测试默认阈值配置"""
        from apps.repository.models import Repository
        
        repo = Repository.objects.create(
            name='default-threshold-repo',
            git_url='https://github.com/test/repo.git',
            local_path='/tmp/repo',
            created_by=test_user
        )
        
        assert repo.high_risk_threshold == 0.70
        assert repo.medium_risk_threshold == 0.40
    
    def test_repository_critical_patterns_default(self, test_user):
        """测试关键文件规则默认值"""
        from apps.repository.models import Repository
        
        repo = Repository.objects.create(
            name='patterns-repo',
            git_url='https://github.com/test/repo.git',
            local_path='/tmp/repo',
            created_by=test_user
        )
        
        assert repo.critical_patterns == []
        assert repo.ignore_patterns == []
    
    def test_repository_unique_constraint(self, test_repository, test_user):
        """测试仓库名称唯一性"""
        from apps.repository.models import Repository
        
        with pytest.raises(Exception):  # 数据库层面的唯一性约束
            Repository.objects.create(
                name='test-repository',  # 重复名称
                git_url='https://github.com/test/another-repo.git',
                local_path='/tmp/another-repo',
                created_by=test_user
            )


@pytest.mark.django_db
class TestRepositorySerializer:
    """仓库序列化器测试"""
    
    def test_repository_serializer_fields(self, test_repository):
        """测试序列化器字段"""
        from apps.repository.serializers import RepositorySerializer
        
        serializer = RepositorySerializer(test_repository)
        data = serializer.data
        
        assert 'id' in data
        assert 'name' in data
        assert 'git_url' in data
        assert 'auth_type' in data
        assert 'is_active' in data
        assert 'high_risk_threshold' in data
    
    def test_repository_serialization(self, test_repository):
        """测试仓库数据序列化"""
        from apps.repository.serializers import RepositorySerializer
        
        serializer = RepositorySerializer(test_repository)
        
        assert serializer.data['name'] == test_repository.name
        assert serializer.data['git_url'] == test_repository.git_url
    
    def test_repository_create_serializer_valid(self, test_user):
        """测试创建仓库序列化器 - 有效数据"""
        from apps.repository.serializers import RepositoryCreateSerializer
        
        data = {
            'name': 'new-repo',
            'git_url': 'https://github.com/test/new-repo.git',
            'auth_type': 'password',
            'username': 'user',
            'password': 'pass',
            'local_path': '/tmp/new-repo'
        }
        
        serializer = RepositoryCreateSerializer(data=data)
        assert serializer.is_valid()
    
    def test_repository_create_serializer_missing_name(self):
        """测试创建仓库序列化器 - 缺少名称"""
        from apps.repository.serializers import RepositoryCreateSerializer
        
        data = {
            'git_url': 'https://github.com/test/repo.git',
            'local_path': '/tmp/repo'
        }
        
        serializer = RepositoryCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors


@pytest.mark.django_db
class TestRepositoryViews:
    """仓库视图测试"""
    
    def test_repository_list_requires_auth(self, client):
        """测试仓库列表需要认证"""
        response = client.get('/api/v1/repositories/')
        assert response.status_code == 401
    
    def test_repository_list_authenticated(self, authenticated_client):
        """测试已认证用户获取仓库列表"""
        response = authenticated_client.get('/api/v1/repositories/')
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert 'total' in data
    
    def test_repository_create_by_non_admin(self, authenticated_client):
        """测试非管理员创建仓库"""
        data = {
            'name': 'test',
            'git_url': 'https://github.com/test/repo.git',
            'local_path': '/tmp/repo'
        }
        response = authenticated_client.post('/api/v1/repositories/', data)
        # 应该返回403，因为普通用户没有权限
        assert response.status_code == 403
    
    def test_repository_create_by_admin(self, admin_client):
        """测试管理员创建仓库"""
        data = {
            'name': 'admin-created-repo',
            'git_url': 'https://github.com/test/repo.git',
            'local_path': '/tmp/repo'
        }
        response = admin_client.post('/api/v1/repositories/', data)
        assert response.status_code == 201
        assert response.json()['message'] == '创建成功'
    
    def test_repository_retrieve(self, authenticated_client, test_repository):
        """测试获取单个仓库"""
        response = authenticated_client.get(f'/api/v1/repositories/{test_repository.id}/')
        assert response.status_code == 200
        assert response.json()['data']['id'] == test_repository.id
    
    def test_repository_update(self, admin_client, test_repository):
        """测试更新仓库"""
        data = {
            'name': 'updated-repo-name',
            'git_url': test_repository.git_url,
            'local_path': test_repository.local_path
        }
        response = admin_client.put(
            f'/api/v1/repositories/{test_repository.id}/',
            data
        )
        assert response.status_code == 200
        assert response.json()['message'] == '更新成功'
    
    def test_repository_delete(self, admin_client, test_repository):
        """测试删除仓库"""
        response = admin_client.delete(f'/api/v1/repositories/{test_repository.id}/')
        assert response.status_code == 204
        
        # 验证已删除
        from apps.repository.models import Repository
        assert not Repository.objects.filter(id=test_repository.id).exists()
    
    def test_repository_filter_by_active(self, admin_client, test_repository):
        """测试按激活状态筛选"""
        response = admin_client.get('/api/v1/repositories/?is_active=true')
        assert response.status_code == 200
        data = response.json()
        assert all(item['is_active'] for item in data['data'])
