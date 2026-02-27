# AI智能评审平台 - 详细设计文档 v1.0

## 文档版本控制

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|---------|
| v1.0 | 2026-01-20 | 架构团队 | 初始版本 |

---

## 一、项目结构设计

### 1.1 目录结构

```
ai_review_platform/
├── manage.py                          # Django管理脚本
├── requirements.txt                   # Python依赖
├── Dockerfile                         # Docker构建文件
├── docker-compose.yml                 # Docker Compose配置
├── README.md                          # 项目说明
│
├── config/                            # 配置文件目录
│   ├── __init__.py
│   ├── settings.py                    # Django配置
│   ├── urls.py                        # URL路由
│   ├── wsgi.py                        # WSGI入口
│   ├── celery.py                      # Celery配置
│   ├── logging.yaml                   # 日志配置
│   └── secret.yaml                    # 密钥配置（不提交git）
│
├── apps/                              # Django应用
│   ├── __init__.py
│   │
│   ├── core/                          # 核心应用（基础功能）
│   │   ├── __init__.py
│   │   ├── models.py                  # 基础模型
│   │   ├── serializers.py             # 基础序列化器
│   │   ├── views.py                   # 基础视图
│   │   ├── permissions.py             # 权限类
│   │   └── mixins.py                  # 基础Mixins
│   │
│   ├── users/                         # 用户管理
│   │   ├── __init__.py
│   │   ├── models.py                  # 用户模型扩展
│   │   ├── serializers.py             # 用户序列化器
│   │   ├── views.py                   # 用户视图
│   │   ├── urls.py                    # 用户URL
│   │   ├── auth.py                    # 认证逻辑
│   │   └── services/                  # 用户相关服务
│   │
│   ├── repository/                    # 仓库管理
│   │   ├── __init__.py
│   │   ├── models.py                  # Repository模型
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py                   # 表单验证
│   │   └── services/                  # 仓库相关服务
│   │       ├── __init__.py
│   │       └── git_service.py         # Git操作服务
│   │
│   ├── code_review/                   # 代码评审
│   │   ├── __init__.py
│   │   ├── models.py                  # CodeReview模型
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py                   # Celery任务
│   │   └── services/                  # 评审服务
│   │       ├── __init__.py
│   │       ├── ai_engine.py           # AI评审引擎
│   │       ├── risk_classifier.py     # 风险分类器
│   │       └── diff_analyzer.py       # Diff分析器
│   │
│   ├── prd_review/                    # PRD评审
│   │   ├── __init__.py
│   │   ├── models.py                  # PRDReview模型
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── services/                  # PRD评审服务
│   │       ├── __init__.py
│   │       ├── document_parser.py     # 文档解析
│   │       └── prd_analyzer.py        # PRD分析引擎
│   │
│   ├── test_case/                     # 测试用例
│   │   ├── __init__.py
│   │   ├── models.py                  # TestCase/TestExecution模型
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── services/                  # 测试服务
│   │       ├── __init__.py
│   │       ├── case_generator.py      # 用例生成器
│   │       └── dubbo_executor.py      # Dubbo执行器
│   │
│   ├── feedback/                      # 反馈优化
│   │   ├── __init__.py
│   │   ├── models.py                  # FeedbackRule模型
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services/                  # 反馈服务
│   │       ├── __init__.py
│   │       └── rule_optimizer.py      # 规则优化器
│   │
│   └── dashboard/                     # 数据看板
│       ├── __init__.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── services/                  # 统计服务
│           ├── __init__.py
│           ├── statistics_service.py
│           └── chart_service.py
│
├── templates/                         # Django模板
│   ├── base.html                     # 基础模板
│   ├── dashboard.html                # Dashboard页面
│   ├── repository/                   # 仓库管理模板
│   ├── code_review/                  # 代码评审模板
│   ├── prd_review/                   # PRD评审模板
│   └── test_case/                    # 测试用例模板
│
├── static/                            # 静态资源
│   ├── css/
│   │   ├── style.css
│   │   └── dashboard.css
│   ├── js/
│   │   ├── chart.min.js
│   │   ├── api.js
│   │   └── dashboard.js
│   └── images/
│
├── media/                             # 上传文件存储
│   ├── prd/
│   ├── reports/
│   └── temp/
│
├── logs/                              # 日志文件
│   └── app.log
│
├── scripts/                           # 脚本工具
│   ├── init_db.sh                    # 初始化数据库
│   ├── start.sh                      # 启动服务
│   └── backup.sh                     # 备份脚本
│
└── tests/                             # 测试用例
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

---

## 二、数据库详细设计

### 2.1 用户与权限模型

#### 2.1.1 用户扩展模型

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class UserRole(models.TextChoices):
    """用户角色"""
    PRODUCT_MANAGER = 'pm', '产品经理'
    DEVELOPER = 'developer', '开发工程师'
    TESTER = 'tester', '测试工程师'
    LEADER = 'leader', '团队负责人'
    ADMIN = 'admin', '管理员'


class User(AbstractUser):
    """
    扩展Django内置User模型
    """
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.DEVELOPER,
        verbose_name='角色'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='部门'
    )
    dingtalk_user_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='钉钉用户ID'
    )
    avatar_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='头像URL'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='手机号'
    )
    
    # 统计字段
    total_reviews = models.IntegerField(
        default=0,
        verbose_name='评审次数'
    )
    feedback_count = models.IntegerField(
        default=0,
        verbose_name='反馈次数'
    )
    last_active_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后活跃时间'
    )
    
    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'
    
    def __str__(self):
        return f"{self.username}({self.get_role_display()})"
```

### 2.2 仓库配置模型

#### 2.2.1 仓库表

