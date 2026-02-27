# 熵减X-AI

基于AI的智能化代码评审、PRD评审、测试用例生成平台。

## 功能特性

- **🤖 代码评审**: 自动扫描Git仓库，AI深度评审代码变更
- **📄 PRD评审**: 上传产品需求文档，AI检查完整性、一致性
- **🧪 测试用例生成**: 基于PRD和代码Diff自动生成测试用例
- **🔗 钉钉集成**: 评审结果实时推送到钉钉群
- **📊 数据看板**: 多维度质量数据统计分析

## 技术栈

- **后端**: Django 4.2 + Django REST Framework
- **任务队列**: Celery + Redis
- **AI引擎**: DeepSeek API
- **数据库**: PostgreSQL
- **前端**: Bootstrap 5 + ECharts

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

### 5. Docker部署

```bash
docker-compose up -d
```

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
│   └── dashboard/     # 数据看板
├── templates/          # HTML模板
├── static/             # 静态文件
├── repos/              # Git仓库存储
├── media/              # 上传文件存储
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API文档

### 代码评审

- `GET /api/code-review/reviews/` - 获取评审列表
- `GET /api/code-review/reviews/{id}/` - 获取评审详情
- `POST /api/code-review/reviews/{id}/feedback/` - 提交反馈
- `GET /api/code-review/reviews/statistics/` - 获取统计

### 仓库管理

- `GET /api/repository/repositories/` - 获取仓库列表
- `POST /api/repository/repositories/` - 新增仓库
- `PUT /api/repository/repositories/{id}/` - 更新仓库
- `DELETE /api/repository/repositories/{id}/` - 删除仓库

### PRD评审

- `GET /api/prd-review/prd-reviews/` - 获取PRD评审列表
- `POST /api/prd-review/prd-reviews/` - 上传PRD并评审
- `GET /api/prd-review/prd-reviews/{id}/` - 获取评审详情

### 测试用例

- `GET /api/test-case/test-cases/` - 获取用例列表
- `POST /api/test-case/test-cases/` - 创建用例
- `POST /api/test-case/test-cases/execute/` - 执行测试

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
