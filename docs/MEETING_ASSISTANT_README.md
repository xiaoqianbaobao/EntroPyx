# 会议助手功能说明

## 功能概述

会议助手(AI Meeting Assistant)是熵减X-AI平台的一个新功能，用于自动化处理评审会议的音频录制、语音转写和纪要生成。

## 核心功能

### 1. 会议录音上传
- 支持上传音频文件(MP3, WAV, M4A等格式)
- 关联到具体的仓库项目
- 记录会议基本信息(标题、时间、参会人员)

### 2. 语音转写
- 自动将音频转换为文本
- 支持说话人分离
- 记录时间戳和置信度

### 3. 智能纪要生成
- 自动提取会议摘要
- 识别讨论要点
- 提取决策事项
- 生成待办任务列表
- 分类评审意见(问题、建议、决策、风险)

### 4. 文档导出
- 支持导出为Markdown格式
- 支持导出为PDF格式
- 支持导出为Word格式

### 5. 评审意见管理
- 从会议纪要中自动提取评审意见
- 支持意见分类和优先级设置
- 支持标记解决状态

## 技术架构

### 数据模型
- `MeetingRecording`: 会议录音记录
- `MeetingTranscript`: 会议转写文本
- `MeetingSummary`: 会议纪要
- `ReviewOpinion`: 评审意见

### 核心服务
- `ASRService`: 语音识别服务(支持Mock和FunASR)
- `NLPService`: 自然语言处理服务(支持规则和LLM)
- `DocumentService`: 文档生成服务

### 异步任务
- `process_audio_task`: 处理音频文件
- `generate_summary_task`: 生成会议纪要
- `export_document_task`: 导出文档

## 使用说明

### 1. 访问会议列表
URL: `/meeting-assistant/`

### 2. 上传会议录音
URL: `/meeting-assistant/upload/`

步骤：
1. 选择关联的仓库
2. 填写会议标题
3. 选择会议时间(可选)
4. 填写参会人员(可选)
5. 上传音频文件
6. 点击"开始上传"

### 3. 查看会议详情
URL: `/meeting-assistant/detail/<id>/`

功能：
- 查看会议基本信息
- 播放录音
- 查看转写文本
- 生成会议纪要

### 4. 查看会议纪要
URL: `/meeting-assistant/summary/<id>/`

功能：
- 查看完整纪要内容
- 导出文档(Markdown/PDF/Word)
- 查看评审意见列表

## API接口

### 录音管理
- `GET /meeting-assistant/api/recordings/` - 获取录音列表
- `GET /meeting-assistant/api/recordings/<id>/` - 获取录音详情
- `POST /meeting-assistant/api/recordings/upload/` - 上传录音
- `GET /meeting-assistant/api/recordings/<id>/audio/` - 播放录音
- `GET /meeting-assistant/api/recordings/<id>/status/` - 获取处理状态

### 纪要管理
- `GET /meeting-assistant/api/summaries/` - 获取纪要列表
- `GET /meeting-assistant/api/summaries/<id>/` - 获取纪要详情
- `POST /meeting-assistant/api/recordings/<id>/generate-summary/` - 生成纪要
- `GET /meeting-assistant/api/summaries/<id>/export/?format=<format>` - 导出文档

### 评审意见
- `GET /meeting-assistant/api/opinions/` - 获取意见列表
- `GET /meeting-assistant/api/opinions/<id>/` - 获取意见详情
- `PUT /meeting-assistant/api/opinions/<id>/` - 更新意见

## 配置说明

### 环境变量

在`.env`文件中可以配置以下变量：

```env
# ASR服务类型 (mock, funasr)
ASR_SERVICE_TYPE=mock

# NLP服务类型 (rule, llm)
NLP_SERVICE_TYPE=rule

# 如果使用LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

### 安装依赖

```bash
# 基础依赖
pip install -r requirements.txt

# 如果使用FunASR
pip install funasr

# 如果使用LLM
pip install ollama

# 如果需要PDF导出
pip install weasyprint

# 如果需要Word导出
pip install python-docx

# 如果需要中文分词
pip install jieba
```

## 部署说明

### 1. 数据库迁移
```bash
python manage.py makemigrations meeting_assistant
python manage.py migrate meeting_assistant
```

### 2. 启动Celery Worker
```bash
celery -A config worker -l info
```

### 3. 启动Django服务
```bash
python manage.py runserver
```

## 注意事项

1. **当前版本说明**：
   - ASR服务使用Mock模拟数据，实际使用需要集成真实的ASR服务
   - NLP服务使用规则方法，可以升级到LLM以获得更好的效果
   - 文档导出功能需要安装相应的依赖库

2. **性能优化**：
   - 音频文件大小建议不超过100MB
   - 转写和纪要生成是异步处理，需要Celery支持
   - 建议使用Redis作为Celery的broker

3. **安全考虑**：
   - 音频文件上传需要验证文件类型和大小
   - 用户权限控制需要根据实际需求配置
   - 建议在生产环境中使用HTTPS

## 未来改进

1. **实时录音**：支持在浏览器中直接录音
2. **实时转写**：使用WebSocket实现实时转写显示
3. **知识图谱**：构建会议知识图谱，支持智能检索
4. **多语言支持**：支持英语等其他语言的转写
5. **语音合成**：支持将纪要转换为语音播放

## 技术支持

如有问题，请联系开发团队。