```python
# apps/repository/models.py
from django.db import models
from django.conf import settings


class AuthType(models.TextChoices):
    """认证方式"""
    PASSWORD = 'password', '用户名密码'
    SSH = 'ssh', 'SSH Key'


class Repository(models.Model):
    """
    Git仓库配置表
    """
    name = models.CharField(
        max_length=100,
        verbose_name='仓库名称'
    )
    git_url = models.URLField(
        verbose_name='Git仓库地址'
    )
    auth_type = models.CharField(
        max_length=20,
        choices=AuthType.choices,
        default=AuthType.PASSWORD,
        verbose_name='认证方式'
    )
    username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='用户名'
    )
    password_encrypted = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='密码（加密）'
    )
    ssh_key_encrypted = models.TextField(
        blank=True,
        verbose_name='SSH Key（加密）'
    )
    local_path = models.CharField(
        max_length=500,
        verbose_name='本地克隆路径'
    )
    
    # 钉钉配置
    dingtalk_webhook = models.URLField(
        blank=True,
        verbose_name='钉钉Webhook'
    )
    dingtalk_secret = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='钉钉Secret'
    )
    
    # 评审配置
    high_risk_threshold = models.FloatField(
        default=0.70,
        verbose_name='高风险阈值'
    )
    medium_risk_threshold = models.FloatField(
        default=0.40,
        verbose_name='中风险阈值'
    )
    
    # 关键文件规则 (JSON)
    # [{"pattern": "**/Controller.java", "level": "critical"}]
    critical_patterns = models.JSONField(
        default=list,
        verbose_name='关键文件规则'
    )
    # 忽略规则 (JSON)
    # [{"pattern": "**/*.md", "type": "ignore"}]
    ignore_patterns = models.JSONField(
        default=list,
        verbose_name='忽略规则'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        db_table = 'repository'
        verbose_name = 'Git仓库'
        verbose_name_plural = '仓库管理'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def clone_status(self):
        """获取克隆状态"""
        from pathlib import Path
        return Path(self.local_path).exists()
```

### 2.3 代码评审模型

#### 2.3.1 代码评审记录表

```python
# apps/code_review/models.py
from django.db import models
from django.conf import settings


class RiskLevel(models.TextChoices):
    """风险等级"""
    HIGH = 'HIGH', '高风险'
    MEDIUM = 'MEDIUM', '中风险'
    LOW = 'LOW', '低风险'


class FeedbackStatus(models.TextChoices):
    """反馈状态"""
    PENDING = 'PENDING', '待反馈'
    CORRECT = 'CORRECT', '评审准确'
    FALSE_POSITIVE = 'FALSE_POSITIVE', '误报'
    MISSED = 'MISSED', '漏报'


class CodeReview(models.Model):
    """
    代码评审记录表
    """
    repository = models.ForeignKey(
        'repository.Repository',
        on_delete=models.CASCADE,
        verbose_name='仓库'
    )
    branch = models.CharField(
        max_length=100,
        verbose_name='分支'
    )
    commit_hash = models.CharField(
        max_length=40,
        verbose_name='Commit Hash'
    )
    commit_message = models.TextField(
        blank=True,
        verbose_name='提交信息'
    )
    author = models.CharField(
        max_length=100,
        verbose_name='作者'
    )
    author_email = models.EmailField(
        blank=True,
        verbose_name='作者邮箱'
    )
    commit_time = models.DateTimeField(
        verbose_name='提交时间'
    )
    
    # 评审结果
    risk_score = models.FloatField(
        verbose_name='风险评分(0-1)'
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        verbose_name='风险等级'
    )
    ai_review_content = models.TextField(
        verbose_name='AI评审内容'
    )
    ai_model = models.CharField(
        max_length=50,
        default='deepseek-coder',
        verbose_name='使用的AI模型'
    )
    
    # 文件变更 (JSON格式)
    # [
    #   {"status": "A/M/D", "path": "src/main/java/xxx.java", "is_critical": true}
    # ]
    changed_files = models.JSONField(
        verbose_name='变更文件列表'
    )
    diff_content = models.TextField(
        blank=True,
        verbose_name='Diff内容'
    )
    
    # 评审要点 (JSON格式)
    # [{"type": "security", "line": 45, "description": "..."}]
    review_points = models.JSONField(
        default=list,
        verbose_name='评审要点'
    )
    
    # 反馈
    feedback_status = models.CharField(
        max_length=20,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.PENDING,
        verbose_name='反馈状态'
    )
    feedback_comment = models.TextField(
        blank=True,
        verbose_name='反馈评论'
    )
    feedback_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks',
        verbose_name='反馈人'
    )
    feedback_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='反馈时间'
    )
    
    # 推送状态
    dingtalk_sent = models.BooleanField(
        default=False,
        verbose_name='是否已推送钉钉'
    )
    dingtalk_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='钉钉推送时间'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='评审时间'
    )
    
    class Meta:
        db_table = 'code_review'
        verbose_name = '代码评审'
        verbose_name_plural = '代码评审记录'
        unique_together = ['repository', 'commit_hash']
        indexes = [
            models.Index(fields=['repository', 'branch']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['feedback_status']),
        ]
    
    def __str__(self):
        return f"{self.repository.name} - {self.commit_hash[:8]}"
```

### 2.4 PRD评审模型

#### 2.4.1 PRD评审记录表

