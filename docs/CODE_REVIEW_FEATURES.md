# 代码评审模块 - 多触发模式功能说明

## 功能概述

代码评审模块现已支持**四种触发模式**，满足不同场景下的代码评审需求：

1. **手动触发** - 用户主动触发评审
2. **定时任务** - 按照预设时间自动批量评审
3. **实时监控** - 监控代码提交，实时触发评审
4. **Webhook触发** - GitLab/GitHub推送时自动触发

## 使用场景

### 场景1：开发者提交代码后立即收到评审

**需求：** 作为开发者，我希望我写完代码提交后，立马就能在钉钉群收到我这次提交的代码评审，然后我可以根据评审内容修改代码。

**解决方案：** 使用**实时监控**模式

**配置步骤：**
```bash
# 1. 启用实时监控
POST /api/v1/code-reviews/realtime-configs/
{
    "repository": 1,
    "is_active": true,
    "monitored_branches": ["master", "develop"],
    "check_interval": 60,
    "auto_review": true,
    "notify_on_new_commit": true,
    "notify_level": "MEDIUM"
}

# 2. 开发者提交代码
git add .
git commit -m "feat: 添加新功能"
git push origin master

# 3. 系统自动检测并评审
# Celery每分钟检查一次，发现新提交后自动触发评审

# 4. 钉钉群收到通知
【代码评审通知】
仓库: settle-center
分支: master
作者: 张三
提交: abc1234 - feat: 添加新功能

📊 风险等级: 中风险 (0.65)
📝 变更文件: 3个
➕ 新增: 120行
➖ 删除: 45行

🔍 评审要点:
1. 潜在的SQL注入风险
2. 缺少输入验证
3. 异常处理不完善

📌 建议: 请尽快修复高风险问题
```

### 场景2：每天定时批量评审

**需求：** 每天定时批量触发一次，比如中午12点和傍晚18点。

**解决方案：** 使用**定时任务**模式

**配置步骤：**
```bash
# 1. 创建中午12点的定时任务
POST /api/v1/code-reviews/scheduled-configs/
{
    "name": "中午批量评审",
    "description": "每天中午12点批量评审所有仓库",
    "repositories": [1, 2, 3],
    "cron_expression": "0 12 * * *",
    "branches": ["master", "develop"],
    "is_active": true
}

# 2. 创建傍晚18点的定时任务
POST /api/v1/code-reviews/scheduled-configs/
{
    "name": "傍晚批量评审",
    "description": "每天傍晚18点批量评审所有仓库",
    "repositories": [1, 2, 3],
    "cron_expression": "0 18 * * *",
    "branches": ["master", "develop"],
    "is_active": true
}

# 3. Celery Beat自动执行
# 每天12:00和18:00自动触发批量评审

# 4. 钉钉群收到汇总通知
【代码评审汇总】
时间: 2026-01-23 12:00
配置: 中午批量评审

📊 评审统计:
- 总提交数: 15
- 高风险: 2
- 中风险: 8
- 低风险: 5
```

### 场景3：手动触发评审

**需求：** 开发者需要立即评审某个分支的代码。

**解决方案：** 使用**手动触发**模式

**配置步骤：**
```bash
# 触发手动评审
POST /api/v1/code-reviews/manual-trigger/
{
    "repository_id": 1,
    "branch": "master",
    "all_branches": false
}

# 查询任务状态
GET /api/v1/code-reviews/task-status/?task_id=manual_1_master_20260123120000
```

### 场景4：GitLab/GitHub推送时自动触发

**需求：** 在GitLab/GitHub中配置Webhook，推送代码时自动触发评审。

**解决方案：** 使用**Webhook触发**模式

**配置步骤：**
```bash
# 1. 在GitLab中配置Webhook
# URL: https://your-domain.com/api/v1/code-reviews/webhook-trigger/
# 触发事件: Push events

# 2. 在GitHub中配置Webhook
# URL: https://your-domain.com/api/v1/code-reviews/webhook-trigger/
# 触发事件: Pushes

# 3. 推送代码时自动触发评审
git push origin master
```

## 技术实现

### 数据模型

