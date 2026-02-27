"""
认证模块API测试
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestAuthAPI:
    """认证API测试"""
    
    def test_user_registration(self, client):
        """TC-USER-001: 用户注册"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPassword123',
            'role': 'developer'
        }
        
        response = client.post('/api/v1/auth/register/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access' in response.json()
        assert 'refresh' in response.json()
    
    def test_user_registration_invalid_email(self, client):
        """用户注册 - 无效邮箱"""
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'NewPassword123'
        }
        
        response = client.post('/api/v1/auth/register/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.json()
    
    def test_user_registration_weak_password(self, client):
        """用户注册 - 弱密码"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123'  # 密码太短
        }
        
        response = client.post('/api/v1/auth/register/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_user_login_success(self, client, test_user):
        """TC-USER-002: 用户登录成功"""
        data = {
            'username': 'test_developer',
            'password': 'test_password123'
        }
        
        response = client.post('/api/v1/auth/login/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.json()
        assert 'refresh' in response.json()
    
    def test_user_login_wrong_password(self, client, test_user):
        """用户登录 - 密码错误"""
        data = {
            'username': 'test_developer',
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/v1/auth/login/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_login_nonexistent(self, client):
        """用户登录 - 用户不存在"""
        data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        
        response = client.post('/api/v1/auth/login/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_refresh(self, client, jwt_token):
        """TC-USER-003: Token刷新"""
        data = {
            'refresh': jwt_token['refresh']
        }
        
        response = client.post('/api/v1/auth/token/refresh/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.json()
    
    def test_token_refresh_invalid(self, client):
        """Token刷新 - 无效Token"""
        data = {
            'refresh': 'invalid_refresh_token'
        }
        
        response = client.post('/api/v1/auth/token/refresh/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_verify(self, client, jwt_token):
        """验证Token"""
        data = {
            'token': jwt_token['access']
        }
        
        response = client.post('/api/v1/auth/token/verify/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_password_change(self, client, authenticated_client, test_user):
        """修改密码"""
        data = {
            'old_password': 'test_password123',
            'new_password': 'NewPassword456'
        }
        
        response = authenticated_client.post('/api/v1/auth/password/change/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # 验证新密码可以登录
        login_response = client.post('/api/v1/auth/login/', {
            'username': 'test_developer',
            'password': 'NewPassword456'
        }, format='json')
        
        assert login_response.status_code == status.HTTP_200_OK
    
    def test_password_change_wrong_old(self, authenticated_client):
        """修改密码 - 旧密码错误"""
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'NewPassword456'
        }
        
        response = authenticated_client.post('/api/v1/auth/password/change/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_current_user(self, authenticated_client, test_user):
        """获取当前用户信息"""
        response = authenticated_client.get('/api/v1/auth/me/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['data']['username'] == test_user.username
    
    def test_current_user_unauthorized(self, client):
        """获取当前用户 - 未认证"""
        response = client.get('/api/v1/auth/me/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