```python
# apps/prd_review/models.py
from django.db import models
from django.conf import settings


class FileType(models.TextChoices):
    """文件类型"""
    WORD = 'word', 'Word文档'
    MARKDOWN = 'md', 'Markdown'
    PDF = 'pdf', 'PDF'


class ReviewStatus(models.TextChoices):
    """评审状态"""
    PENDING = 'PENDING', '待评审'
    APPROVED = 'APPROVED', '已通过'
    REJECTED = 'REJECTED', '需修改'


class IssueSeverity(models.TextChoices):
    """问题严重性"""
    HIGH = 'high', '高'
    MEDIUM = 'medium', '中'
    LOW = 'low', '低'


class IssueType(models.TextChoices):
    """问题类型"""
    COMPLETENESS = 'completeness', '完整性问题'
    CONSISTENCY = 'consistency', '一致性问题'
    RISK = 'risk', '风险问题'
    CLARITY = 'clarity', '清晰度问题'


class PRDReview(models.Model):
    """
    PRD评审记录表
    """
    title = models.CharField(
        max_length=200,
        verbose_name='PRD标题'
    )
    file = models.FileField(
        upload_to='prd/',
        verbose_name='PRD文件'
    )
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        verbose_name='文件类型'
    )
    file_size = models.IntegerField(
        verbose_name='文件大小(bytes)'
    )
    
    # AI提取的结构化内容
    background = models.TextField(
        blank=True,
        verbose_name='背景描述'
    )
    user_stories = models.JSONField(
        default=list,
        verbose_name='用户故事'
    )
    requirements = models.JSONField(
        default=list,
        verbose_name='需求点'
    )
    # [{"id": "REQ001", "description": "...", "priority": "P0"}]
    
    # 评审维度得分
    completeness_score = models.FloatField(
        verbose_name='完整性得分(0-1)'
    )
    consistency_score = models.FloatField(
        verbose_name='一致性得分(0-1)'
    )
    risk_score = models.FloatField(
        verbose_name='风险得分(0-1)'
    )
    overall_score = models.FloatField(
        verbose_name='综合得分(0-1)'
    )
    
    # AI建议
    ai_suggestions = models.TextField(
        verbose_name='AI改进建议'
    )
    issues_found = models.JSONField(
        default=list,
        verbose_name='发现的问题'
    )
    # [
    #   {"type": "completeness", "severity": "high", "description": "..."}
    # ]
    
    # 人工评审
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        verbose_name='评审状态'
    )
    review_comment = models.TextField(
        blank=True,
        verbose_name='评审意见'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prd_reviews',
        verbose_name='评审人'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='评审时间'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_prds',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    class Meta:
        db_table = 'prd_review'
        verbose_name = 'PRD评审'
        verbose_name_plural = 'PRD评审记录'
        indexes = [
            models.Index(fields=['created_by']),
            models.Index(fields=['review_status']),
            models.Index(fields=['overall_score']),
        ]
    
    def __str__(self):
        return self.title
```

### 2.5 测试用例模型

#### 2.5.1 测试用例表

```python
# apps/test_case/models.py
from django.db import models
from django.conf import settings


class CaseType(models.TextChoices):
    """用例类型"""
    FUNCTION = 'FUNCTION', '功能测试'
    BOUNDARY = 'BOUNDARY', '边界测试'
    EXCEPTION = 'EXCEPTION', '异常测试'
    PERFORMANCE = 'PERFORMANCE', '性能测试'


class CasePriority(models.TextChoices):
    """优先级"""
    P0 = 'P0', 'P0-核心流程'
    P1 = 'P1', 'P1-重要功能'
    P2 = 'P2', 'P2-一般功能'


class ReviewStatus(models.TextChoices):
    """评审状态"""
    PENDING = 'PENDING', '待评审'
    APPROVED = 'APPROVED', '已通过'
    REJECTED = 'REJECTED', '需修改'


class ExecutionStatus(models.TextChoices):
    """执行状态"""
    RUNNING = 'RUNNING', '执行中'
    PASSED = 'PASSED', '通过'
    FAILED = 'FAILED', '失败'
    ERROR = 'ERROR', '错误'


class TestCase(models.Model):
    """
    测试用例表
    """
    prd_review = models.ForeignKey(
        'prd_review.PRDReview',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联PRD评审'
    )
    code_review = models.ForeignKey(
        'code_review.CodeReview',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联代码评审'
    )
    
    case_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='用例编号'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='用例标题'
    )
    type = models.CharField(
        max_length=20,
        choices=CaseType.choices,
        verbose_name='测试类型'
    )
    priority = models.CharField(
        max_length=10,
        choices=CasePriority.choices,
        verbose_name='优先级'
    )
    
    # 用例内容
    precondition = models.TextField(
        blank=True,
        verbose_name='前置条件'
    )
    steps = models.JSONField(
        verbose_name='测试步骤'
    )
    expected_result = models.TextField(
        verbose_name='预期结果'
    )
    
    # Dubbo调用配置
    dubbo_interface = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Dubbo接口'
    )
    dubbo_method = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Dubbo方法'
    )
    dubbo_params = models.JSONField(
        default=dict,
        verbose_name='Dubbo参数'
    )
    dubbo_group = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Dubbo分组'
    )
    dubbo_version = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Dubbo版本'
    )
    
    # 评审
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        verbose_name='评审状态'
    )
    review_comment = models.TextField(
        blank=True,
        verbose_name='评审意见'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_test_cases',
        verbose_name='评审人'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='评审时间'
    )
    
    # 统计
    execution_count = models.IntegerField(
        default=0,
        verbose_name='执行次数'
    )
    last_execution_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='最后执行状态'
    )
    last_executed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后执行时间'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_test_cases',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        db_table = 'test_case'
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例管理'
        indexes = [
            models.Index(fields=['prd_review']),
            models.Index(fields=['type']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.case_id} - {self.title}"


class TestExecution(models.Model):
    """
    测试执行记录表
    """
    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        verbose_name='测试用例'
    )
    execution_batch = models.CharField(
        max_length=100,
        verbose_name='执行批次'
    )
    
    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        verbose_name='执行状态'
    )
    
    # 请求响应
    request_data = models.JSONField(
        null=True,
        verbose_name='请求数据'
    )
    response_data = models.JSONField(
        null=True,
        verbose_name='响应数据'
    )
    execution_time = models.FloatField(
        verbose_name='执行耗时(秒)'
    )
    
    # 错误信息
    error_message = models.TextField(
        blank=True,
        verbose_name='错误信息'
    )
    stack_trace = models.TextField(
        blank=True,
        verbose_name='堆栈信息'
    )
    
    executed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='执行时间'
    )
    
    class Meta:
        db_table = 'test_execution'
        verbose_name = '测试执行'
        verbose_name_plural = '测试执行记录'
        indexes = [
            models.Index(fields=['test_case']),
            models.Index(fields=['execution_batch']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.test_case.case_id} - {self.status}"


class TestReport(models.Model):
    """
    测试报告表
    """
    batch_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='批次ID'
    )
    
    # 统计
    total_cases = models.IntegerField(
        verbose_name='总用例数'
    )
    passed_cases = models.IntegerField(
        verbose_name='通过数'
    )
    failed_cases = models.IntegerField(
        verbose_name='失败数'
    )
    error_cases = models.IntegerField(
        verbose_name='错误数'
    )
    skipped_cases = models.IntegerField(
        default=0,
        verbose_name='跳过数'
    )
    pass_rate = models.FloatField(
        verbose_name='通过率(%)'
    )
    
    # 时间
    start_time = models.DateTimeField(
        verbose_name='开始时间'
    )
    end_time = models.DateTimeField(
        verbose_name='结束时间'
    )
    duration = models.FloatField(
        verbose_name='总耗时(秒)'
    )
    
    # 报告文件
    report_file = models.FileField(
        upload_to='reports/',
        verbose_name='报告文件'
    )
    
    # 环境信息
    environment = models.JSONField(
        default=dict,
        verbose_name='环境信息'
    )
    
    # 失败用例列表
    failed_details = models.JSONField(
        default=list,
        verbose_name='失败详情'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    class Meta:
        db_table = 'test_report'
        verbose_name = '测试报告'
        verbose_name_plural = '测试报告'
        indexes = [
            models.Index(fields=['batch_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"测试报告 - {self.batch_id}"
```