#### 1. CodeReview（代码评审记录）
```python
class CodeReview(models.Model):
    # 基本信息
    repository = ForeignKey('Repository')
    branch = CharField()
    commit_hash = CharField()
    commit_message = TextField()
    author = CharField()
    
    # 触发信息
    trigger_mode = CharField(choices=TriggerMode.choices)  # MANUAL/SCHEDULED/REALTIME/WEBHOOK
    triggered_by = ForeignKey('User')
    
    # 评审结果
    risk_score = FloatField()
    risk_level = CharField(choices=RiskLevel.choices)
    ai_review_content = TextField()
    
    # 代码统计
    lines_added = IntegerField()
    lines_deleted = IntegerField()
    lines_changed = IntegerField()
```

#### 2. ReviewTask（评审任务）
```python
class ReviewTask(models.Model):
    task_id = CharField(unique=True)
    repository = ForeignKey('Repository')
    status = CharField(choices=TaskStatus.choices)
    progress = IntegerField()
    
    # 触发信息
    trigger_mode = CharField(choices=TriggerMode.choices)
    triggered_by = ForeignKey('User')
    
    # 评审结果
    high_risk_count = IntegerField()
    medium_risk_count = IntegerField()
    low_risk_count = IntegerField()
```

#### 3. ScheduledReviewConfig（定时评审配置）
```python
class ScheduledReviewConfig(models.Model):
    name = CharField()
    repositories = ManyToManyField('Repository')
    cron_expression = CharField()  # 例如: "0 12 * * *"
    branches = JSONField()
    is_active = BooleanField()
    last_run_at = DateTimeField()
```

#### 4. RealtimeMonitorConfig（实时监控配置）
```python
class RealtimeMonitorConfig(models.Model):
    repository = OneToOneField('Repository')
    is_active = BooleanField()
    monitored_branches = JSONField()
    check_interval = IntegerField()  # 检查间隔（秒）
    auto_review = BooleanField()
    notify_on_new_commit = BooleanField()
    notify_level = CharField(choices=RiskLevel.choices)
    last_checked_commit = CharField()
```

### Celery任务

#### 1. code_review_task（代码评审任务）
```python
@shared_task(bind=True, max_retries=3)
def code_review_task(self, repository_id, branch, task_id=None, 
                     all_branches=False, trigger_mode='MANUAL', 
                     triggered_by_id=None):
    # 1. 克隆/更新仓库
    # 2. 获取提交记录
    # 3. 遍历提交进行评审
    # 4. AI评审代码
    # 5. 保存评审结果
    # 6. 发送钉钉通知
```

#### 2. scheduled_review_task（定时评审任务）
```python
@shared_task
def scheduled_review_task(config_id):
    # 获取定时配置
    # 为每个仓库启动评审任务
```

#### 3. realtime_monitor_task（实时监控任务）
```python
@shared_task
def realtime_monitor_task():
    # 检查所有启用的仓库
    # 发现新提交后触发评审
```

#### 4. webhook_review_task（Webhook触发任务）
```python
@shared_task
def webhook_review_task(repository_id, commit_hash, branch, 
                        author, author_email, commit_message):
    # 检查是否已评审
    # 触发评审任务
```

### Celery Beat配置

```python
app.conf.beat_schedule = {
    # 每天中午12点执行定时评审
    'scheduled-review-noon': {
        'task': 'apps.code_review.tasks.scheduled_review_task',
        'schedule': crontab(hour=12, minute=0),
        'args': (1,),
    },
    
    # 每天傍晚18点执行定时评审
    'scheduled-review-evening': {
        'task': 'apps.code_review.tasks.scheduled_review_task',
        'schedule': crontab(hour=18, minute=0),
        'args': (2,),
    },
    
    # 每分钟执行一次实时监控任务
    'realtime-monitor': {
        'task': 'apps.code_review.tasks.realtime_monitor_task',
        'schedule': crontab(),
    },
}
```

## API接口

### 1. 手动触发评审
```bash
POST /api/v1/code-reviews/manual-trigger/
Content-Type: application/json

{
    "repository_id": 1,
    "branch": "master",
    "all_branches": false
}
```

