# 代码评审模块 - 多触发模式

## 📋 功能概述

代码评审模块现已支持**四种触发模式**，满足不同场景下的代码评审需求：

1. **手动触发** - 用户主动触发评审
2. **定时任务** - 按照预设时间自动批量评审（每天中午12点、傍晚18点）
3. **实时监控** - 监控代码提交，实时触发评审
4. **Webhook触发** - GitLab/GitHub推送时自动触发

## 🚀 快速开始

### 1. 启动服务
```bash
./start_code_review_services.sh
```

### 2. 测试功能
```bash
python3 test_code_review_triggers.py
```

### 3. 检查状态
```bash
./check_code_review_services.sh
```

## 📖 使用场景

### 场景1：开发者提交代码后立即收到评审

**配置实时监控：**
```bash
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
```

**工作流程：**
1. 开发者提交代码：`git push origin master`
2. 系统自动检测新提交（每分钟检查一次）
3. 自动触发AI评审
4. 钉钉群收到评审通知
5. 开发者根据评审结果修改代码

### 场景2：每天定时批量评审

**配置定时任务：**
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

**工作流程：**
1. 每天中午12点自动触发
2. 批量评审所有配置的仓库
3. 发送汇总通知到钉钉

### 场景3：手动触发评审

```bash
POST /api/v1/code-reviews/manual-trigger/
{
    "repository_id": 1,
    "branch": "master",
    "all_branches": false
}
```

### 场景4：Webhook触发

**GitLab/GitHub配置：**
- Webhook URL: `https://your-domain.com/api/v1/code-reviews/webhook-trigger/`
- 触发事件: Push events

## 📊 数据模型

### CodeReview（代码评审记录）
- repository - 仓库
- branch - 分支
- commit_hash - Commit Hash
- trigger_mode - 触发模式（MANUAL/SCHEDULED/REALTIME/WEBHOOK）
- risk_score - 风险评分
- risk_level - 风险等级（HIGH/MEDIUM/LOW）
- lines_added - 新增行数
- lines_deleted - 删除行数

### ReviewTask（评审任务）
- task_id - 任务ID
- status - 任务状态
- progress - 进度
- trigger_mode - 触发模式
- high_risk_count - 高风险数量

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

## 📡 API接口

### 手动触发评审
```bash
POST /api/v1/code-reviews/manual-trigger/
```

### 查询任务状态
```bash
GET /api/v1/code-reviews/task-status/?task_id=xxx
```

### Webhook触发
```bash
POST /api/v1/code-reviews/webhook-trigger/
```

### 定时评审配置管理
```bash
POST /api/v1/code-reviews/scheduled-configs/
GET /api/v1/code-reviews/scheduled-configs/
POST /api/v1/code-reviews/scheduled-configs/{id}/run_now/
POST /api/v1/code-reviews/scheduled-configs/{id}/toggle_active/
```

### 实时监控配置管理
```bash
POST /api/v1/code-reviews/realtime-configs/
GET /api/v1/code-reviews/realtime-configs/
POST /api/v1/code-reviews/realtime-configs/{id}/toggle_active/
POST /api/v1/code-reviews/realtime-configs/{id}/check_now/
```

## 📝 钉钉通知格式

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
```

## 🔧 服务管理

### 启动服务
```bash
./start_code_review_services.sh
```

### 停止服务
```bash
./stop_code_review_services.sh
```

### 检查状态
```bash
./check_code_review_services.sh
```

### 查看日志
```bash
# Celery Worker日志
tail -f /tmp/celery.log

# Celery Beat日志
tail -f /tmp/celery-beat.log

# Django应用日志
tail -f logs/app.log
```

## 📚 文档

- [详细使用指南](CODE_REVIEW_GUIDE.md)
- [功能说明文档](CODE_REVIEW_FEATURES.md)

## ✅ 测试

运行测试脚本验证所有功能：
```bash
python3 test_code_review_triggers.py
```

测试结果：
```
✅ 创建定时评审配置成功: 中午批量评审
✅ 创建定时评审配置成功: 傍晚批量评审
✅ 创建实时监控配置成功
✅ 手动评审任务已触发
✅ Webhook评审任务已触发

📅 定时评审配置: 2个
👁️  实时监控配置: 1个
📊 代码评审记录: 9条
```

## 🎯 最佳实践

1. **实时监控用于核心分支**
   - 对master、develop等核心分支启用实时监控
   - 确保重要提交及时评审

2. **定时任务用于全量评审**
   - 每天定时评审所有分支
   - 确保不遗漏任何提交

3. **合理设置通知级别**
   - 高风险项目：只通知HIGH和MEDIUM
   - 低风险项目：通知所有级别

4. **提供反馈机制**
   - 鼓励开发者对评审结果提供反馈
   - 持续优化AI评审准确性

## 🔍 故障排查

### 任务一直处于PENDING状态
- 检查Celery Worker是否正常运行
- 检查Redis连接是否正常
- 查看Celery日志: `tail -f /tmp/celery.log`

### 定时任务未执行
- 检查Cron表达式是否正确
- 检查配置是否启用
- 检查Celery Beat是否正常运行

### 实时监控未检测到新提交
- 检查监控是否启用
- 检查监控分支是否正确
- 检查Celery Beat是否正常运行

### 钉钉通知未发送
- 检查Webhook URL是否正确
- 检查Secret是否配置
- 查看Django日志: `tail -f logs/app.log`

## 📊 当前配置状态

```
📅 定时评审配置: 2个
   - 中午批量评审 (0 12 * * *) ✅ 启用
   - 傍晚批量评审 (0 18 * * *) ✅ 启用

👁️  实时监控配置: 1个
   - test-repo-updated ✅ 启用

📊 代码评审记录: 9条
   - 手动触发: 9条
   - 定时任务: 0条
   - 实时监控: 0条
   - Webhook: 0条

🎯 风险统计:
   - 高风险: 1条
   - 中风险: 1条
   - 低风险: 7条
```

## 🎉 总结

代码评审模块现已支持完整的多种触发模式：

✅ **手动触发** - 用户主动触发评审
✅ **定时任务** - 每天中午12点和傍晚18点自动批量评审
✅ **实时监控** - 监控代码提交，实时触发评审
✅ **Webhook触发** - GitLab/GitHub推送时自动触发

开发者提交代码后，可以立即在钉钉群收到评审结果，根据评审内容修改代码，提高代码质量和开发效率。