### 2.6 反馈规则模型

```python
# apps/feedback/models.py
from django.db import models
from django.conf import settings


class RuleType(models.TextChoices):
    """规则类型"""
    WHITELIST = 'WHITELIST', '白名单-忽略'
    BLACKLIST = 'BLACKLIST', '黑名单-加强检测'


class FeedbackRule(models.Model):
    """
    反馈优化规则表
    """
    rule_type = models.CharField(
        max_length=20,
        choices=RuleType.choices,
        verbose_name='规则类型'
    )
    pattern = models.TextField(
        verbose_name='规则模式'
    )
    description = models.TextField(
        blank=True,
        verbose_name='规则描述'
    )
    weight = models.FloatField(
        default=1.0,
        verbose_name='权重'
    )
    
    # 统计
    feedback_count = models.IntegerField(
        default=0,
        verbose_name='反馈次数'
    )
    accuracy_rate = models.FloatField(
        default=0.0,
        verbose_name='准确率(%)'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        db_table = 'feedback_rule'
        verbose_name = '反馈规则'
        verbose_name_plural = '反馈规则管理'
        indexes = [
            models.Index(fields=['rule_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_rule_type_display()} - {self.pattern[:50]}"
```

---

## 三、API接口设计

### 3.1 代码评审接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/reviews/ | 评审列表 | ✅ |
| GET | /api/v1/reviews/{id}/ | 评审详情 | ✅ |
| POST | /api/v1/reviews/{id}/feedback/ | 提交反馈 | ✅ |
| GET | /api/v1/reviews/statistics/ | 评审统计 | ✅ |
| POST | /api/v1/reviews/trigger/ | 手动触发评审 | ✅ |

#### 3.1.1 评审列表接口

**请求参数**
```
GET /api/v1/reviews/
{
    "repository_id": 1,        // 可选，仓库ID筛选
    "branch": "master",        // 可选，分支筛选
    "risk_level": "HIGH",      // 可选，风险等级筛选
    "author": "zhangsan",      // 可选，作者筛选
    "feedback_status": "PENDING", // 可选，反馈状态筛选
    "start_date": "2026-01-01",   // 可选，开始日期
    "end_date": "2026-01-20",     // 可选，结束日期
    "page": 1,                 // 页码
    "page_size": 20            // 每页数量
}
```

**响应**
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "total": 150,
        "page": 1,
        "page_size": 20,
        "items": [
            {
                "id": 1,
                "repository": {
                    "id": 1,
                    "name": "settle-center"
                },
                "branch": "master",
                "commit_hash": "a1b2c3d4e5f6",
                "commit_message": "feat: 新增账户充值功能",
                "author": "zhangsan",
                "commit_time": "2026-01-19T10:30:00Z",
                "risk_score": 0.85,
                "risk_level": "HIGH",
                "changed_files_count": 3,
                "feedback_status": "PENDING",
                "created_at": "2026-01-19T10:35:00Z"
            }
        ]
    }
}
```

#### 3.1.2 评审详情接口

**响应**
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "id": 1,
        "repository": {
            "id": 1,
            "name": "settle-center"
        },
        "branch": "master",
        "commit_hash": "a1b2c3d4e5f6",
        "commit_message": "feat: 新增账户充值功能",
        "author": "zhangsan",
        "author_email": "zhangsan@company.com",
        "commit_time": "2026-01-19T10:30:00Z",
        
        "risk_score": 0.85,
        "risk_level": "HIGH",
        "ai_review_content": "### 评审结果\\n\\n**风险评分: 85% (高风险)**\\n\\n### 发现的问题\\n\\n1. **[严重] 金额计算使用double类型**...",
        "ai_model": "deepseek-coder",
        
        "changed_files": [
            {
                "status": "M",
                "path": "src/main/java/com/bestpay/service/AccountService.java",
                "is_critical": true
            },
            {
                "status": "A",
                "path": "src/main/java/com/bestpay/controller/RechargeController.java",
                "is_critical": true
            }
        ],
        "diff_content": "diff --git a/...",
        
        "review_points": [
            {
                "type": "security",
                "line": 45,
                "file": "AccountService.java",
                "severity": "high",
                "description": "金额计算使用double类型，存在精度丢失风险",
                "suggestion": "改用BigDecimal"
            }
        ],
        
        "feedback_status": "PENDING",
        "feedback_comment": "",
        "feedback_by": null,
        "feedback_at": null,
        
        "dingtalk_sent": true,
        "dingtalk_sent_at": "2026-01-19T10:35:05Z",
        
        "created_at": "2026-01-19T10:35:00Z"
    }
}
```

#### 3.1.3 提交反馈接口

**请求**
```
POST /api/v1/reviews/1/feedback/
{
    "feedback_status": "FALSE_POSITIVE",
    "comment": "这是误报，金额场景下使用double是安全的"
}
```

**响应**
```json
{
    "code": 0,
    "message": "反馈提交成功",
    "data": {
        "feedback_status": "FALSE_POSITIVE",
        "feedback_comment": "这是误报...",
        "feedback_by": 1,
        "feedback_at": "2026-01-19T11:00:00Z"
    }
}
```

### 3.2 仓库管理接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/repositories/ | 仓库列表 | ✅ |
| POST | /api/v1/repositories/ | 新增仓库 | ✅ (Leader/Admin) |
| GET | /api/v1/repositories/{id}/ | 仓库详情 | ✅ |
| PUT | /api/v1/repositories/{id}/ | 更新仓库 | ✅ (Owner) |
| DELETE | /api/v1/repositories/{id}/ | 删除仓库 | ✅ (Admin) |
| POST | /api/v1/repositories/{id}/test-connection/ | 测试连接 | ✅ |
| POST | /api/v1/repositories/{id}/sync/ | 同步仓库 | ✅ |

