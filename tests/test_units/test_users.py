"""
用户模块单元测试
"""
import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestUserModel:
    """用户模型测试"""
    
    def test_create_user(self):
        """测试创建用户"""
        from apps.users.models import User, UserRole
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=UserRole.DEVELOPER
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.role == UserRole.DEVELOPER
        assert user.pk is not None
    
    def test_create_superuser(self):
        """测试创建超级用户"""
        from apps.users.models import User
        
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
    
    def test_user_role_display(self):
        """测试角色显示"""
        from apps.users.models import User, UserRole
        
        user = User.objects.create_user(
            username='developer',
            email='dev@example.com',
            password='pass123',
            role=UserRole.DEVELOPER
        )
        
        assert user.get_role_display() == '开发工程师'
    
    def test_user_str_representation(self):
        """测试用户字符串表示"""
        from apps.users.models import User
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        expected = 'testuser(开发工程师)'
        assert str(user) == expected
    
    def test_user_default_role(self):
        """测试默认角色"""
        from apps.users.models import User, UserRole
        
        user = User.objects.create_user(
            username='default_user',
            email='default@example.com',
            password='pass123'
        )
        
        assert user.role == UserRole.DEVELOPER
    
    def test_user_statistics_fields(self):
        """测试用户统计字段"""
        from apps.users.models import User
        
        user = User.objects.create_user(
            username='stats_user',
            email='stats@example.com',
            password='pass123'
        )
        
        assert user.total_reviews == 0
        assert user.feedback_count == 0
        assert user.last_active_at is None


@pytest.mark.django_db
class TestUserSerializer:
    """用户序列化器测试"""
    
    def test_user_serializer_fields(self, test_user):
        """测试序列化器字段"""
        from apps.users.serializers import UserSerializer
        from apps.users.models import UserRole
        
        serializer = UserSerializer(test_user)
        data = serializer.data
        
        assert 'id' in data
        assert 'username' in data
        assert 'email' in data
        assert 'role' in data
        assert 'department' in data
    
    def test_user_serialization(self, test_user):
        """测试用户数据序列化"""
        from apps.users.serializers import UserSerializer
        
        serializer = UserSerializer(test_user)
        
        assert serializer.data['username'] == test_user.username
        assert serializer.data['email'] == test_user.email
    
    def test_user_deserialization_valid(self):
        """测试用户数据反序列化 - 有效数据"""
        from apps.users.serializers import UserSerializer
        
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'role': 'developer'
        }
        
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()
    
    def test_user_deserialization_invalid_email(self):
        """测试用户数据反序列化 - 无效邮箱"""
        from apps.users.serializers import UserSerializer
        
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'newpass123'
        }
        
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_user_deserialization_missing_username(self):
        """测试用户数据反序列化 - 缺少用户名"""
        from apps.users.serializers import UserSerializer
        
        data = {
            'email': 'new@example.com',
            'password': 'newpass123'
        }
        
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors


@pytest.mark.django_db
class TestUserViews:
    """用户视图测试"""
    
    def test_user_list_requires_auth(self, client):
        """测试用户列表需要认证"""
        response = client.get('/api/v1/users/')
        assert response.status_code == 401
    
    def test_user_list_authenticated(self, authenticated_client):
        """测试已认证用户获取用户列表"""
        response = authenticated_client.get('/api/v1/users/')
        assert response.status_code == 200
        assert 'data' in response.json()
    
    def test_user_retrieve(self, authenticated_client, test_user):
        """测试获取单个用户"""
        response = authenticated_client.get(f'/api/v1/users/{test_user.id}/')
        assert response.status_code == 200
        data = response.json()
        assert data['data']['id'] == test_user.id
