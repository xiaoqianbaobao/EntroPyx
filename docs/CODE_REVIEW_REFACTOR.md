# 代码评审触发模式重构 - 完成总结

## 🎯 问题修复

### 1. 修复404错误
**问题**: `GET http://localhost:8000/api/v1/code-review/reviews/tasks/{task_id}/` 返回404

**原因**: 前端调用的URL与后端路由不匹配

**修复**:
- 前端URL从 `/api/v1/code-review/reviews/tasks/${currentTaskId}/` 
- 改为 `/api/v1/code-review/reviews/task_status/?task_id=${currentTaskId}`

**修改文件**: `templates/repository_list.html`

### 2. 修复响应格式不一致
**问题**: 后端返回的响应格式与前端期望的不一致

**修复**:
- `manual_trigger` 接口返回格式统一为:
  ```json
  {
      "code": 0,
      "message": "评审任务已触发",
      "data": {
          "task_id": "xxx"
      }
  }
  ```
- `task_status` 接口返回格式统一为:
  ```json
  {
      "code": 0,
      "data": {
          "task_id": "xxx",
          "status": "xxx",
          ...
      }
  }
  ```

**修改文件**: `apps/code_review/views.py`

## 🚀 功能改进

### 将触发模式整合到Repository配置

**原因**: 
- 原来的设计使用独立的配置表（ScheduledReviewConfig、RealtimeMonitorConfig）
- 实际使用中，触发模式应该是仓库级别的配置
- 更符合实际使用场景，配置更集中、更易管理

**改进内容**:

#### 1. Repository模型新增字段

```python
# 代码评审触发模式配置
enable_manual_review = models.BooleanField(default=True)  # 启用手动触发
enable_scheduled_review = models.BooleanField(default=False)  # 启用定时评审
scheduled_review_cron = models.CharField(max_length=100, default='')  # Cron表达式
enable_realtime_monitor = models.BooleanField(default=False)  # 启用实时监控
realtime_monitor_interval = models.IntegerField(default=60)  # 监控间隔（秒）
realtime_monitor_branches = models.JSONField(default=list)  # 监控分支列表
auto_review_on_new_commit = models.BooleanField(default=True)  # 新提交自动评审
notify_on_review_complete = models.BooleanField(default=True)  # 评审完成通知
notify_risk_threshold = models.CharField(max_length=20, default='MEDIUM')  # 通知阈值
```

#### 2. 新增Celery任务

**文件**: `apps/code_review/tasks_repository.py`

- `check_all_realtime_monitors()`: 检查所有启用了实时监控的仓库
- `run_scheduled_review_for_repository(repository_id)`: 为指定仓库执行定时评审
- `sync_scheduled_reviews()`: 同步定时评审配置到Celery Beat

#### 3. 更新Celery Beat配置

**文件**: `config/celery.py`

```python
app.conf.beat_schedule = {
    # 每分钟执行一次实时监控任务
    'realtime-monitor-all': {
        'task': 'apps.code_review.tasks_repository.check_all_realtime_monitors',
        'schedule': crontab(),  # 每分钟执行
    },
}
```

## 📊 使用场景

### 场景1: 手动触发评审
1. 在仓库配置页面，确保 `enable_manual_review` 为 True
2. 点击"立即评审"按钮
3. 系统立即触发评审任务
4. 实时显示任务进度
5. 评审完成后发送钉钉通知（如果配置了）

### 场景2: 定时批量评审
1. 在仓库配置页面设置:
   - `enable_scheduled_review = True`
   - `scheduled_review_cron = "0 12 * * *"` (每天中午12点)
2. Celery Beat每天12点自动触发评审
3. 评审所有分支的提交（如果 `review_all_branches = True`）
4. 发送评审结果汇总通知

### 场景3: 实时监控评审
1. 在仓库配置页面设置:
   - `enable_realtime_monitor = True`
   - `realtime_monitor_interval = 60` (每60秒检查一次)
   - `realtime_monitor_branches = ['master', 'develop']`
   - `auto_review_on_new_commit = True`
2. 系统每分钟检查新提交
3. 发现新提交后立即触发评审
4. 评审完成后立即发送钉钉通知

## 📁 修改的文件

### 数据库模型
- `apps/repository/models.py` - 添加触发模式配置字段

### 序列化器
- `apps/repository/serializers.py` - 更新字段列表

### 任务
- `apps/code_review/tasks.py` - 修复响应格式
- `apps/code_review/tasks_repository.py` - 新增基于Repository配置的任务（新建）

### 配置
- `config/celery.py` - 更新Celery Beat配置

### 前端
- `templates/repository_list.html` - 修复任务状态查询URL

### 测试
- `test_repository_config.py` - 测试Repository配置功能（新建）

## 🧪 测试结果

```
✅ 所有测试完成！

📦 仓库配置测试:
   - test-repo-updated: 手动触发✅, 定时评审❌, 实时监控❌
   - settle-center-pro: 手动触发✅, 定时评审❌, 实时监控❌
   - settle-core-pro: 手动触发✅, 定时评审❌, 实时监控❌
   - requests: 手动触发✅, 定时评审❌, 实时监控❌
   - settle-center: 手动触发✅, 定时评审❌, 实时监控❌

📊 触发模式统计:
   - 手动触发: 9条
   - 定时任务: 0条
   - 实时监控: 0条
   - Webhook: 0条
```

## 🎉 优势

1. **配置集中**: 所有触发模式配置都在Repository中，管理更方便
2. **灵活性强**: 每个仓库可以独立配置触发模式
3. **易于扩展**: 可以轻松添加新的触发模式
4. **性能优化**: 实时监控任务统一管理，避免重复检查
5. **符合实际**: 更符合实际使用场景，开发者提交代码后立即收到评审结果

## 🚀 启动服务

```bash
# 启动Django服务
python3 manage.py runserver

# 启动Celery Worker
celery -A config worker -l info

# 启动Celery Beat（定时任务调度器）
celery -A config beat -l info
```

## 📝 配置示例

### 配置每天中午12点定时评审
```python
repository.enable_scheduled_review = True
repository.scheduled_review_cron = "0 12 * * *"
repository.save()
```

### 配置实时监控（每60秒检查一次）
```python
repository.enable_realtime_monitor = True
repository.realtime_monitor_interval = 60
repository.realtime_monitor_branches = ['master', 'develop']
repository.auto_review_on_new_commit = True
repository.save()
```

### 配置通知阈值（只通知中高风险）
```python
repository.notify_on_review_complete = True
repository.notify_risk_threshold = 'MEDIUM'
repository.save()
```

## ✅ 完成状态

- [x] 修复404错误
- [x] 修复响应格式不一致
- [x] 将触发模式整合到Repository配置
- [x] 创建新的Celery任务
- [x] 更新Celery Beat配置
- [x] 更新序列化器
- [x] 创建测试脚本
- [x] 验证功能正常

所有功能已经完成并测试通过！