### 3.3 PRD评审接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/prd-reviews/ | PRD评审列表 | ✅ |
| POST | /api/v1/prd-reviews/ | 上传并评审PRD | ✅ |
| GET | /api/v1/prd-reviews/{id}/ | PRD评审详情 | ✅ |
| PUT | /api/v1/prd-reviews/{id}/review/ | 人工评审 | ✅ |

### 3.4 测试用例接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/test-cases/ | 用例列表 | ✅ |
| POST | /api/v1/test-cases/generate/ | 生成用例 | ✅ |
| POST | /api/v1/test-cases/execute/ | 执行测试 | ✅ |
| GET | /api/v1/test-cases/{id}/ | 用例详情 | ✅ |
| PUT | /api/v1/test-cases/{id}/ | 更新用例 | ✅ |
| GET | /api/v1/test-reports/ | 测试报告列表 | ✅ |
| GET | /api/v1/test-reports/{id}/ | 测试报告详情 | ✅ |

### 3.5 数据统计接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/dashboard/stats/ | Dashboard统计 | ✅ |
| GET | /api/v1/dashboard/trend/ | 趋势数据 | ✅ |
| GET | /api/v1/dashboard/ranking/ | 排名数据 | ✅ |
| GET | /api/v1/dashboard/risk-heatmap/ | 风险热力图 | ✅ |

---

## 四、核心服务设计

### 4.1 Git服务

```python
# apps/repository/services/git_service.py
import os
import git
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from django.conf import settings


class GitService:
    """Git仓库操作服务"""
    
    def __init__(self, repository):
        self.repository = repository
        self.local_path = Path(repository.local_path)
    
    def ensure_repo(self) -> bool:
        """
        确保仓库已克隆或更新
        Returns:
            bool: 是否是首次克隆
        """
        if not self.local_path.exists():
            return self._clone()
        else:
            return self._fetch()
    
    def _clone(self) -> bool:
        """克隆仓库"""
        try:
            if self.repository.auth_type == 'password':
                # 使用用户名密码
                repo = git.Repo.clone_from(
                    self.repository.git_url,
                    self.local_path,
                    branch='master',
                    depth=1  # 浅克隆
                )
            else:
                # 使用SSH Key
                with git.remote.Remote.add(repo, 'origin', self.repository.git_url):
                    pass
            return True
        except Exception as e:
            raise GitException(f"克隆仓库失败: {str(e)}")
    
    def _fetch(self) -> bool:
        """更新仓库"""
        try:
            repo = git.Repo(str(self.local_path))
            repo.remotes.origin.fetch()
            return False  # 不是首次克隆
        except Exception as e:
            raise GitException(f"更新仓库失败: {str(e)}")
    
    def get_today_commits(self, branch: str = 'master') -> List[Dict]:
        """获取今日提交"""
        try:
            repo = git.Repo(str(self.local_path))
            today = timezone.now().date()
            
            commits = list(repo.iter_commits(
                f'origin/{branch}',
                since=today.strftime('%Y-%m-%d 00:00:00')
            ))
            
            return [
                {
                    'hash': c.hexsha,
                    'message': c.message.strip(),
                    'author': c.author.name,
                    'author_email': c.author.email,
                    'committed_datetime': c.committed_datetime,
                    'parents': [p.hexsha for p in c.parents]
                }
                for c in commits
            ]
        except Exception as e:
            raise GitException(f"获取提交记录失败: {str(e)}")
    
    def get_diff_and_files(self, commit_hash: str) -> Tuple[str, List[Dict]]:
        """
        获取Diff和文件变更列表
        
        Returns:
            Tuple[diff_content, files_list]
        """
        try:
            repo = git.Repo(str(self.local_path))
            commit = repo.commit(commit_hash)
            
            # 获取Diff
            if commit.parents:
                diffs = commit.parents[0].diff(
                    commit,
                    create_patch=True,
                    unified=5
                )
            else:
                # 首次提交
                diffs = commit.diff(git.NULL_TREE, create_patch=True)
            
            # 解析文件变更
            files = []
            diff_content_parts = []
            
            for d in diffs:
                file_info = {
                    'status': d.change_type,  # A/M/D/R
                    'path': d.b_path or d.a_path,
                    'is_critical': self._is_critical_file(d.b_path or d.a_path),
                    'new_path': d.b_path,
                    'old_path': d.a_path
                }
                files.append(file_info)
                
                # 收集Diff文本
                if d.diff:
                    diff_content_parts.append(
                        d.diff.decode('utf-8', errors='replace')
                    )
            
            diff_content = '\n'.join(diff_content_parts)
            return diff_content, files
            
        except Exception as e:
            raise GitException(f"获取Diff失败: {str(e)}")
    
    def _is_critical_file(self, file_path: str) -> bool:
        """判断是否为关键文件"""
        patterns = self.repository.critical_patterns or []
        for pattern in patterns:
            if self._match_pattern(file_path, pattern.get('pattern', '')):
                return True
        return False
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """简单路径匹配（支持通配符）"""
        from fnmatch import fnmatch
        return fnmatch(path, pattern)
    
    def get_file_content(self, commit_hash: str, file_path: str) -> str:
        """获取文件内容"""
        try:
            repo = git.Repo(str(self.local_path))
            commit = repo.commit(commit_hash)
            blob = commit.tree / file_path
            return blob.data_stream.read().decode('utf-8')
        except Exception as e:
            raise GitException(f"获取文件内容失败: {str(e)}")
    
    def get_all_branches(self) -> List[str]:
        """获取所有远程分支"""
        try:
            repo = git.Repo(str(self.local_path))
            branches = [b.name for b in repo.remotes.origin.fetch()]
            return branches
        except Exception as e:
            raise GitException(f"获取分支列表失败: {str(e)}")


class GitException(Exception):
    """Git操作异常"""
    pass
```

### 4.2 AI评审引擎

