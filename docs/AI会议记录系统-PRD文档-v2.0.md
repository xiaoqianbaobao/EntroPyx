# AI会议记录与纪要生成系统 - 产品需求文档 (PRD)

**版本:** 2.0  
**创建日期:** 2026年1月28日  
**文档类型:** 产品需求文档  
**集成场景:** Django评审平台功能扩展

---

## 目录

1. [项目概述](#1-项目概述)
2. [现有平台分析](#2-现有平台分析)
3. [Django集成架构设计](#3-django集成架构设计)
4. [数据模型设计](#4-数据模型设计)
5. [API设计](#5-api设计)
6. [Celery异步任务设计](#6-celery异步任务设计)
7. [核心服务实现](#7-核心服务实现)
8. [前端集成方案](#8-前端集成方案)
9. [Django Settings配置](#9-django-settings配置)
10. [部署方案](#10-部署方案)
11. [迁移与集成步骤](#11-迁移与集成步骤)
12. [优化建议](#12-优化建议)
13. [测试计划](#13-测试计划)
14. [风险评估](#14-风险评估)
15. [成本与ROI分析](#15-成本与roi分析)
16. [实施时间线](#16-实施时间线)
17. [附录](#17-附录)
18. [总结](#18-总结)

---

## 1. 项目概述

### 1.1 项目背景

基于现有Django评审平台,需要集成AI会议记录功能,实现评审会议的自动记录、智能整理和知识沉淀。通过语音识别、自然语言处理和知识图谱技术,将会议内容与评审流程深度结合,提升评审效率和质量追溯能力。

### 1.2 项目目标

- 在Django评审平台中集成实时语音转文字功能
- 自动生成评审会议纪要,关联评审项目
- 支持多种文档格式导出(.md, .pdf, .docx)
- 构建评审知识图谱,实现历史评审内容检索
- 自动提取评审意见、决策事项和待办任务

### 1.3 核心价值

- **提升评审效率:** 将评审会议记录整理时间缩短80%
- **增强可追溯性:** 所有评审过程有完整音频和文字记录
- **知识复用:** 历史评审意见和问题可快速检索参考
- **合规性保障:** 完整记录满足审计和质量管理要求
- **无缝集成:** 与现有Django平台深度整合,无需切换系统

---

## 2. 现有平台分析

### 2.1 Django平台假设

基于典型评审平台,假设现有系统包含以下核心模块:

**核心数据模型:**

```python
# 评审项目
class ReviewProject(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20)  # 待评审、评审中、已完成
    created_by = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)

# 评审会议
class ReviewMeeting(models.Model):
    project = models.ForeignKey(ReviewProject)
    meeting_date = models.DateTimeField()
    participants = models.ManyToManyField(User)
    status = models.CharField(max_length=20)

# 评审意见
class ReviewComment(models.Model):
    meeting = models.ForeignKey(ReviewMeeting)
    author = models.ForeignKey(User)
    content = models.TextField()
    comment_type = models.CharField(max_length=20)  # 问题、建议、决策
```

### 2.2 集成点分析

**集成位置:**

1. 评审会议详情页 - 添加"开始录音"/"上传音频"按钮
2. 评审会议列表 - 显示会议纪要状态
3. 评审项目详情 - 展示关联的所有会议记录
4. 全局搜索 - 支持跨会议内容检索

**数据关联:**

- 会议录音关联到ReviewMeeting
- 会议纪要关联到ReviewProject
- 提取的评审意见自动创建ReviewComment
- 任务事项关联到任务管理模块(如果有)

---

## 3. Django集成架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│              现有Django评审平台                            │
│  Views / Templates / URL Routes / Django ORM            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│           Django App: meeting_assistant                 │
│  (新增Django应用,包含models, views, urls, tasks)          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌──────────────┬──────────────┬──────────────┬────────────┐
│  语音识别服务  │  NLP处理服务  │  知识图谱服务  │ 文档生成服务│
│  (独立进程)   │  (Celery任务) │   (独立进程)  │(Celery任务)│
└──────────────┴──────────────┴──────────────┴────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    数据存储层                             │
│   Django DB(PostgreSQL) + MinIO(音频) + Neo4j(图数据)    │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Django应用结构

```
your_django_project/
├── review/                          # 现有评审应用
│   ├── models.py
│   ├── views.py
│   └── ...
├── meeting_assistant/               # 新增会议助手应用
│   ├── __init__.py
│   ├── models.py                    # 会议记录相关模型
│   ├── views.py                     # API视图
│   ├── urls.py                      # 路由配置
│   ├── tasks.py                     # Celery异步任务
│   ├── services/                    # 业务逻辑层
│   │   ├── asr_service.py          # FunASR封装
│   │   ├── nlp_service.py          # NLP处理
│   │   ├── kg_service.py           # 知识图谱
│   │   └── document_service.py     # 文档生成
│   ├── serializers.py              # DRF序列化器
│   ├── templates/                   # 前端模板
│   │   ├── meeting_record.html
│   │   └── meeting_summary.html
│   └── static/                      # 静态资源
│       ├── js/recorder.js
│       └── css/meeting.css
├── static/
├── templates/
└── manage.py
```

---

## 4. 数据模型设计

### 4.1 新增Django Models

```python
# meeting_assistant/models.py
from django.db import models
from django.contrib.auth.models import User
from review.models import ReviewProject, ReviewMeeting

class MeetingRecording(models.Model):
    """会议录音记录"""
    meeting = models.OneToOneField(
        ReviewMeeting, 
        on_delete=models.CASCADE,
        related_name='recording'
    )
    audio_file = models.CharField(max_length=500)  # MinIO对象路径
    duration = models.IntegerField(help_text="时长(秒)")
    file_size = models.BigIntegerField(help_text="文件大小(字节)")
    upload_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('uploaded', '已上传'),
            ('processing', '处理中'),
            ('completed', '已完成'),
            ('failed', '失败')
        ],
        default='uploaded'
    )
    
    class Meta:
        db_table = 'meeting_recording'
        verbose_name = '会议录音'
        verbose_name_plural = '会议录音'


class MeetingTranscript(models.Model):
    """会议转写文本"""
    recording = models.ForeignKey(
        MeetingRecording, 
        on_delete=models.CASCADE,
        related_name='transcripts'
    )
    speaker = models.CharField(max_length=50, help_text="说话人标识")
    speaker_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        help_text="关联的用户账号"
    )
    content = models.TextField(help_text="转写内容")
    start_time = models.FloatField(help_text="开始时间(秒)")
    end_time = models.FloatField(help_text="结束时间(秒)")
    confidence = models.FloatField(default=0.0, help_text="识别置信度")
    
    class Meta:
        db_table = 'meeting_transcript'
        ordering = ['start_time']
        verbose_name = '会议转写'
        verbose_name_plural = '会议转写'


class MeetingSummary(models.Model):
    """会议纪要"""
    meeting = models.OneToOneField(
        ReviewMeeting,
        on_delete=models.CASCADE,
        related_name='summary'
    )
    project = models.ForeignKey(
        ReviewProject,
        on_delete=models.CASCADE,
        related_name='meeting_summaries'
    )
    
    # 基本信息
    title = models.CharField(max_length=200)
    summary_text = models.TextField(help_text="会议摘要")
    
    # 结构化内容(JSON存储)
    key_points = models.JSONField(default=list, help_text="讨论要点")
    decisions = models.JSONField(default=list, help_text="决策事项")
    action_items = models.JSONField(default=list, help_text="待办任务")
    
    # 导出的文档
    markdown_file = models.CharField(max_length=500, blank=True)
    pdf_file = models.CharField(max_length=500, blank=True)
    docx_file = models.CharField(max_length=500, blank=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_by = models.CharField(
        max_length=20,
        choices=[('auto', '自动生成'), ('manual', '人工编辑')],
        default='auto'
    )
    
    class Meta:
        db_table = 'meeting_summary'
        verbose_name = '会议纪要'
        verbose_name_plural = '会议纪要'


class ReviewOpinion(models.Model):
    """评审意见(从会议中提取)"""
    summary = models.ForeignKey(
        MeetingSummary,
        on_delete=models.CASCADE,
        related_name='opinions'
    )
    transcript = models.ForeignKey(
        MeetingTranscript,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="对应的转写片段"
    )
    
    opinion_type = models.CharField(
        max_length=20,
        choices=[
            ('issue', '问题'),
            ('suggestion', '建议'),
            ('decision', '决策'),
            ('risk', '风险'),
            ('positive', '肯定意见')
        ]
    )
    content = models.TextField(help_text="意见内容")
    speaker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    priority = models.CharField(
        max_length=10,
        choices=[('high', '高'), ('medium', '中'), ('low', '低')],
        default='medium'
    )
    
    # 关联到原有评审意见表(如果需要)
    related_comment = models.ForeignKey(
        'review.ReviewComment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_opinion'
        verbose_name = '评审意见'
        verbose_name_plural = '评审意见'


class KnowledgeGraphEntity(models.Model):
    """知识图谱实体(Django侧索引)"""
    entity_type = models.CharField(
        max_length=50,
        choices=[
            ('person', '人员'),
            ('project', '项目'),
            ('topic', '主题'),
            ('issue', '问题'),
            ('technology', '技术')
        ]
    )
    entity_name = models.CharField(max_length=200)
    neo4j_id = models.CharField(max_length=100, unique=True)  # Neo4j节点ID
    
    # 关联Django对象
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(ReviewProject, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'kg_entity'
        unique_together = ['entity_type', 'entity_name']
        verbose_name = '知识图谱实体'
        verbose_name_plural = '知识图谱实体'
```

---

## 5. API设计

### 5.1 RESTful API接口

```python
# meeting_assistant/urls.py
from django.urls import path
from . import views

app_name = 'meeting_assistant'

urlpatterns = [
    # 录音管理
    path('recordings/', views.RecordingListView.as_view(), name='recording-list'),
    path('recordings/<int:pk>/', views.RecordingDetailView.as_view(), name='recording-detail'),
    path('recordings/upload/', views.RecordingUploadView.as_view(), name='recording-upload'),
    
    # 实时转写(WebSocket)
    path('transcribe/realtime/', views.RealtimeTranscribeView.as_view(), name='realtime-transcribe'),
    
    # 纪要管理
    path('summaries/', views.SummaryListView.as_view(), name='summary-list'),
    path('summaries/<int:pk>/', views.SummaryDetailView.as_view(), name='summary-detail'),
    path('summaries/<int:pk>/generate/', views.GenerateSummaryView.as_view(), name='generate-summary'),
    path('summaries/<int:pk>/export/', views.ExportSummaryView.as_view(), name='export-summary'),
    
    # 评审意见
    path('opinions/', views.OpinionListView.as_view(), name='opinion-list'),
    path('opinions/<int:pk>/', views.OpinionDetailView.as_view(), name='opinion-detail'),
    
    # 知识图谱
    path('knowledge-graph/search/', views.KGSearchView.as_view(), name='kg-search'),
    path('knowledge-graph/relations/', views.KGRelationsView.as_view(), name='kg-relations'),
    
    # 与评审平台集成的特殊接口
    path('meetings/<int:meeting_id>/start-recording/', views.StartMeetingRecordingView.as_view()),
    path('meetings/<int:meeting_id>/sync-opinions/', views.SyncOpinionsToReviewView.as_view()),
]
```

### 5.2 关键API示例

```python
# meeting_assistant/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import MeetingRecording, MeetingSummary
from .tasks import process_audio_task, generate_summary_task
from .serializers import MeetingRecordingSerializer, MeetingSummarySerializer

class RecordingUploadView(APIView):
    """上传会议录音"""
    
    def post(self, request):
        meeting_id = request.data.get('meeting_id')
        audio_file = request.FILES.get('audio_file')
        
        # 验证会议是否存在
        meeting = get_object_or_404(ReviewMeeting, pk=meeting_id)
        
        # 上传到MinIO
        from .services.storage_service import upload_audio
        audio_path = upload_audio(audio_file, meeting_id)
        
        # 创建录音记录
        recording = MeetingRecording.objects.create(
            meeting=meeting,
            audio_file=audio_path,
            duration=0,  # 将在处理时计算
            file_size=audio_file.size,
            status='uploaded'
        )
        
        # 异步处理音频(转写)
        process_audio_task.delay(recording.id)
        
        return Response({
            'recording_id': recording.id,
            'status': 'processing',
            'message': '音频上传成功,正在处理中...'
        })


class GenerateSummaryView(APIView):
    """生成会议纪要"""
    
    def post(self, request, pk):
        recording = get_object_or_404(MeetingRecording, pk=pk)
        
        if recording.status != 'completed':
            return Response(
                {'error': '转写尚未完成,请稍后再试'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 异步生成纪要
        task = generate_summary_task.delay(recording.id)
        
        return Response({
            'task_id': task.id,
            'status': 'generating',
            'message': '纪要生成中,请稍后查看'
        })


class SyncOpinionsToReviewView(APIView):
    """将AI提取的意见同步到评审系统"""
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(ReviewMeeting, pk=meeting_id)
        
        if not hasattr(meeting, 'summary'):
            return Response({'error': '会议纪要不存在'}, status=400)
        
        summary = meeting.summary
        opinions = summary.opinions.all()
        
        # 同步到原有的ReviewComment表
        from review.models import ReviewComment
        synced_count = 0
        
        for opinion in opinions:
            if not opinion.related_comment:
                comment = ReviewComment.objects.create(
                    meeting=meeting,
                    author=opinion.speaker,
                    content=opinion.content,
                    comment_type=opinion.opinion_type
                )
                opinion.related_comment = comment
                opinion.save()
                synced_count += 1
        
        return Response({
            'synced_count': synced_count,
            'message': f'成功同步{synced_count}条评审意见'
        })
```

---

## 6. Celery异步任务设计

### 6.1 任务定义

```python
# meeting_assistant/tasks.py
from celery import shared_task
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_audio_task(self, recording_id):
    """处理音频文件:转写+说话人分离"""
    from .models import MeetingRecording, MeetingTranscript
    from .services.asr_service import FunASRService
    
    try:
        recording = MeetingRecording.objects.get(pk=recording_id)
        recording.status = 'processing'
        recording.save()
        
        # 下载音频文件
        from .services.storage_service import download_audio
        audio_path = download_audio(recording.audio_file)
        
        # 使用FunASR进行转写
        asr_service = FunASRService()
        transcripts = asr_service.transcribe_with_diarization(audio_path)
        
        # 保存转写结果
        for transcript_data in transcripts:
            MeetingTranscript.objects.create(
                recording=recording,
                speaker=transcript_data['speaker'],
                content=transcript_data['text'],
                start_time=transcript_data['start_time'],
                end_time=transcript_data['end_time'],
                confidence=transcript_data['confidence']
            )
        
        recording.status = 'completed'
        recording.save()
        
        logger.info(f"Recording {recording_id} processed successfully")
        
        # 自动触发纪要生成
        generate_summary_task.delay(recording_id)
        
    except Exception as e:
        logger.error(f"Error processing recording {recording_id}: {str(e)}")
        recording.status = 'failed'
        recording.save()
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True)
def generate_summary_task(self, recording_id):
    """生成会议纪要"""
    from .models import MeetingRecording, MeetingSummary
    from .services.nlp_service import NLPService
    from .services.kg_service import KGService
    
    try:
        recording = MeetingRecording.objects.get(pk=recording_id)
        meeting = recording.meeting
        
        # 获取所有转写文本
        transcripts = recording.transcripts.all().order_by('start_time')
        full_text = "\n".join([t.content for t in transcripts])
        
        # NLP处理
        nlp_service = NLPService()
        summary_data = nlp_service.generate_meeting_summary(
            full_text=full_text,
            transcripts=transcripts,
            meeting=meeting
        )
        
        # 创建或更新纪要
        summary, created = MeetingSummary.objects.update_or_create(
            meeting=meeting,
            defaults={
                'project': meeting.project,
                'title': summary_data['title'],
                'summary_text': summary_data['summary'],
                'key_points': summary_data['key_points'],
                'decisions': summary_data['decisions'],
                'action_items': summary_data['action_items']
            }
        )
        
        # 提取评审意见
        from .models import ReviewOpinion
        for opinion_data in summary_data['opinions']:
            ReviewOpinion.objects.create(
                summary=summary,
                opinion_type=opinion_data['type'],
                content=opinion_data['content'],
                speaker_id=opinion_data.get('speaker_id'),
                priority=opinion_data.get('priority', 'medium')
            )
        
        # 更新知识图谱
        kg_service = KGService()
        kg_service.build_meeting_graph(summary, transcripts)
        
        logger.info(f"Summary generated for recording {recording_id}")
        
        return {'summary_id': summary.id}
        
    except Exception as e:
        logger.error(f"Error generating summary for recording {recording_id}: {str(e)}")
        raise


@shared_task
def export_document_task(summary_id, format_type):
    """导出文档(markdown/pdf/docx)"""
    from .models import MeetingSummary
    from .services.document_service import DocumentService
    
    try:
        summary = MeetingSummary.objects.get(pk=summary_id)
        doc_service = DocumentService()
        
        if format_type == 'markdown':
            file_path = doc_service.export_markdown(summary)
            summary.markdown_file = file_path
        elif format_type == 'pdf':
            file_path = doc_service.export_pdf(summary)
            summary.pdf_file = file_path
        elif format_type == 'docx':
            file_path = doc_service.export_docx(summary)
            summary.docx_file = file_path
        
        summary.save()
        return {'file_path': file_path}
        
    except Exception as e:
        logger.error(f"Error exporting document: {str(e)}")
        raise
```

---

## 7. 核心服务实现

### 7.1 FunASR服务封装

```python
# meeting_assistant/services/asr_service.py
from funasr import AutoModel
import os

class FunASRService:
    """FunASR服务封装"""
    
    def __init__(self):
        # 加载模型(建议在应用启动时加载,避免重复加载)
        self.model = AutoModel(
            model="paraformer-zh",  # 语音识别模型
            model_revision="v2.0.4",
            vad_model="fsmn-vad",   # 语音活动检测
            vad_model_revision="v2.0.4",
            punc_model="ct-punc",   # 标点预测
            punc_model_revision="v2.0.4",
            spk_model="cam++",      # 说话人分离
            spk_model_revision="v2.0.2"
        )
    
    def transcribe_with_diarization(self, audio_path):
        """
        转写音频并进行说话人分离
        
        Returns:
            List[dict]: [
                {
                    'speaker': 'spk0',
                    'text': '转写内容',
                    'start_time': 0.0,
                    'end_time': 5.2,
                    'confidence': 0.95
                },
                ...
            ]
        """
        result = self.model.generate(
            input=audio_path,
            batch_size_s=300,
            hotword='',  # 可添加热词
        )
        
        transcripts = []
        for item in result:
            if 'text' in item:
                transcripts.append({
                    'speaker': item.get('spk', 'unknown'),
                    'text': item['text'],
                    'start_time': item.get('timestamp', [0, 0])[0] / 1000,
                    'end_time': item.get('timestamp', [0, 0])[1] / 1000,
                    'confidence': item.get('confidence', 0.0)
                })
        
        return transcripts
    
    def transcribe_realtime(self, audio_stream):
        """实时转写(用于WebSocket)"""
        # 实时转写实现
        pass
```

### 7.2 NLP服务实现

```python
# meeting_assistant/services/nlp_service.py
import json
import re
from typing import List, Dict

class NLPService:
    """NLP处理服务"""
    
    def __init__(self):
        # 这里可以初始化本地LLM模型(如Ollama)
        # 或者使用规则+传统NLP方法
        self.use_llm = True  # 配置是否使用LLM
        
        if self.use_llm:
            from ollama import Client
            self.llm_client = Client(host='http://localhost:11434')
            self.model_name = 'qwen2.5:7b'
    
    def generate_meeting_summary(self, full_text: str, transcripts, meeting) -> Dict:
        """生成会议纪要"""
        
        if self.use_llm:
            return self._generate_with_llm(full_text, meeting)
        else:
            return self._generate_with_rules(full_text, transcripts, meeting)
    
    def _generate_with_llm(self, full_text: str, meeting) -> Dict:
        """使用LLM生成纪要"""
        
        prompt = f"""
请根据以下会议转写内容,生成结构化的会议纪要。

会议信息:
- 项目: {meeting.project.title}
- 日期: {meeting.meeting_date}

会议内容:
{full_text[:4000]}  # 限制长度避免超出context

请以JSON格式输出,包含以下字段:
{{
    "title": "会议标题",
    "summary": "会议摘要(3-5句话)",
    "key_points": ["要点1", "要点2", ...],
    "decisions": ["决策1", "决策2", ...],
    "action_items": [
        {{"task": "任务描述", "assignee": "负责人", "deadline": "截止日期"}},
        ...
    ],
    "opinions": [
        {{"type": "issue|suggestion|decision", "content": "意见内容", "priority": "high|medium|low"}},
        ...
    ]
}}
"""
        
        response = self.llm_client.chat(
            model=self.model_name,
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        try:
            result = json.loads(response['message']['content'])
            return result
        except:
            # 如果LLM输出格式不对,降级到规则方法
            return self._generate_with_rules(full_text, None, meeting)
    
    def _generate_with_rules(self, full_text: str, transcripts, meeting) -> Dict:
        """使用规则方法生成纪要"""
        import jieba.analyse
        
        # 提取关键词
        keywords = jieba.analyse.extract_tags(full_text, topK=10)
        
        # 简单的规则匹配
        decisions = self._extract_decisions(full_text)
        action_items = self._extract_action_items(full_text)
        
        return {
            'title': f"{meeting.project.title} - 评审会议纪要",
            'summary': full_text[:200] + '...',  # 简单截取
            'key_points': keywords,
            'decisions': decisions,
            'action_items': action_items,
            'opinions': []
        }
    
    def _extract_decisions(self, text: str) -> List[str]:
        """提取决策事项"""
        decision_patterns = [
            r'决定[：:](.*?)([。\n])',
            r'确定[：:](.*?)([。\n])',
            r'通过[：:](.*?)([。\n])',
        ]
        
        decisions = []
        for pattern in decision_patterns:
            matches = re.findall(pattern, text)
            decisions.extend([m[0].strip() for m in matches])
        
        return decisions[:10]  # 最多返回10条
    
    def _extract_action_items(self, text: str) -> List[Dict]:
        """提取待办任务"""
        action_patterns = [
            r'(需要|要|请)(.*?)(完成|处理|跟进)(.*?)([。\n])',
        ]
        
        action_items = []
        for pattern in action_patterns:
            matches = re.findall(pattern, text)
            for match in matches[:5]:  # 最多5条
                action_items.append({
                    'task': ''.join(match),
                    'assignee': '',
                    'deadline': ''
                })
        
        return action_items
```

### 7.3 知识图谱服务

```python
# meeting_assistant/services/kg_service.py
from neo4j import GraphDatabase
from django.conf import settings

class KGService:
    """Neo4j知识图谱服务"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def build_meeting_graph(self, summary, transcripts):
        """构建会议知识图谱"""
        with self.driver.session() as session:
            # 创建会议节点
            session.execute_write(self._create_meeting_node, summary)
            
            # 创建参会人员关系
            session.execute_write(self._create_attendee_relations, summary)
            
            # 创建主题节点和关系
            session.execute_write(self._create_topic_relations, summary)
    
    @staticmethod
    def _create_meeting_node(tx, summary):
        query = """
        MERGE (m:Meeting {id: $meeting_id})
        SET m.title = $title,
            m.date = $date,
            m.project = $project,
            m.summary = $summary
        RETURN m
        """
        result = tx.run(query,
            meeting_id=f"meeting-{summary.meeting.id}",
            title=summary.title,
            date=summary.meeting.meeting_date.isoformat(),
            project=summary.project.title,
            summary=summary.summary_text
        )
        return result.single()[0]
    
    @staticmethod
    def _create_attendee_relations(tx, summary):
        """创建参会人员关系"""
        meeting_id = f"meeting-{summary.meeting.id}"
        
        for participant in summary.meeting.participants.all():
            query = """
            MERGE (p:Person {id: $person_id})
            SET p.name = $name
            WITH p
            MATCH (m:Meeting {id: $meeting_id})
            MERGE (p)-[:ATTENDED]->(m)
            """
            tx.run(query,
                person_id=f"person-{participant.id}",
                name=participant.get_full_name() or participant.username,
                meeting_id=meeting_id
            )
    
    def search_related_meetings(self, keywords: List[str], project_id: int = None):
        """搜索相关会议"""
        with self.driver.session() as session:
            query = """
            MATCH (m:Meeting)
            WHERE ANY(keyword IN $keywords WHERE m.summary CONTAINS keyword)
            """
            if project_id:
                query += " AND m.project = $project"
            
            query += """
            RETURN m.id, m.title, m.date, m.summary
            ORDER BY m.date DESC
            LIMIT 10
            """
            
            result = session.run(query, 
                keywords=keywords,
                project=f"project-{project_id}" if project_id else None
            )
            
            return [dict(record) for record in result]
```

### 7.4 文档生成服务

```python
# meeting_assistant/services/document_service.py
from django.conf import settings
import os

class DocumentService:
    """文档生成服务"""
    
    def export_markdown(self, summary):
        """导出Markdown格式"""
        content = self._generate_markdown_content(summary)
        
        # 保存到MinIO
        filename = f"meeting_{summary.meeting.id}_{summary.generated_at.strftime('%Y%m%d')}.md"
        file_path = self._save_to_storage(filename, content.encode('utf-8'))
        
        return file_path
    
    def export_pdf(self, summary):
        """导出PDF格式"""
        # 先生成Markdown,再转PDF
        from markdown2 import markdown
        from weasyprint import HTML
        
        md_content = self._generate_markdown_content(summary)
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: "Microsoft YaHei", Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #333; border-bottom: 2px solid #0066cc; }}
                h2 {{ color: #0066cc; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            {markdown(md_content, extras=['tables'])}
        </body>
        </html>
        """
        
        filename = f"meeting_{summary.meeting.id}_{summary.generated_at.strftime('%Y%m%d')}.pdf"
        temp_path = f"/tmp/{filename}"
        HTML(string=html_content).write_pdf(temp_path)
        
        with open(temp_path, 'rb') as f:
            file_path = self._save_to_storage(filename, f.read())
        
        os.remove(temp_path)
        return file_path
    
    def export_docx(self, summary):
        """导出Word格式"""
        from docx import Document
        from docx.shared import Pt, RGBColor
        
        doc = Document()
        
        # 标题
        title = doc.add_heading(summary.title, level=1)
        
        # 基本信息
        doc.add_heading('基本信息', level=2)
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Light Grid Accent 1'
        
        cells = table.rows[0].cells
        cells[0].text = '项目'
        cells[1].text = summary.project.title
        
        cells = table.rows[1].cells
        cells[0].text = '会议时间'
        cells[1].text = str(summary.meeting.meeting_date)
        
        cells = table.rows[2].cells
        cells[0].text = '参会人员'
        cells[1].text = ', '.join([p.get_full_name() for p in summary.meeting.participants.all()])
        
        # 会议摘要
        doc.add_heading('会议摘要', level=2)
        doc.add_paragraph(summary.summary_text)
        
        # 讨论要点
        doc.add_heading('讨论要点', level=2)
        for point in summary.key_points:
            doc.add_paragraph(point, style='List Bullet')
        
        # 决策事项
        doc.add_heading('决策事项', level=2)
        for decision in summary.decisions:
            p = doc.add_paragraph(decision, style='List Bullet')
        
        # 待办任务
        if summary.action_items:
            doc.add_heading('待办任务', level=2)
            task_table = doc.add_table(rows=len(summary.action_items)+1, cols=3)
            task_table.style = 'Light Grid Accent 1'
            
            hdr_cells = task_table.rows[0].cells
            hdr_cells[0].text = '任务'
            hdr_cells[1].text = '负责人'
            hdr_cells[2].text = '截止时间'
            
            for idx, item in enumerate(summary.action_items):
                row_cells = task_table.rows[idx+1].cells
                row_cells[0].text = item.get('task', '')
                row_cells[1].text = item.get('assignee', '')
                row_cells[2].text = item.get('deadline', '')
        
        # 保存
        filename = f"meeting_{summary.meeting.id}_{summary.generated_at.strftime('%Y%m%d')}.docx"
        temp_path = f"/tmp/{filename}"
        doc.save(temp_path)
        
        with open(temp_path, 'rb') as f:
            file_path = self._save_to_storage(filename, f.read())
        
        os.remove(temp_path)
        return file_path
    
    def _generate_markdown_content(self, summary):
        """生成Markdown内容"""
        md = f"""# {summary.title}

## 基本信息

- **项目**: {summary.project.title}
- **会议时间**: {summary.meeting.meeting_date}
- **参会人员**: {', '.join([p.get_full_name() for p in summary.meeting.participants.all()])}
- **生成时间**: {summary.generated_at}

## 会议摘要

{summary.summary_text}

## 讨论要点

"""
        for point in summary.key_points:
            md += f"- {point}\n"
        
        md += "\n## 决策事项\n\n"
        for decision in summary.decisions:
            md += f"- ✅ {decision}\n"
        
        if summary.action_items:
            md += "\n## 待办任务\n\n"
            md += "| 任务 | 负责人 | 截止时间 |\n"
            md += "|------|--------|----------|\n"
            for item in summary.action_items:
                md += f"| {item.get('task', '')} | {item.get('assignee', '')} | {item.get('deadline', '')} |\n"
        
        return md
    
    def _save_to_storage(self, filename, content):
        """保存到MinIO"""
        from .storage_service import upload_document
        return upload_document(filename, content)
```

---

## 8. 前端集成方案

### 8.1 会议录制界面

```html
<!-- meeting_assistant/templates/meeting_record.html -->
{% extends "base.html" %}

{% block content %}
<div class="meeting-recorder">
    <h2>{{ meeting.project.title }} - 评审会议</h2>
    
    <div class="recorder-controls">
        <button id="start-record" class="btn btn-primary">
            <i class="icon-mic"></i> 开始录音
        </button>
        <button id="stop-record" class="btn btn-danger" disabled>
            <i class="icon-stop"></i> 停止录音
        </button>
        <button id="upload-audio" class="btn btn-secondary">
            <i class="icon-upload"></i> 上传音频文件
        </button>
    </div>
    
    <div class="realtime-transcript">
        <h3>实时转写</h3>
        <div id="transcript-container" class="transcript-box">
            <!-- 实时转写内容将显示在这里 -->
        </div>
    </div>
    
    <div class="recording-status">
        <span>录音时长: <span id="duration">00:00:00</span></span>
        <span>状态: <span id="status">未开始</span></span>
    </div>
</div>

<script src="{% static 'js/recorder.js' %}"></script>
<script>
const recorder = new MeetingRecorder({
    meetingId: {{ meeting.id }},
    wsUrl: 'ws://{{ request.get_host }}/ws/transcribe/',
    apiUrl: '/api/meeting-assistant/'
});
</script>
{% endblock %}
```

### 8.2 会议纪要展示

```html
<!-- meeting_assistant/templates/meeting_summary.html -->
{% extends "base.html" %}

{% block content %}
<div class="meeting-summary">
    <div class="summary-header">
        <h2>{{ summary.title }}</h2>
        <div class="actions">
            <button class="btn" onclick="exportSummary('markdown')">导出Markdown</button>
            <button class="btn" onclick="exportSummary('pdf')">导出PDF</button>
            <button class="btn" onclick="exportSummary('docx')">导出Word</button>
            <button class="btn" onclick="syncToReview()">同步到评审系统</button>
        </div>
    </div>
    
    <div class="summary-content">
        <section>
            <h3>基本信息</h3>
            <table>
                <tr><td>项目</td><td>{{ summary.project.title }}</td></tr>
                <tr><td>会议时间</td><td>{{ summary.meeting.meeting_date }}</td></tr>
                <tr><td>参会人员</td><td>{{ summary.meeting.participants.all|join:", " }}</td></tr>
            </table>
        </section>
        
        <section>
            <h3>会议摘要</h3>
            <p>{{ summary.summary_text }}</p>
        </section>
        
        <section>
            <h3>讨论要点</h3>
            <ul>
                {% for point in summary.key_points %}
                <li>{{ point }}</li>
                {% endfor %}
            </ul>
        </section>
        
        <section>
            <h3>决策事项</h3>
            <ul>
                {% for decision in summary.decisions %}
                <li>✅ {{ decision }}</li>
                {% endfor %}
            </ul>
        </section>
        
        <section>
            <h3>待办任务</h3>
            <table class="action-items">
                <thead>
                    <tr>
                        <th>任务</th>
                        <th>负责人</th>
                        <th>截止时间</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in summary.action_items %}
                    <tr>
                        <td>{{ item.task }}</td>
                        <td>{{ item.assignee }}</td>
                        <td>{{ item.deadline }}</td>
                        <td><input type="checkbox"></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
    </div>
</div>

<script>
function exportSummary(format) {
    window.location.href = `/api/meeting-assistant/summaries/{{ summary.id }}/export/?format=${format}`;
}

function syncToReview() {
    fetch(`/api/meeting-assistant/meetings/{{ summary.meeting.id }}/sync-opinions/`, {
        method: 'POST',
        headers: {'X-CSRFToken': '{{ csrf_token }}'}
    })
    .then(res => res.json())
    .then(data => alert(data.message));
}
</script>
{% endblock %}
```

---

## 9. Django Settings配置

```python
# settings.py 新增配置

# ========== 会议助手配置 ==========

# FunASR配置
FUNASR_MODEL_DIR = os.path.join(BASE_DIR, 'models', 'funasr')
FUNASR_DEVICE = 'cuda'  # or 'cpu'

# MinIO配置(音频文件存储)
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_BUCKET_AUDIO = 'meeting-audios'
MINIO_BUCKET_DOCS = 'meeting-docs'

# Neo4j配置
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# Celery配置(如果还没有)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分钟超时

# Ollama配置(本地LLM)
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')

# WebSocket配置(Django Channels)
ASGI_APPLICATION = 'your_project.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# 添加新应用
INSTALLED_APPS = [
    # ... 现有应用
    'meeting_assistant',
    'rest_framework',
    'channels',  # WebSocket支持
]

# 文件上传配置
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'meeting_assistant.log'),
        },
    },
    'loggers': {
        'meeting_assistant': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## 10. 部署方案

### 10.1 Docker Compose部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Django Web服务
  web:
    build: .
    command: gunicorn your_project.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis
      - neo4j
      - minio
  
  # Celery Worker
  celery:
    build: .
    command: celery -A your_project worker -l info -Q default,audio_processing,nlp_processing
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - redis
      - db
  
  # PostgreSQL
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=review_platform
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your_password
  
  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  # Neo4j
  neo4j:
    image: neo4j:5.15
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/your_password
    volumes:
      - neo4j_data:/data
  
  # MinIO
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
  
  # Ollama
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  neo4j_data:
  minio_data:
  ollama_data:
  static_volume:
  media_volume:
```

---

## 11. 迁移与集成步骤

### 11.1 数据库迁移

```bash
# 1. 创建meeting_assistant应用
python manage.py startapp meeting_assistant

# 2. 配置settings.py

# 3. 生成迁移文件
python manage.py makemigrations meeting_assistant

# 4. 执行迁移
python manage.py migrate meeting_assistant
```

### 11.2 集成步骤

**Week 1-2: 环境准备**
- 搭建开发环境(Docker Compose)
- 安装FunASR及依赖
- 配置MinIO和Neo4j

**Week 3-4: Django集成**
- 创建meeting_assistant应用
- 实现数据模型
- 开发基础API

**Week 5-7: 核心服务**
- 集成FunASR服务
- 实现NLP处理
- 开发Celery任务

**Week 8-9: 前端开发**
- 录音界面
- 纪要展示页面
- 与现有页面集成

**Week 10-11: 高级功能**
- 知识图谱构建
- 文档导出
- 搜索功能

**Week 12: 测试上线**
- 单元测试
- 集成测试
- 部署上线

---

## 12. 优化建议

### 12.1 性能优化

1. **数据库索引**
```sql
CREATE INDEX idx_transcript_recording ON meeting_transcript(recording_id, start_time);
CREATE INDEX idx_summary_meeting ON meeting_summary(meeting_id);
CREATE INDEX idx_opinion_summary ON review_opinion(summary_id);
```

2. **缓存策略**
```python
from django.core.cache import cache

def get_meeting_summary(meeting_id):
    cache_key = f'meeting_summary_{meeting_id}'
    summary = cache.get(cache_key)
    if not summary:
        summary = MeetingSummary.objects.get(meeting_id=meeting_id)
        cache.set(cache_key, summary, timeout=3600)
    return summary
```

3. **异步处理**
- 音频上传后立即返回,后台处理
- 使用Celery队列管理任务优先级
- 实现进度追踪

### 12.2 用户体验优化

1. **实时反馈**
- WebSocket推送处理进度
- 显示转写实时结果
- 进度条显示

2. **编辑功能**
- 支持手动编辑纪要
- 修正说话人标注
- 添加/删除意见

3. **模板定制**
- 可配置纪要模板
- 自定义导出格式
- 个性化设置

---

## 13. 测试计划

### 13.1 单元测试

```python
from django.test import TestCase
from meeting_assistant.services.asr_service import FunASRService

class ASRServiceTest(TestCase):
    def test_transcribe(self):
        service = FunASRService()
        result = service.transcribe_with_diarization('test.wav')
        self.assertIsInstance(result, list)
```

### 13.2 集成测试

```python
from django.test import Client

class MeetingIntegrationTest(TestCase):
    def test_upload_and_process(self):
        client = Client()
        with open('test.wav', 'rb') as audio:
            response = client.post('/api/meeting-assistant/recordings/upload/',
                                  {'meeting_id': 1, 'audio_file': audio})
        self.assertEqual(response.status_code, 200)
```

---

## 14. 风险评估

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| Django版本兼容性 | 低 | 中 | 虚拟环境隔离,提前测试 |
| 数据库迁移失败 | 中 | 高 | 备份数据,分步迁移 |
| FunASR性能不足 | 中 | 中 | GPU加速,模型优化 |
| 知识图谱复杂度 | 低 | 中 | 简化实现,分阶段推进 |

---

## 15. 成本与ROI分析

### 15.1 成本估算

**开发成本:** ¥180,000
- 后端集成: 2人 × 6周 = ¥120,000
- 前端集成: 1人 × 4周 = ¥40,000
- 测试优化: 1人 × 2周 = ¥20,000

**硬件成本:** ¥30,000
- GPU服务器: ¥25,000
- 存储扩容: ¥5,000

**总投入:** ¥210,000

### 15.2 收益分析

**效率提升:**
- 每场评审节省45分钟
- 每月10场 = 7.5小时
- 月节省¥1,500

**预计ROI:**
- 年收益: ¥50,000+
- 回本周期: 5-6个月

---

## 16. 实施时间线

| 阶段 | 周数 | 任务 | 交付物 |
|------|------|------|--------|
| Phase 0 | Week 1 | 环境搭建 | 开发环境 |
| Phase 1 | Week 2-4 | Django集成 | 基础功能 |
| Phase 2 | Week 5-7 | 服务开发 | 转写+纪要 |
| Phase 3 | Week 8-9 | 前端集成 | 完整UI |
| Phase 4 | Week 10-11 | 高级功能 | 全功能版 |
| Phase 5 | Week 12 | 测试上线 | 生产就绪 |

**里程碑:**
- M1 (Week 4): 基础集成完成
- M2 (Week 7): 转写和纪要可用
- M3 (Week 9): 前端集成完成
- M4 (Week 12): 正式上线

---

## 17. 附录

### 17.1 快速开始

```bash
# 1. 克隆项目
git clone <your-project>
cd <your-project>

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
docker-compose up -d

# 4. 运行迁移
python manage.py migrate

# 5. 启动开发服务器
python manage.py runserver

# 6. 启动Celery
celery -A your_project worker -l info
```

### 17.2 参考资源

- FunASR: https://github.com/alibaba-damo-academy/FunASR
- Neo4j: https://neo4j.com/
- Django: https://www.djangoproject.com/
- Celery: https://docs.celeryq.dev/

---

## 18. 总结

### 18.1 方案优势

✅ 无缝集成 - Django应用深度整合  
✅ 渐进式迁移 - 不影响现有功能  
✅ 技术成熟 - 全开源技术栈  
✅ 成本可控 - 预算约21万元  
✅ 扩展性强 - 模块化设计  

### 18.2 关键成功因素

1. 充分调研现有系统
2. 分阶段实施
3. 用户培训
4. 持续优化

### 18.3 下一步行动

- [ ] 确认项目立项
- [ ] 分析Django代码结构
- [ ] 准备测试数据
- [ ] 搭建开发环境
- [ ] 开始开发

---

**文档版本:** 2.0  
**最后更新:** 2026-01-28  
**维护:** 持续更新
