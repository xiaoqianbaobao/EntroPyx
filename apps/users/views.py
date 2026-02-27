from rest_framework import viewsets, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.http import QueryDict
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

from .serializers import (
    UserSerializer, UserCreateSerializer, UserLoginSerializer, UserUpdateSerializer
)
from rest_framework.response import Response

User = get_user_model()


class EncryptedLoginView(LoginView):
    """支持前端加密密码的登录视图"""
    
    def post(self, request, *args, **kwargs):
        # 尝试解密密码
        encrypted_password = request.POST.get('password')
        if encrypted_password:
            try:
                # 预设的静态密钥 (16字节)，与前端保持一致
                # 注意：实际生产环境应使用更安全的密钥管理方式
                key = b'1234567890123456' 
                
                # Base64解码
                encrypted_data = base64.b64decode(encrypted_password)
                
                # AES解密 (ECB模式，简单对齐前端CryptoJS默认行为或显式指定)
                cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
                decryptor = cipher.decryptor()
                decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
                
                # 去除PKCS7填充
                unpadder = padding.PKCS7(128).unpadder()
                decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()
                
                original_password = decrypted_data.decode('utf-8')
                
                # 修改 request.POST 中的密码为明文，以便 Django Auth 表单验证
                # request.POST 是不可变的 QueryDict，需要复制一份修改
                mutable_post = request.POST.copy()
                mutable_post['password'] = original_password
                request.POST = mutable_post
                
            except Exception as e:
                # 解密失败，可能是未加密的明文或密钥错误，尝试直接使用（如果是明文）
                # 或者记录日志
                print(f"Password decryption failed: {e}")
                pass
                
        return super().post(request, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'code': 0,
            'message': '创建成功',
            'data': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'code': 0,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'code': 0,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(views.APIView):
    """当前用户视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