```python
# apps/code_review/services/ai_engine.py
import json
import re
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from .risk_classifier import RiskClassifier


class AIReviewEngine:
    """AI评审引擎"""
    
    # 风险关键词映射
    RISK_KEYWORDS = {
        'security': [
            'sql注入', 'xss', 'csrf', '认证绕过', '权限提升',
            '敏感信息泄露', '加密', '解密', '密码', 'token'
        ],
        'performance': [
            '循环', '嵌套查询', '全表扫描', '内存泄漏',
            '大数据量', '分页', '缓存', '索引'
        ],
        'reliability': [
            '空指针', '空指针异常', '除零', '数组越界',
            '异常捕获', '事务', '幂等', '并发'
        ],
        'maintainability': [
            '重复代码', '硬编码', '魔法数字', '过长方法',
            '过深继承', '耦合', '依赖'
        ]
    }
    
    def __init__(self, api_key: str = None, model: str = 'deepseek'):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model
        self.risk_classifier = RiskClassifier()
    
    def review(
        self,
        diff_content: str,
        files: List[Dict],
        commit_message: str,
        commit_hash: str = None
    ) -> Dict:
        """
        执行AI代码评审
        
        Args:
            diff_content: Git Diff内容
            files: 文件变更列表
            commit_message: 提交信息
            commit_hash: 提交Hash
            
        Returns:
            Dict: 评审结果
        """
        # 1. 构建Prompt
        prompt = self._build_prompt(diff_content, files, commit_message)
        
        # 2. 调用AI模型
        response = self._call_ai(prompt)
        
        # 3. 解析结果
        result = self._parse_response(response)
        
        # 4. 风险分类
        result['risk_score'] = self.risk_classifier.classify(
            result['issues'],
            files
        )
        result['risk_level'] = self._get_risk_level(result['risk_score'])
        
        # 5. 提取评审要点
        result['review_points'] = self._extract_review_points(
            result['ai_content'],
            files
        )
        
        return result
    
    def _build_prompt(
        self,
        diff_content: str,
        files: List[Dict],
        commit_message: str
    ) -> str:
        """构建评审Prompt"""
        prompt = f"""
你是一位资深代码评审专家，请对以下代码变更进行评审。

## 提交信息
**Message**: {commit_message}

## 变更文件 ({len(files)}个)
"""
        for f in files:
            prompt += f"- [{f['status']}] {f['path']}"
            if f.get('is_critical'):
                prompt += " [关键文件]"
            prompt += "\n"

        prompt += f"""
## 代码变更 (Diff)
```
{diff_content[:15000]}  # 限制长度
```

## 评审要求

请从以下几个维度进行分析：

### 1. 安全风险 (Security)
- SQL注入、XSS、CSRF
- 认证授权问题
- 敏感信息处理
- 加密解密逻辑

### 2. 性能问题 (Performance)
- 循环效率
- 数据库查询优化
- 内存使用
- 缓存策略

### 3. 可靠性 (Reliability)
- 空指针处理
- 异常处理完整性
- 事务一致性
- 幂等性保证

### 4. 可维护性 (Maintainability)
- 代码重复
- 硬编码
- 代码复杂度
- 命名规范

## 输出格式

请用JSON格式输出评审结果：

```json
{{
    "summary": "一句话总结评审结果",
    "issues": [
        {{
            "type": "security|performance|reliability|maintainability",
            "severity": "high|medium|low",
            "file": "文件路径",
            "line": 行号,
            "description": "问题描述",
            "suggestion": "修复建议",
            "code_snippet": "问题代码片段"
        }}
    ],
    "praise": [
        "做得好的地方1",
        "做得好的地方2"
    ]
}}
```
"""
        return prompt
    
    def _call_ai(self, prompt: str) -> str:
        """调用AI模型"""
        # TODO: 实现具体的API调用
        # 这里使用DeepSeek API示例
        import requests
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-coder",
                "messages": [
                    {"role": "system", "content": "你是一位专业的代码评审专家。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            },
            timeout=60
        )
        
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    
    def _parse_response(self, response: str) -> Dict:
        """解析AI响应"""
        # 提取JSON内容
        json_match = re.search(r'```json\n(.+?)\n```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            result = json.loads(json_str)
        else:
            # 尝试直接解析
            result = json.loads(response)
        
        # 确保字段完整
        result.setdefault('summary', '')
        result.setdefault('issues', [])
        result.setdefault('praise', [])
        result.setdefault('ai_content', response)
        
        return result
    
    def _extract_review_points(
        self,
        ai_content: str,
        files: List[Dict]
    ) -> List[Dict]:
        """提取评审要点"""
        points = []
        
        # 从AI内容中提取关键问题
        lines = ai_content.split('\n')
        for i, line in enumerate(lines):
            # 识别问题行
            if '**' in line and ('问题' in line or '建议' in line):
                # 简化提取逻辑
                pass
        
        return points
    
    def _get_risk_level(self, score: float) -> str:
        """根据风险评分获取风险等级"""
        if score >= 0.7:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
```

### 4.3 风险分类器

```python
# apps/code_review/services/risk_classifier.py
from typing import List, Dict, Optional


class RiskClassifier:
    """风险分类器"""
    
    # 高风险模式
    HIGH_RISK_PATTERNS = [
        # 安全相关
        (r'sql.*format|%\s*.*s.*%', 'potential_sql_injection', 0.9),
        (r'exec\(|eval\(', 'code_execution_risk', 0.95),
        (r'password|secret|token|key', 'sensitive_data_handling', 0.7),
        (r' decrypt| encrypt', 'encryption_logic', 0.6),
        
        # 可靠性相关
        (r'null', 'null_handling', 0.6),
        (r'double\s+[\w]+', 'floating_point_precision', 0.8),
        (r'@Transactional', 'transaction_missing', 0.7),
        (r'synchronized', 'concurrency_risk', 0.6),
        
        # 性能相关
        (r'for.*for', 'nested_loop', 0.7),
        (r'select\s*\*.+from', 'full_table_scan', 0.7),
    ]
    
    # 中风险模式
    MEDIUM_RISK_PATTERNS = [
        (r'System\.out\.print', 'debug_code', 0.4),
        (r'TODO|FIXME', 'incomplete_code', 0.4),
        (r'\bnew\s+\w+Service\(\)', 'service_coupling', 0.4),
        (r'\bhardcode|\bhard_code', 'hardcoding_risk', 0.4),
    ]
    
    def classify(
        self,
        issues: List[Dict],
        files: List[Dict]
    ) -> float:
        """
        综合评估风险评分
        
        Args:
            issues: AI识别的问题列表
            files: 变更文件列表
            
        Returns:
            float: 风险评分 (0-1)
        """
        score = 0.0
        
        # 1. 基于AI识别的问题计算分数
        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity == 'high':
                score += 0.15
            elif severity == 'medium':
                score += 0.08
            else:
                score += 0.03
        
        # 2. 基于文件重要性调整
        critical_files = [f for f in files if f.get('is_critical')]
        if critical_files:
            score *= 1.2  # 关键文件风险权重增加20%
        
        # 3. 模式匹配调整
        for pattern, name, weight in self.HIGH_RISK_PATTERNS:
            # 检查是否匹配（简化实现）
            pass
        
        # 限制在0-1范围内
        return min(1.0, max(0.0, score))
```

