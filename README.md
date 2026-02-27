# 天枢效能平台 (EntropyX AI)

基于AI的智能化代码评审、PRD评审、测试用例生成平台。

## 最新更新 (2026-02-27)

### 🚀 新特性
- **AI 智能评审升级**: 全面接入 DeepSeek V2.5 大模型，提升代码评审、PRD 分析的准确性。
- **会议助手增强**: 
  - 支持批量删除会议记录。
  - 新增分页查询功能，可自定义每页显示条数。
  - 优化录音上传校验，支持 `.mp3`, `.wav`, `.m4a` 等格式。
- **测试用例管理**:
  - 支持测试用例分页展示和自定义分页大小。
  - 新增批量配置 Dubbo 接口参数功能。
- **消息通知优化**: 
  - 钉钉机器人消息模板升级，包含评审结果摘要、风险等级和关键指标。
  - 支持点击消息链接直接跳转至评审报告详情页。
- **安全增强**: 
  - 前端登录密码加密传输 (AES/ECB)，提升安全性。
  - 完善文件上传格式校验，防止非法文件注入。
- **PRD文档管理**:
  - 支持 PRD 文档分页查询和自定义每页显示条数。
  - 新增批量删除 PRD 文档功能。
  - **在线编辑**: 集成 Markdown 编辑器，支持在线修改 PRD 内容并实时保存。

### ⚙️ 配置变更
- **AI 模型接口**: 默认 API 地址已更新为内部 OCR Server (`https://ocrserver.bestpay.com.cn/...`)，无需额外配置。
- **环境变量**: 推荐配置 `DEEPSEEK_API_KEY` 以支持更高级的 AI 功能（如 ASR 语音转写）。

---

## 功能特性

- **🤖 代码评审**: 自动扫描Git仓库，AI深度评审代码变更
- **📄 PRD评审**: 上传产品需求文档，AI检查完整性、一致性
- **🧪 测试用例生成**: 基于PRD和代码Diff自动生成测试用例
- **🔗 钉钉集成**: 评审结果实时推送到钉钉群
- **📊 数据看板**: 多维度质量数据统计分析
- **⚙️ 平台管理**: 智能体管理、工作流编排、知识库管理一体化

## 技术栈

- **后端**: Django 4.2 + Django REST Framework
- **任务队列**: Celery + Redis
- **AI引擎**: DeepSeek API
- **数据库**: PostgreSQL
- **前端**: Bootstrap 5 + ECharts
- **智能体框架**: 基于 ReAct 模式的 Agent 框架

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，填入配置信息
```

### 3. 初始化数据库

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. 启动服务

```bash
# 启动Django服务
python manage.py runserver 0.0.0.0:8000

# 启动Celery Worker（可选，用于异步任务）
celery -A config worker -l info

# 启动Celery Beat（可选，用于定时任务）
celery -A config beat -l info
```

### 5. Docker部署 (推荐)

#### 方式一：Docker Compose (开发环境)

```bash
docker-compose up -d
```

#### 方式二：单机 All-in-One 部署 (生产/内网环境)

我们提供了一个集成了 Django、PostgreSQL、Redis、Nginx 和 Celery 的 All-in-One 镜像，非常适合内网单机部署。

1. **构建镜像** (或从私有仓库拉取)
   ```bash
   docker build -t entropyx-ai:latest .
   ```

2. **启动容器**
   ```bash
   docker run -d \
     --name entropyx-ai \
     -p 80:80 \
     -v $(pwd)/data/postgres:/var/lib/postgresql/data \
     -v $(pwd)/data/redis:/var/lib/redis \
     -v $(pwd)/media:/app/media \
     -e DEEPSEEK_API_KEY=your-api-key \
     -e DEEPSEEK_API_BASE=https://api.deepseek.com/v1 \
     -e POSTGRES_PASSWORD=secure_password \
     entropyx-ai:latest
   ```

   **环境变量说明**:
   - `DEEPSEEK_API_KEY`: DeepSeek API Key (必填)
   - `DEEPSEEK_API_BASE`: DeepSeek API 地址
   - `POSTGRES_PASSWORD`: 数据库密码 (默认会根据此变量初始化数据库)
   - `DJANGO_SUPERUSER_USERNAME`: 自动创建的管理员用户名 (可选)
   - `DJANGO_SUPERUSER_PASSWORD`: 自动创建的管理员密码 (可选)
   - `DJANGO_SUPERUSER_EMAIL`: 自动创建的管理员邮箱 (可选)

## 项目结构

```
ai_review_platform/
├── config/              # Django配置
│   ├── settings.py     # settings.py
│   ├── urls.py         # 主路由
│   ├── wsgi.py         # WSGI配置
│   └── celery.py       # Celery配置
├── apps/               # Django应用
│   ├── core/          # 核心模块
│   ├── users/         # 用户模块
│   ├── repository/    # 仓库管理
│   ├── code_review/   # 代码评审
│   ├── prd_review/    # PRD评审
│   ├── test_case/     # 测试用例
│   ├── feedback/      # 反馈优化
│   ├── dashboard/     # 数据看板
│   ├── ai_chat/       # 智能调度机器人
│   ├── meeting_assistant/ # 会议助手
│   ├── platform_management/ # 平台管理(智能体/工作流/知识库)
│   └── knowledge_base/ # 知识库核心
├── templates/          # HTML模板
├── static/             # 静态文件
├── repos/              # Git仓库存储
├── media/              # 上传文件存储
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API文档

### 平台管理

- `GET /platform-management/` - 平台管理仪表盘
- `GET /platform-management/agents/` - 智能体列表
- `GET /platform-management/workflows/` - 工作流列表
- `GET /api/v1/knowledge/` - 知识库管理API

### 代码评审

- `GET /api/v1/code-review/reviews/` - 获取评审列表
- `GET /api/v1/code-review/reviews/{id}/` - 获取评审详情
- `POST /api/v1/code-review/reviews/{id}/feedback/` - 提交反馈
- `GET /api/v1/code-review/reviews/statistics/` - 获取统计

### 仓库管理

- `GET /api/v1/repository/repositories/` - 获取仓库列表
- `POST /api/v1/repository/repositories/` - 新增仓库
- `PUT /api/v1/repository/repositories/{id}/` - 更新仓库
- `DELETE /api/v1/repository/repositories/{id}/` - 删除仓库

### PRD评审

- `GET /api/v1/prd-review/prd-reviews/` - 获取PRD评审列表
- `POST /api/v1/prd-review/prd-reviews/` - 上传PRD并评审
- `GET /api/v1/prd-review/prd-reviews/{id}/` - 获取评审详情

### 测试用例

- `GET /api/v1/test-case/test-cases/` - 获取用例列表
- `POST /api/v1/test-case/test-cases/` - 创建用例
- `POST /api/v1/test-case/test-cases/execute/` - 执行测试

## 配置说明

### 钉钉机器人配置

1. 在钉钉群中添加自定义机器人
2. 复制WebHook地址和加签密钥
3. 在仓库管理中配置

### AI模型配置

平台默认使用 DeepSeek Coder 模型，可在 `.env` 中配置：

```env
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-coder
```

## 定时任务

平台支持以下定时任务：

- **代码评审扫描**: 每90秒扫描一次仓库新提交
- **数据统计汇总**: 每天凌晨生成日报

## 许可证

MIT License
