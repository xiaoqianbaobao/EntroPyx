# 代码评审模块使用指南

## 概述

代码评审模块支持多种触发模式，满足不同场景的需求：

1. **手动触发** - 用户主动触发评审
2. **定时任务** - 按照预设时间自动批量评审
3. **实时监控** - 监控代码提交，实时触发评审
4. **Webhook触发** - GitLab/GitHub推送时自动触发

## 触发模式详解

### 1. 手动触发

**适用场景：** 开发者提交代码后，主动触发评审查看结果

**API调用：**
```bash
POST /api/v1/code-reviews/manual-trigger/
Content-Type: application/json

{
    "repository_id": 1,
    "branch": "master",
    "all_branches": false
}
```

**响应：**
```json
{
    "message": "评审任务已触发",
    "task_id": "manual_1_master_20260123120000"
}
```

**查询任务状态：**
```bash
GET /api/v1/code-reviews/task-status/?task_id=manual_1_master_20260123120000
```

### 2. 定时任务

**适用场景：** 每天固定时间批量评审所有仓库的代码

**配置定时任务：**
```bash
POST /api/v1/code-reviews/scheduled-configs/
Content-Type: application/json

{
    "name": "中午批量评审",
    "description": "每天中午12点批量评审所有仓库",
    "repositories": [1, 2, 3],
    "cron_expression": "0 12 * * *",
    "branches": ["master", "develop"],
    "review_all_branches": false,
    "is_active": true,
    "notify_on_complete": true,
    "notify_webhook": "https://oapi.dingtalk.com/robot/send?access_token=xxx"
}
```

**Cron表达式说明：**
- `0 12 * * *` - 每天中午12点
- `0 18 * * *` - 每天傍晚18点
- `0 */6 * * *` - 每6小时
- `0 9-18 * * 1-5` - 工作日9点到18点，每小时

**管理定时任务：**
```bash
# 立即运行
POST /api/v1/code-reviews/scheduled-configs/{id}/run_now/

# 启用/禁用
POST /api/v1/code-reviews/scheduled-configs/{id}/toggle_active/

# 查看所有配置
GET /api/v1/code-reviews/scheduled-configs/

# 更新配置
PUT /api/v1/code-reviews/scheduled-configs/{id}/

# 删除配置
DELETE /api/v1/code-reviews/scheduled-configs/{id}/
```

### 3. 实时监控

**适用场景：** 开发者提交代码后，立即收到评审结果

**配置实时监控：**
```bash
POST /api/v1/code-reviews/realtime-configs/
Content-Type: application/json

{
    "repository": 1,
    "is_active": true,
    "monitored_branches": ["master", "develop"],
    "check_interval": 60,
    "auto_review": true,
    "notify_on_new_commit": true,
    "notify_level": "MEDIUM"
}
```

**参数说明：**
- `is_active` - 是否启用监控
- `monitored_branches` - 监控的分支列表
- `check_interval` - 检查间隔（秒），默认60秒
- `auto_review` - 发现新提交后是否自动评审
- `notify_on_new_commit` - 是否发送钉钉通知
- `notify_level` - 通知级别（HIGH/MEDIUM/LOW）

**管理实时监控：**
```bash
# 启用/禁用监控
POST /api/v1/code-reviews/realtime-configs/{id}/toggle_active/

# 立即检查新提交
POST /api/v1/code-reviews/realtime-configs/{id}/check_now/

# 查看所有监控配置
GET /api/v1/code-reviews/realtime-configs/
```

### 4. Webhook触发

**适用场景：** GitLab/GitHub推送代码时自动触发评审

**API调用：**
```bash
POST /api/v1/code-reviews/webhook-trigger/
Content-Type: application/json

{
    "repository_id": 1,
    "commit_hash": "abc123def456...",
    "branch": "master",
    "author": "张三",
    "author_email": "zhangsan@example.com",
    "commit_message": "fix bug: 修复登录问题"
}
```

**GitLab Webhook配置：**
1. 进入GitLab项目设置 -> Webhooks
2. 添加URL: `https://your-domain.com/api/v1/code-reviews/webhook-trigger/`
3. 选择触发事件: Push events
4. 保存

**GitHub Webhook配置：**
1. 进入GitHub仓库设置 -> Webhooks
2. 添加URL: `https://your-domain.com/api/v1/code-reviews/webhook-trigger/`
3. 选择触发事件: Pushes
4. 保存

## 工作流程

### 典型使用场景：开发者提交代码后立即收到评审

1. **配置实时监控**
   ```bash
   POST /api/v1/code-reviews/realtime-configs/
   {
       "repository": 1,
       "is_active": true,
       "monitored_branches": ["master"],
       "auto_review": true,
       "notify_on_new_commit": true,
       "notify_level": "MEDIUM"
   }
   ```