### 4.4 钉钉推送服务

```python
# apps/core/services/dingtalk_service.py
import time
import hmac
import hashlib
import base64
import requests
from typing import Dict, List, Optional
from urllib.parse import quote_plus


class DingTalkService:
    """钉钉消息推送服务"""
    
    def __init__(self, webhook: str, secret: str = None):
        self.webhook = webhook
        self.secret = secret
    
    def send_review_notification(
        self,
        review_data: Dict,
        at_users: List[str] = None
    ) -> bool:
        """
        发送代码评审通知
        
        Args:
            review_data: 评审数据
            at_users: @用户列表
            
        Returns:
            bool: 是否发送成功
        """
        # 构建消息内容
        content = self._build_review_content(review_data)
        
        # 构建at用户
        at_mobiles = at_users or []
        
        # 发送消息
        return self._send_message(content, at_mobiles)
    
    def _build_review_content(self, review_data: Dict) -> str:
        """构建评审消息内容"""
        risk_emoji = {
            'HIGH': '🔴',
            'MEDIUM': '🟠',
            'LOW': '🟢'
        }
        
        emoji = risk_emoji.get(review_data.get('risk_level'), '🟢')
        
        content = f"""## AI代码评审报告 {emoji}

**仓库**: {review_data.get('repository_name', '')}
**分支**: {review_data.get('branch', '')}
**提交**: `{review_data.get('commit_hash', '')[:8]}`
**作者**: {review_data.get('author', '')}
**风险等级**: {review_data.get('risk_level', '')} ({review_data.get('risk_score', 0) * 100:.0f}%)

---

### 📝 提交信息
```
{review_data.get('commit_message', '')}
```

### 📁 变更文件
"""
        
        for f in review_data.get('changed_files', []):
            emoji_map = {'A': '➕', 'M': '📝', 'D': '❌', 'R': '🔄'}
            file_emoji = emoji_map.get(f.get('status', ''), '📄')
            critical = ' ⚠️' if f.get('is_critical') else ''
            content += f"{file_emoji} {f['path']}{critical}\n"
        
        content += "\n### 🔍 AI评审结果\n\n"
        content += review_data.get('ai_summary', '暂无详细评审内容')
        
        content += "\n\n---\n*来自AI智能评审平台*"
        
        return content
    
    def _send_message(
        self,
        content: str,
        at_mobiles: List[str] = None
    ) -> bool:
        """
        发送消息
        
        Args:
            content: 消息内容（Markdown格式）
            at_mobiles: @用户手机号列表
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 如果配置了加签密钥，需要签名
            if self.secret:
                timestamp, sign = self._sign()
                url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.webhook
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "AI代码评审报告",
                    "text": content
                },
                "at": {
                    "atMobiles": at_mobiles or [],
                    "isAtAll": False
                }
            }
            
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            return response.json().get('errcode', -1) == 0
            
        except Exception as e:
            # 记录错误日志
            return False
    
    def _sign(self) -> Tuple[str, str]:
        """生成签名"""
        timestamp = str(int(time.time() * 1000))
        
        string_to_sign = f"{timestamp}\n{self.secret}"
        
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        sign = quote_plus(base64.b64encode(hmac_code))
        
        return timestamp, sign
```

### 4.5 Celery任务

```python
# apps/code_review/tasks.py
from celery import shared_task
from django.utils import timezone
from .services.ai_engine import AIReviewEngine
from .services.dingtalk_service import DingTalkService
from repository.services.git_service import GitService
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def code_review_task(self, repository_id: int, branch: str = 'master'):
    """
    代码评审任务
    
    Args:
        repository_id: 仓库ID
        branch: 分支名
    """
    from apps.repository.models import Repository
    from apps.code_review.models import CodeReview
    
    try:
        # 1. 获取仓库配置
        repository = Repository.objects.get(id=repository_id)
        
        # 2. Git操作
        git_service = GitService(repository)
        git_service.ensure_repo()
        
        # 3. 获取今日提交
        commits = git_service.get_today_commits(branch)
        
        for commit in commits:
            # 检查是否已评审
            if CodeReview.objects.filter(
                repository=repository,
                commit_hash=commit['hash']
            ).exists():
                continue
            
            # 4. 获取Diff
            diff_content, files = git_service.get_diff_and_files(commit['hash'])
            
            # 5. AI评审
            ai_engine = AIReviewEngine()
            result = ai_engine.review(
                diff_content=diff_content,
                files=files,
                commit_message=commit['message'],
                commit_hash=commit['hash']
            )
            
            # 6. 保存评审记录
            review = CodeReview.objects.create(
                repository=repository,
                branch=branch,
                commit_hash=commit['hash'],
                commit_message=commit['message'],
                author=commit['author'],
                author_email=commit['author_email'],
                commit_time=commit['committed_datetime'],
                risk_score=result['risk_score'],
                risk_level=result['risk_level'],
                ai_review_content=result.get('ai_content', ''),
                changed_files=files,
                diff_content=diff_content,
                review_points=result.get('review_points', [])
            )
            
            # 7. 钉钉推送
            if review.risk_level in ['HIGH', 'MEDIUM']:
                if repository.dingtalk_webhook:
                    dingtalk = DingTalkService(
                        webhook=repository.dingtalk_webhook,
                        secret=repository.dingtalk_secret
                    )
                    
                    dingtalk.send_review_notification({
                        'repository_name': repository.name,
                        'branch': branch,
                        'commit_hash': commit['hash'],
                        'author': commit['author'],
                        'commit_message': commit['message'],
                        'risk_level': result['risk_level'],
                        'risk_score': result['risk_score'],
                        'changed_files': files,
                        'ai_summary': result.get('summary', '')
                    })
                    
                    review.dingtalk_sent = True
                    review.dingtalk_sent_at = timezone.now()
                    review.save()
            
            logger.info(f"评审完成: {repository.name} - {commit['hash'][:8]}")
    
    except Exception as e:
        logger.error(f"代码评审任务失败: {str(e)}")
        raise self.retry(exc=e)


@shared_task
def scan_all_repositories():
    """扫描所有仓库的任务（由Celery Beat调度）"""
    from apps.repository.models import Repository
    
    repositories = Repository.objects.filter(is_active=True)
    
    for repo in repositories:
        # 为每个仓库启动评审任务
        code_review_task.delay(repo.id, 'master')
        # 也可以扫描其他分支
        for branch in ['develop', 'release']:
            code_review_task.delay(repo.id, branch)
```