### 2. 查询任务状态
```bash
GET /api/v1/code-reviews/task-status/?task_id=xxx
```

### 3. Webhook触发
```bash
POST /api/v1/code-reviews/webhook-trigger/
Content-Type: application/json

{
    "repository_id": 1,
    "commit_hash": "abc123...",
    "branch": "master",
    "author": "张三",
    "author_email": "zhangsan@example.com",
    "commit_message": "fix bug"
}
```

### 4. 定时评审配置管理
```bash
# 创建配置
POST /api/v1/code-reviews/scheduled-configs/

# 查看所有配置
GET /api/v1/code-reviews/scheduled-configs/

# 立即运行
POST /api/v1/code-reviews/scheduled-configs/{id}/run_now/

# 启用/禁用
POST /api/v1/code-reviews/scheduled-configs/{id}/toggle_active/

# 更新配置
PUT /api/v1/code-reviews/scheduled-configs/{id}/

# 删除配置
DELETE /api/v1/code-reviews/scheduled-configs/{id}/
```

### 5. 实时监控配置管理
```bash
# 创建配置
POST /api/v1/code-reviews/realtime-configs/

# 查看所有配置
GET /api/v1/code-reviews/realtime-configs/

# 启用/禁用监控
POST /api/v1/code-reviews/realtime-configs/{id}/toggle_active/

# 立即检查
POST /api/v1/code-reviews/realtime-configs/{id}/check_now/
```

## 快速开始

### 1. 启动服务
```bash
# 启动所有服务
./start_code_review_services.sh

# 或手动启动
python3 manage.py runserver
celery -A config worker -l info
celery -A config beat -l info
```

### 2. 测试功能
```bash
# 运行测试脚本
python3 test_code_review_triggers.py
```

### 3. 检查状态
```bash
# 检查服务状态
./check_code_review_services.sh
```

### 4. 查看日志
```bash
# Celery Worker日志
tail -f /tmp/celery.log

# Celery Beat日志
tail -f /tmp/celery-beat.log

# Django应用日志
tail -f logs/app.log
```

## 最佳实践

### 1. 实时监控配置
- 对核心分支（master、develop）启用实时监控
- 设置合理的检查间隔（60秒）
- 根据项目风险等级设置通知级别

### 2. 定时任务配置
- 每天定时评审所有分支，确保不遗漏
- 设置合理的时间点（避开高峰期）
- 配置完成后通知，便于团队了解

### 3. Webhook配置
- 在GitLab/GitHub中配置Webhook
- 确保URL外网可访问
- 配置密钥以保证安全性

### 4. 通知策略
- 高风险项目：只通知HIGH和MEDIUM
- 低风险项目：通知所有级别
- 提供反馈机制，持续优化

## 故障排查

### 问题1：任务一直处于PENDING状态
**原因：** Celery Worker未运行
**解决：** 检查Celery Worker是否启动
```bash
ps aux | grep celery
./start_code_review_services.sh
```

### 问题2：定时任务未执行
**原因：** Celery Beat未运行或配置错误
**解决：** 检查Celery Beat和Cron表达式
```bash
ps aux | grep beat
tail -f /tmp/celery-beat.log
```

### 问题3：实时监控未检测到新提交
**原因：** 监控未启用或配置错误
**解决：** 检查监控配置和分支
```bash
GET /api/v1/code-reviews/realtime-configs/
```

### 问题4：钉钉通知未发送
**原因：** Webhook URL或Secret配置错误
**解决：** 检查钉钉配置
```bash
tail -f logs/app.log | grep dingtalk
```

## 总结

代码评审模块现已支持完整的多种触发模式：

✅ **手动触发** - 用户主动触发评审
✅ **定时任务** - 每天中午12点和傍晚18点自动批量评审
✅ **实时监控** - 监控代码提交，实时触发评审
✅ **Webhook触发** - GitLab/GitHub推送时自动触发

开发者提交代码后，可以立即在钉钉群收到评审结果，根据评审内容修改代码，提高代码质量和开发效率。

详细使用说明请查看：`CODE_REVIEW_GUIDE.md`