2. **开发者提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   git push origin master
   ```

3. **系统自动检测新提交**
   - Celery每分钟检查一次启用的仓库
   - 发现新提交后自动触发评审

4. **AI评审代码**
   - 获取diff内容
   - 调用DeepSeek API进行评审
   - 生成评审结果

5. **发送钉钉通知**
   - 评审完成后自动发送到钉钉群
   - 包含风险等级、修改文件、评审要点等信息

6. **开发者查看评审结果**
   - 在钉钉群中查看评审结果
   - 根据评审意见修改代码
   - 提供反馈（准确/误报/漏报）

### 典型使用场景：每天定时批量评审

1. **配置定时任务**
   ```bash
   POST /api/v1/code-reviews/scheduled-configs/
   {
       "name": "中午批量评审",
       "repositories": [1, 2, 3],
       "cron_expression": "0 12 * * *",
       "branches": ["master", "develop"],
       "is_active": true
   }
   ```

2. **Celery Beat自动执行**
   - 每天中午12点自动触发
   - 批量评审所有配置的仓库
   - 发送汇总通知

3. **团队查看评审结果**
   - 在系统中查看所有评审记录
   - 按风险等级筛选
   - 查看个人评审统计

## 数据模型

### CodeReview（代码评审记录）
- repository - 仓库
- branch - 分支
- commit_hash - Commit Hash
- commit_message - 提交信息
- author - 作者
- trigger_mode - 触发模式（MANUAL/SCHEDULED/REALTIME/WEBHOOK）
- risk_score - 风险评分
- risk_level - 风险等级（HIGH/MEDIUM/LOW）
- ai_review_content - AI评审内容
- lines_added - 新增行数
- lines_deleted - 删除行数
- review_points - 评审要点

### ReviewTask（评审任务）
- task_id - 任务ID
- repository - 仓库
- status - 任务状态
- progress - 进度
- trigger_mode - 触发模式
- high_risk_count - 高风险数量
- medium_risk_count - 中风险数量
- low_risk_count - 低风险数量

### ScheduledReviewConfig（定时评审配置）
- name - 配置名称
- repositories - 关联仓库
- cron_expression - Cron表达式
- branches - 评审分支
- is_active - 是否启用

### RealtimeMonitorConfig（实时监控配置）
- repository - 仓库
- is_active - 是否启用
- monitored_branches - 监控分支
- check_interval - 检查间隔
- auto_review - 自动评审
- notify_level - 通知级别

## 钉钉通知格式

### 单条提交评审通知
```
【代码评审通知】
仓库: settle-center
分支: master
作者: 张三
提交: abc1234 - fix bug: 修复登录问题

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

### 定时任务汇总通知
```
【代码评审汇总】
时间: 2026-01-23 12:00
配置: 中午批量评审

📊 评审统计:
- 总提交数: 15
- 高风险: 2
- 中风险: 8
- 低风险: 5

🔴 高风险提交:
1. settle-center - abc1234 - 张三
2. settle-center-pro - def5678 - 李四

✅ 已发送钉钉通知: 15条
```

## 最佳实践

1. **实时监控用于核心分支**
   - 对master、develop等核心分支启用实时监控
   - 确保重要提交及时评审

2. **定时任务用于全量评审**
   - 每天定时评审所有分支
   - 确保不遗漏任何提交

3. **合理设置通知级别**
   - 高风险项目：只通知HIGH和MEDIUM
   - 低风险项目：通知所有级别

4. **定期清理历史数据**
   - 定期归档旧的评审记录
   - 保持数据库性能

5. **提供反馈机制**
   - 鼓励开发者对评审结果提供反馈
   - 持续优化AI评审准确性

## 故障排查

### 任务一直处于PENDING状态
- 检查Celery worker是否正常运行
- 检查Redis连接是否正常
- 查看Celery日志: `tail -f /tmp/celery.log`

### 钉钉通知未发送
- 检查Webhook URL是否正确
- 检查Secret是否配置
- 查看Django日志: `tail -f logs/app.log`

### 实时监控未检测到新提交
- 检查监控是否启用
- 检查监控分支是否正确
- 检查Celery Beat是否正常运行

### 定时任务未执行
- 检查Cron表达式是否正确
- 检查配置是否启用
- 检查Celery Beat是否配置定时任务

## 启动服务

```bash
# 启动Django服务
python3 manage.py runserver

# 启动Celery Worker
celery -A config worker -l info

# 启动Celery Beat（定时任务）
celery -A config beat -l info
```

## 注意事项

1. 确保Redis服务正常运行
2. 确保Celery Worker和Beat都启动
3. 定时任务的Cron表达式需要正确配置
4. Webhook URL需要外网可访问
5. 钉钉Webhook和Secret需要正确配置