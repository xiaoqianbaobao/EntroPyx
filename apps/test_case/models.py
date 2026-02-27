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
    """测试用例表"""
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
    
    case_id = models.CharField(max_length=50, unique=True, verbose_name='用例编号')
    title = models.CharField(max_length=200, verbose_name='用例标题')
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
    precondition = models.TextField(blank=True, verbose_name='前置条件')
    steps = models.JSONField(verbose_name='测试步骤')
    expected_result = models.TextField(verbose_name='预期结果')
    
    # Dubbo调用配置
    dubbo_interface = models.CharField(max_length=200, blank=True, verbose_name='Dubbo接口')
    dubbo_method = models.CharField(max_length=100, blank=True, verbose_name='Dubbo方法')
    dubbo_params = models.JSONField(default=dict, verbose_name='Dubbo参数')
    dubbo_group = models.CharField(max_length=50, blank=True, verbose_name='Dubbo分组')
    dubbo_version = models.CharField(max_length=20, blank=True, verbose_name='Dubbo版本')
    
    # 评审
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        verbose_name='评审状态'
    )
    review_comment = models.TextField(blank=True, verbose_name='评审意见')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_test_cases',
        verbose_name='评审人'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='评审时间')
    
    # 统计
    execution_count = models.IntegerField(default=0, verbose_name='执行次数')
    last_execution_status = models.CharField(max_length=20, blank=True, verbose_name='最后执行状态')
    last_executed_at = models.DateTimeField(null=True, blank=True, verbose_name='最后执行时间')
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_test_cases',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
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
    """测试执行记录表"""
    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        verbose_name='测试用例'
    )
    execution_batch = models.CharField(max_length=100, verbose_name='执行批次')
    
    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        verbose_name='执行状态'
    )
    
    # 请求响应
    request_data = models.JSONField(null=True, verbose_name='请求数据')
    response_data = models.JSONField(null=True, verbose_name='响应数据')
    execution_time = models.FloatField(verbose_name='执行耗时(秒)')
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    stack_trace = models.TextField(blank=True, verbose_name='堆栈信息')
    
    executed_at = models.DateTimeField(auto_now_add=True, verbose_name='执行时间')
    
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
    """测试报告表"""
    batch_id = models.CharField(max_length=100, unique=True, verbose_name='批次ID')
    
    # 统计
    total_cases = models.IntegerField(verbose_name='总用例数')
    passed_cases = models.IntegerField(verbose_name='通过数')
    failed_cases = models.IntegerField(verbose_name='失败数')
    error_cases = models.IntegerField(verbose_name='错误数')
    skipped_cases = models.IntegerField(default=0, verbose_name='跳过数')
    pass_rate = models.FloatField(verbose_name='通过率(%)')
    
    # 时间
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    duration = models.FloatField(verbose_name='总耗时(秒)')
    
    # 报告文件
    report_file = models.FileField(upload_to='reports/', verbose_name='报告文件')
    
    # 环境信息
    environment = models.JSONField(default=dict, verbose_name='环境信息')
    
    # 失败用例列表
    failed_details = models.JSONField(default=list, verbose_name='失败详情')
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
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


class GenerationTaskStatus(models.TextChoices):
    """生成任务状态"""
    PENDING = 'PENDING', '等待中'
    ANALYZING = 'ANALYZING', '分析中'
    AI_GENERATING = 'AI_GENERATING', 'AI生成中'
    PARSING = 'PARSING', '解析结果中'
    SAVING = 'SAVING', '保存用例中'
    COMPLETED = 'COMPLETED', '已完成'
    FAILED = 'FAILED', '失败'


class TestCaseGenerationTask(models.Model):
    """测试用例生成任务表"""
    task_id = models.CharField(max_length=100, unique=True, verbose_name='Celery任务ID')
    
    status = models.CharField(
        max_length=20,
        choices=GenerationTaskStatus.choices,
        default=GenerationTaskStatus.PENDING,
        verbose_name='任务状态'
    )
    
    progress = models.IntegerField(default=0, verbose_name='进度(0-100)')
    current_step = models.CharField(max_length=200, blank=True, verbose_name='当前步骤')
    
    # 关联评审
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
    
    # 统计
    total_cases = models.IntegerField(default=0, verbose_name='生成用例总数')
    generated_cases = models.IntegerField(default=0, verbose_name='已生成用例数')
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 时间
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generation_tasks',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    class Meta:
        db_table = 'test_case_generation_task'
        verbose_name = '测试用例生成任务'
        verbose_name_plural = '测试用例生成任务'
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"生成任务 - {self.task_id}"
