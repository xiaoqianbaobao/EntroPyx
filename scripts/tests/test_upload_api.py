#!/usr/bin/env python3
"""
测试录音上传API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from apps.repository.models import Repository

def test_upload_api():
    client = Client()
    
    # 获取第一个仓库
    repo = Repository.objects.first()
    if not repo:
        print("❌ 没有找到仓库，请先创建仓库")
        return
    
    print(f"✓ 使用仓库: {repo.name} (ID: {repo.id})")
    
    # 创建一个测试音频文件
    test_audio_content = b'fake audio data for testing'
    
    # 准备测试数据 - 使用FILES方式上传
    from django.core.files.uploadedfile import SimpleUploadedFile
    audio_file = SimpleUploadedFile(
        "test.webm",
        test_audio_content,
        content_type="audio/webm"
    )
    
    data = {
        'repository_id': repo.id,
        'meeting_title': '测试会议',
        'participants': '张三,李四',
        'audio_file': audio_file
    }
    
    print("\n📤 发送上传请求...")
    response = client.post('/meeting-assistant/api/recordings/upload/', data)
    
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ 上传成功!")
        print(f"   - 录音ID: {result.get('recording_id')}")
        print(f"   - 状态: {result.get('status')}")
        print(f"   - 消息: {result.get('message')}")
    else:
        print(f"❌ 上传失败")
        print(f"   响应内容: {response.content.decode('utf-8')}")

if __name__ == '__main__':
    print("=" * 50)
    print("测试录音上传API")
    print("=" * 50)
    test_upload_api()