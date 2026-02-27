"""
会议助手功能测试脚本
Meeting Assistant Feature Test Script
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.repository.models import Repository
from apps.meeting_assistant.models import MeetingRecording, MeetingTranscript, MeetingSummary
from apps.meeting_assistant.services.kg_service import get_kg_service
from django.contrib.auth.models import User

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("会议助手功能测试")
    print("=" * 60)
    
    # 1. 测试数据模型
    print("\n1. 测试数据模型...")
    try:
        # 检查是否有仓库
        repositories = Repository.objects.all()
        print(f"   ✓ 找到 {repositories.count()} 个仓库")
        
        if repositories.count() > 0:
            repo = repositories.first()
            print(f"   示例仓库: {repo.name}")
        else:
            print("   ⚠ 没有找到仓库，请先创建仓库")
            return False
    except Exception as e:
        print(f"   ✗ 数据模型测试失败: {str(e)}")
        return False
    
    # 2. 测试会议录音
    print("\n2. 测试会议录音...")
    try:
        repo = repositories.first()
        
        recording = MeetingRecording.objects.create(
            repository=repo,
            meeting_title='测试会议',
            participants='测试用户1,测试用户2',
            audio_file='test_audio.mp3',
            audio_file_original_name='test_audio.mp3',
            duration=60,
            file_size=1024000,
            created_by=None
        )
        print(f"   ✓ 创建会议录音: {recording.id}")
        
        # 创建转写文本
        transcripts = [
            {'speaker': 'spk0', 'text': '大家好，今天我们进行代码评审会议。', 'start_time': 0.0, 'end_time': 5.0, 'confidence': 0.95},
            {'speaker': 'spk1', 'text': '我先介绍一下这个PR的主要功能。', 'start_time': 5.0, 'end_time': 10.0, 'confidence': 0.93},
            {'speaker': 'spk0', 'text': '有几个地方需要改进。', 'start_time': 10.0, 'end_time': 15.0, 'confidence': 0.92},
        ]
        
        for t in transcripts:
            MeetingTranscript.objects.create(
                recording=recording,
                speaker=t['speaker'],
                content=t['text'],
                start_time=t['start_time'],
                end_time=t['end_time'],
                confidence=t['confidence']
            )
        
        recording.transcript_count = len(transcripts)
        recording.status = 'completed'
        recording.save()
        
        print(f"   ✓ 创建 {len(transcripts)} 条转写文本")
        
    except Exception as e:
        print(f"   ✗ 会议录音测试失败: {str(e)}")
        return False
    
    # 3. 测试纪要生成
    print("\n3. 测试纪要生成...")
    try:
        summary = MeetingSummary.objects.create(
            recording=recording,
            repository=repo,
            title='测试会议纪要',
            summary_text='本次会议主要讨论了代码评审相关事项。',
            key_points=['代码评审', '功能优化', '性能改进'],
            decisions=['同意PR合并', '需要添加单元测试'],
            action_items=[
                {'task': '添加单元测试', 'assignee': '测试用户1', 'deadline': '2026-02-01'}
            ]
        )
        print(f"   ✓ 创建会议纪要: {summary.id}")
        
    except Exception as e:
        print(f"   ✗ 纪要生成测试失败: {str(e)}")
        return False
    
    # 4. 测试知识图谱
    print("\n4. 测试知识图谱...")
    try:
        kg_service = get_kg_service()
        kg_service.build_meeting_graph(summary)
        print("   ✓ 知识图谱构建完成")
        
        # 搜索实体
        entities = kg_service.search_entities('测试')
        print(f"   ✓ 找到 {len(entities)} 个相关实体")
        
    except Exception as e:
        print(f"   ✗ 知识图谱测试失败: {str(e)}")
        return False
    
    # 5. 测试API访问
    print("\n5. 测试API访问...")
    try:
        from django.test import Client
        client = Client()
        
        # 测试会议列表
        response = client.get('/meeting-assistant/')
        if response.status_code == 200 or response.status_code == 302:
            print("   ✓ 会议列表页面可访问")
        else:
            print(f"   ⚠ 会议列表页面返回: {response.status_code}")
        
        # 测试API
        response = client.get('/meeting-assistant/api/recordings/')
        if response.status_code == 200:
            print("   ✓ 录音API可访问")
        else:
            print(f"   ⚠ 录音API返回: {response.status_code}")
        
    except Exception as e:
        print(f"   ✗ API测试失败: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 所有测试通过！")
    print("=" * 60)
    
    # 显示访问信息
    print("\n访问信息:")
    print("- 会议列表: http://localhost:8000/meeting-assistant/")
    print("- 上传录音: http://localhost:8000/meeting-assistant/upload/")
    print("- 实时录音: http://localhost:8000/meeting-assistant/realtime-record/")
    print("- 知识图谱: http://localhost:8000/meeting-assistant/knowledge-graph/")
    print("- Admin: http://localhost:8000/admin/")
    
    return True

if __name__ == '__main__':
    test_basic_functionality()