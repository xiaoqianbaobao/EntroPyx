#!/usr/bin/env python3
"""
测试知识库上传页面修复
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from apps.users.models import User

def test_knowledge_upload():
    """测试知识库上传页面"""
    print("🔍 测试知识库上传页面")
    
    # 创建测试用户
    user, created = User.objects.get_or_create(username='admin', defaults={
        'email': 'admin@example.com',
        'is_staff': True,
        'is_superuser': True
    })
    
    if created:
        user.set_password('admin')
        user.save()
        print("✅ 创建测试用户")
    else:
        print("ℹ️  用户已存在")
    
    # 测试客户端
    client = Client()
    
    # 1. 测试未登录访问
    print("\n1. 测试未登录访问上传页面")
    response = client.get('/api/v1/knowledge/upload/')
    print(f"   状态码: {response.status_code} (期望: 302)")
    if response.status_code == 302:
        print("   ✅ 重定向到登录页面")
    else:
        print("   ❌ 未正确重定向")
    
    # 2. 测试登录
    print("\n2. 测试用户登录")
    login_response = client.post('/accounts/login/', {
        'username': 'admin',
        'password': 'admin'
    })
    print(f"   登录状态码: {login_response.status_code}")
    if login_response.status_code == 200:
        print("   ✅ 登录成功")
    else:
        print("   ❌ 登录失败")
    
    # 3. 测试登录后访问上传页面
    print("\n3. 测试登录后访问上传页面")
    upload_response = client.get('/api/v1/knowledge/upload/')
    print(f"   状态码: {upload_response.status_code}")
    print(f"   模板: {upload_response.templates[0].name if upload_response.templates else '无'}")
    
    if upload_response.status_code == 200 and upload_response.templates:
        print("   ✅ 上传页面加载成功")
        # 检查页面内容
        content = upload_response.content.decode('utf-8')
        if '知识库文档上传' in content:
            print("   ✅ 页面内容正确")
        else:
            print("   ❌ 页面内容不正确")
    else:
        print("   ❌ 上传页面加载失败")
    
    # 4. 测试模板加载
    print("\n4. 测试模板加载")
    try:
        from django.template.loader import get_template
        template = get_template('knowledge_base/upload.html')
        print("   ✅ 模板加载成功")
        print(f"   模板路径: {template.origin.name}")
    except Exception as e:
        print(f"   ❌ 模板加载失败: {e}")
    
    print("\n🎉 测试完成！")
    return True

if __name__ == '__main__':
    test_knowledge_upload()