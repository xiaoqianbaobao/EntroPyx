# 🎯 代码评审触发模式 - 快速参考

## 📋 修复的问题

### 1. 404错误
- **URL**: `/api/v1/code-review/reviews/tasks/{task_id}/`
- **修复**: 改为 `/api/v1/code-review/reviews/task_status/?task_id={task_id}`
- **文件**: `templates/repository_list.html:285`

### 2. 响应格式不一致
- **修复**: 统一返回格式为 `{"code": 0, "message": "...", "data": {...}}`
- **文件**: `apps/code_review/views.py`

## 🚀 新增功能

### Repository配置字段
```python
# 触发模式配置
enable_manual_review          # 启用手动触发
enable_scheduled_review       # 启用定时评审
scheduled_review_cron         # Cron表达式
enable_realtime_monitor       # 启用实时监控
realtime_monitor_interval     # 监控间隔（秒）
realtime_monitor_branches     # 监控分支列表
auto_review_on_new_commit     # 新提交自动评审
notify_on_review_complete     # 评审完成通知
notify_risk_threshold         # 通知阈值
```

### 新增Celery任务
- `check_all_realtime_monitors()` - 检查所有实时监控仓库
- `run_scheduled_review_for_repository()` - 执行定时评审
- `sync_scheduled_reviews()` - 同步定时配置

## 📝 配置示例

### 场景1: 每天中午12点定时评审
```python
repo.enable_scheduled_review = True
repo.scheduled_review_cron = "0 12 * * *"
repo.save()
```

### 场景2: 实时监控（每60秒检查）
```python
repo.enable_realtime_monitor = True
repo.realtime_monitor_interval = 60
repo.realtime_monitor_branches = ['master', 'develop']
repo.auto_review_on_new_commit = True
repo.save()
```

### 场景3: 只通知中高风险
```python
repo.notify_on_review_complete = True
repo.notify_risk_threshold = 'MEDIUM'
repo.save()
```

## 🔄 工作流程

### 手动触发
1. 用户点击"立即评审"按钮
2. 调用 `POST /api/v1/code-review/reviews/manual_trigger/`
3. 返回 `{"code": 0, "data": {"task_id": "xxx"}}`
4. 前端轮询任务状态
5. 评审完成发送钉钉通知

### 定时触发
1. Celery Beat每天12点触发
2. 调用 `run_scheduled_review_for_repository()`
3. 执行代码评审任务
4. 发送评审结果汇总

### 实时监控
1. Celery Beat每分钟触发
2. 调用 `check_all_realtime_monitors()`
3. 检查所有启用了实时监控的仓库
4. 发现新提交后立即触发评审
5. 评审完成立即发送通知

## 📊 测试命令

```bash
# 测试Repository配置
python3 test_repository_config.py

# 测试所有触发模式
python3 test_code_review_triggers.py

# 检查服务状态
./check_code_review_services.sh
```

## 🚀 启动服务

```bash
# 启动所有服务
./start_code_review_services.sh

# 停止所有服务
./stop_code_review_services.sh
```

## 📚 相关文档

- `CODE_REVIEW_GUIDE.md` - 详细使用指南
- `CODE_REVIEW_FEATURES.md` - 功能说明
- `CODE_REVIEW_README.md` - 快速开始
- `CODE_REVIEW_REFACTOR.md` - 重构总结

## ✅ 验证清单

- [x] 404错误已修复
- [x] 响应格式已统一
- [x] Repository配置已添加
- [x] Celery任务已创建
- [x] 测试脚本已创建
- [x] 功能已验证

## 🎯 核心优势

1. **配置集中**: 所有触发模式在Repository中统一管理
2. **灵活独立**: 每个仓库可独立配置
3. **实时响应**: 提交后立即收到评审结果
4. **定时批量**: 支持定时批量评审
5. **易于扩展**: 可轻松添加新触发模式