---

## 五、前端页面设计

### 5.1 页面路由

```python
# config/urls.py
from django.urls import path, include

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # 仓库管理
    path('repositories/', include('apps.repository.urls')),
    
    # 代码评审
    path('reviews/', include('apps.code_review.urls')),
    
    # PRD评审
    path('prd-reviews/', include('apps.prd_review.urls')),
    
    # 测试用例
    path('test-cases/', include('apps.test_case.urls')),
    
    # 统计分析
    path('statistics/', include('apps.dashboard.urls')),
]
```

### 5.2 Dashboard页面

```html
<!-- templates/dashboard.html -->
{% extends "base.html" %}

{% block title %}AI智能评审平台 - Dashboard{% endblock %}

{% block content %}
<div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-cards">
        <div class="stat-card">
            <h3>今日评审</h3>
            <div class="value">{{ today_review_count }}</div>
            <div class="trend {{ trend_class }}">
                {{ trend_text }}
            </div>
        </div>
        <div class="stat-card">
            <h3>高风险提交</h3>
            <div class="value">{{ high_risk_count }}</div>
            <div class="sub-text">占比 {{ high_risk_rate }}%</div>
        </div>
        <div class="stat-card">
            <h3>待反馈</h3>
            <div class="value">{{ pending_feedback_count }}</div>
        </div>
        <div class="stat-card">
            <h3>AI准确率</h3>
            <div class="value">{{ accuracy_rate }}%</div>
        </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-row">
        <!-- 风险趋势图 -->
        <div class="chart-container">
            <h3>风险趋势（近30天）</h3>
            <canvas id="riskTrendChart"></canvas>
        </div>
        
        <!-- 仓库风险分布 -->
        <div class="chart-container">
            <h3>仓库风险分布</h3>
            <canvas id="repoRiskChart"></canvas>
        </div>
    </div>
    
    <!-- 待处理事项 -->
    <div class="pending-section">
        <h3>待处理事项</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>仓库</th>
                    <th>风险等级</th>
                    <th>提交信息</th>
                    <th>作者</th>
                    <th>时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                {% for review in pending_reviews %}
                <tr>
                    <td>{{ review.repository.name }}</td>
                    <td>
                        <span class="risk-badge {{ review.risk_level|lower }}">
                            {{ review.get_risk_level_display }}
                        </span>
                    </td>
                    <td>{{ review.commit_message|truncatechars:30 }}</td>
                    <td>{{ review.author }}</td>
                    <td>{{ review.created_at|timesince }}前</td>
                    <td>
                        <a href="{% url 'code_review:detail' review.id %}" 
                           class="btn btn-sm">查看详情</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/chart.min.js' %}"></script>
<script>
    // 初始化图表
    document.addEventListener('DOMContentLoaded', function() {
        initRiskTrendChart();
        initRepoRiskChart();
    });
</script>
{% endblock %}
```

---

## 六、部署配置

### 6.1 Docker配置

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
```

### 6.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    container_name: ai-review-platform
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings
      - DEBUG=0
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=ai_review
      - DB_USER=postgres
      - DB_PASSWORD=your_password
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    container_name: ai-review-db
    environment:
      - POSTGRES_DB=ai_review
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: ai-review-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  celery-worker:
    build: .
    container_name: ai-review-worker
    command: celery -A config worker -l info
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings
      - DB_HOST=db
      - REDIS_HOST=redis
    volumes:
      - ./media:/app/media
    depends_on:
      - db
      - redis
    restart: unless-stopped

  celery-beat:
    build: .
    container_name: ai-review-beat
    command: celery -A config beat -l info
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings
      - DB_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 6.3 环境配置

```yaml
# config/settings.py (关键配置)
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'your-secret-key')

# 调试模式
DEBUG = os.environ.get('DEBUG', '0')

# 允许的域名
ALLOWED_HOSTS = ['*']

# 应用定义
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 第三方应用
    'rest_framework',
    'corsheaders',
    
    # 自定义应用
    'apps.core',
    'apps.users',
    'apps.repository',
    'apps.code_review',
    'apps.prd_review',
    'apps.test_case',
    'apps.feedback',
    'apps.dashboard',
]

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'NAME': os.environ.get('DB_NAME', 'ai_review'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
    }
}

# Redis配置
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery配置
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# AI模型配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-coder')

# 文件存储
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

---

## 七、总结

本文档详细描述了AI智能评审平台的详细设计方案，包括：

1. **项目结构设计**：清晰的目录结构和模块划分
2. **数据库设计**：完整的ER图和表结构定义
3. **API接口设计**：RESTful API规范
4. **核心服务设计**：
   - Git集成服务
   - AI评审引擎
   - 风险分类器
   - 钉钉推送服务
   - Celery异步任务
5. **前端页面设计**：Dashboard页面模板
6. **部署配置**：Docker容器化方案

---

**文档状态**: 已完成  
**最后更新**: 2026-01-20  
**联系人**: 架构团队
