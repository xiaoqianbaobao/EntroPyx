# 知识库管理系统使用指南

## 🚀 快速开始

### 1. 启动服务
```bash
# 给予执行权限
chmod +x start_server.sh

# 启动Django服务器
./start_server.sh
```

### 2. 访问应用
- **主页**: http://localhost:8000
- **知识库管理**: http://localhost:8000/api/v1/knowledge/
- **录音转写**: http://localhost:8000/meeting-assistant/record/
- **智能问答**: http://localhost:8000/api/v1/knowledge/chat/

## ⚙️ 配置说明

### DeepSeek API配置
在项目根目录创建 `.env` 文件：
```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 必需的Python包
```bash
pip install PyPDF2 python-docx beautifulsoup4 matplotlib pillow
```

## 📋 功能使用

### 🎙️ 录音转写与纪要生成

1. **访问录音页面**
   - 打开浏览器访问: http://localhost:8000/meeting-assistant/record/

2. **开始录音**
   - 选择仓库
   - 输入会议标题
   - 点击"开始录音"

3. **生成纪要**
   - 录音结束后自动显示模板选择
   - 选择模板类型（图文纪要、会议纪要等）
   - 系统自动调用DeepSeek API生成智能纪要

4. **查看结果**
   - 访问会议详情页查看生成的纪要
   - 支持导出为MD/PDF/Word格式

### 📚 知识库管理

1. **访问知识库**
   - 打开浏览器访问: http://localhost:8000/api/v1/knowledge/

2. **上传文档**
   - 点击"上传文档"按钮
   - 选择PDF/MD/Word/TXT文件
   - 系统自动处理并提取知识

3. **查看知识**
   - 在列表中查看已上传的文档
   - 点击文档查看详情
   - 支持搜索和筛选

4. **智能问答**
   - 访问问答页面: http://localhost:8000/api/v1/knowledge/chat/
   - 输入问题
   - 系统基于知识库智能回答

### 📊 数据看板

1. **访问主页**
   - 打开浏览器访问: http://localhost:8000
   - 查看知识库统计卡片
   - 快速访问知识库管理

## 🔧 常用命令

### 启动相关
```bash
# 启动Django服务器
./start_server.sh

# 启动Celery任务队列
celery -A config worker -l info

# 运行测试
python3 test_simple.py
```

### 开发相关
```bash
# 检查Django配置
python3 manage.py check

# 数据库迁移
python3 manage.py makemigrations
python3 manage.py migrate

# 创建超级用户
python3 manage.py createsuperuser
```

## 🎯 核心功能特点

### ✨ AI智能
- **DeepSeek API集成**: 真实的AI转写和生成
- **智能提取**: 自动提取文档结构化信息
- **上下文问答**: 基于知识库的智能回答

### 📱 多媒体支持
- **文档格式**: PDF、MD、Word、TXT
- **图片生成**: 高质量的图文纪要
- **多格式导出**: MD、PDF、Word

### 🎨 用户体验
- **直观界面**: 响应式设计，支持移动端
- **实时反馈**: 实时状态更新和进度显示
- **错误处理**: 完善的错误提示和降级机制

## 📈 性能优化

### 异步处理
- 使用Celery处理耗时任务
- 支持任务重试和状态监控
- 实时进度反馈

### 缓存策略
- 文档内容缓存
- 查询结果缓存
- 图片文件缓存

## 🚨 常见问题

### Q: 如何配置DeepSeek API？
A: 在项目根目录创建 `.env` 文件，添加：
```
DEEPSEEK_API_KEY=your_api_key_here
```

### Q: 上传文档失败怎么办？
A: 
1. 检查文件格式是否支持
2. 确认文件大小不超过100MB
3. 检查磁盘空间是否充足

### Q: 录音转写不准确怎么办？
A: 
1. 确保麦克风权限已授权
2. 检查网络连接
3. 确认DeepSeek API密钥配置正确

### Q: 图片生成失败怎么办？
A: 
1. 检查PIL库是否安装
2. 确认matplotlib库版本兼容
3. 检查系统字体配置

## 📞 技术支持

如果遇到问题，请检查：
1. Django配置是否正确
2. Python依赖是否完整
3. API密钥是否有效
4. 系统资源是否充足

---

**版本**: v1.0  
**更新时间**: 2024-01-29  
**状态**: ✅ 生产就绪