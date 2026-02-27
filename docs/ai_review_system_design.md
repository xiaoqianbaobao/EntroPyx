# AI智能评审平台 - 系统概要设计文档 v1.0

## 文档版本控制

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|---------|
| v1.0 | 2026-01-19 | 架构团队 | 初始版本 |

---

## 一、系统架构设计

### 1.1 总体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Web前端  │  │  钉钉群  │  │  CI/CD   │  │  IDE插件 │        │
│  │  Vue 3   │  │  机器人  │  │  Jenkins │  │  (未来)  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                         接入层                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Nginx (负载均衡 + SSL卸载 + 静态资源)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         应用层                                    │
│  ┌────────────────────┐       ┌────────────────────┐           │
│  │  Django Web Server │       │   Celery Workers   │           │
│  │  (Gunicorn x 4)    │       │   (评审/测试任务)   │           │
│  │                    │       │                    │           │
│  │ ┌────────────────┐ │       │ ┌────────────────┐ │           │
│  │ │ 用户认证与鉴权  │ │       │ │  代码评审引擎  │ │           │
│  │ │ 仓库配置管理    │ │       │ │  PRD分析引擎   │ │           │
│  │ │ 评审结果查询    │ │       │ │  测试用例生成  │ │           │
│  │ │ 反馈系统       │ │       │ │  Dubbo测试执行 │ │           │
│  │ │ 统计分析看板    │ │       │ │  钉钉消息推送  │ │           │
│  │ └────────────────┘ │       │ └────────────────┘ │           │
│  └────────────────────┘       └────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         服务层                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   Git    │  │    AI    │  │  Dubbo   │  │  钉钉    │       │
│  │  集成    │  │  服务    │  │  服务    │  │  API     │       │
│  │          │  │          │  │          │  │          │       │
│  │ - 克隆   │  │ DeepSeek │  │ Zookeeper│  │ WebHook  │       │
│  │ - Diff   │  │ Claude   │  │ Registry │  │ 签名认证  │       │
│  │ - Fetch  │  │ GPT-4    │  │          │  │          │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         数据层                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │PostgreSQL│  │  Redis   │  │  MinIO   │  │ClickHouse│       │
│  │          │  │          │  │          │  │          │       │
│  │ - 业务数据│  │ - 缓存   │  │ - 文件   │  │ - 日志   │       │
│  │ - 评审记录│  │ - 任务队列│  │ - PRD文档│  │ - 审计   │       │
│  │ - 用户数据│  │ - Session│  │ - 报告   │  │          │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      基础设施层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Docker  │  │   K8s    │  │ Prometheus│ │   ELK    │       │
│  │  容器化  │  │  编排    │  │  监控     │  │  日志    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术架构分层

| 层级 | 技术选型 | 职责 |
|------|---------|------|
| **接入层** | Nginx 1.24 | 负载均衡、SSL卸载、静态资源、限流 |
| **应用层** | Django 4.2 + Gunicorn + Celery | 业务逻辑、异步任务、API服务 |
| **服务层** | Git/AI/Dubbo/钉钉 | 外部服务集成 |
| **数据层** | PostgreSQL + Redis + MinIO + ClickHouse | 数据持久化、缓存、文件、日志 |
| **基础设施** | Docker + K8s + Prometheus + ELK | 容器化、编排、监控、日志 |

---

## 二、核心流程设计

### 2.1 代码评审流程时序图

```
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│Celery│  │Django│  │ Git  │  │  AI  │  │钉钉  │  │ DB   │
│ Beat │  │Worker│  │Service│ │Engine│  │ API  │  │      │
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
   │         │         │         │         │         │
   │ 1.触发定时任务(每90秒)                           │
   ├────────>│         │         │         │         │
   │         │ 2.获取仓库列表                         │
   │         ├────────────────────────────────────────>│
   │         │<────────────────────────────────────────┤
   │         │ 3.遍历每个仓库                          │
   │         ├────────>│         │         │         │
   │         │ 4.fetch origin                          │
   │         │         │ git fetch                      │
   │         │         │ git branch -r                  │
   │         │<────────┤         │         │         │
   │         │ 5.检查今日新提交                        │
   │         ├────────>│         │         │         │
   │         │         │ git log --since=today          │
   │         │<────────┤         │         │         │
   │         │ 6.获取diff和文件内容                    │
   │         ├────────>│         │         │         │
   │         │         │ git diff parent..commit        │
   │         │         │ git show commit:filepath       │
   │         │<────────┤         │         │         │
   │         │ 7.调用AI评审                            │
   │         ├────────────────────>│         │         │
   │         │         │ POST /v1/chat/completions      │
   │         │<────────────────────┤         │         │
   │         │ 8.解析风险评分                          │
   │         │ risk_score = extract_score(response)   │
   │         │ 9.保存评审记录                          │
   │         ├────────────────────────────────────────>│
   │         │<────────────────────────────────────────┤
   │         │ 10.推送钉钉消息                         │
   │         ├────────────────────────────────>│       │
   │         │         │         │ POST /robot/send    │
   │         │<────────────────────────────────┤       │
   │         │ 11.任务完成                             │
   │<────────┤         │         │         │         │
   │         │         │         │         │         │
```

### 2.2 测试用例生成流程

```
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│ User │  │Django│  │Celery│  │  AI  │  │  DB  │
│      │  │ View │  │Worker│  │Engine│  │      │
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
   │         │         │         │         │
   │ 1.选择PRD和代码分支                    │
   ├────────>│         │         │         │
   │         │ 2.创建异步任务                │
   │         ├────────>│         │         │
   │         │<────────┤         │         │
   │<────────┤ 返回任务ID                   │
   │         │         │ 3.读取PRD内容       │
   │         │         ├─────────────────────>│
   │         │         │<─────────────────────┤
   │         │         │ 4.获取代码Diff      │
   │         │         ├─────────────────────>│
   │         │         │<─────────────────────┤
   │         │         │ 5.调用AI生成用例     │
   │         │         ├────────>│         │
   │         │         │ Prompt:            │
   │         │         │ PRD+Diff → 测试用例 │
   │         │         │<────────┤         │
   │         │         │ 6.解析JSON结果      │
   │         │         │ cases = parse(response)
   │         │         │ 7.批量保存用例       │
   │         │         ├─────────────────────>│
   │         │         │<─────────────────────┤
   │         │         │ 8.更新任务状态       │
   │         │         ├─────────────────────>│
   │ 9.轮询任务状态                          │
   ├────────>│         │         │         │
   │<────────┤         │         │         │
   │ 返回生成的用例列表                      │
   │         │         │         │         │
```

### 2.3 接口测试执行流程

```
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│ User │  │Django│  │Celery│  │Dubbo │  │  DB  │
│      │  │ View │  │Worker│  │Client│  │      │
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
   │         │         │         │         │
   │ 1.选择测试用例批量执行                 │
   ├────────>│         │         │         │
   │         │ 2.创建测试批次                │
   │         ├─────────────────────────────>│
   │         │<─────────────────────────────┤
   │         │ 3.创建异步任务(批次执行)      │
   │         ├────────>│         │         │
   │<────────┤         │         │         │
   │         │         │ 4.连接Dubbo注册中心 │
   │         │         ├────────>│         │
   │         │         │ connect(zk_url)    │
   │         │         │<────────┤         │
   │         │         │ 5.遍历测试用例      │
   │         │         │ for case in cases: │
   │         │         │   6.构造请求参数    │
   │         │         │   7.调用Dubbo接口   │
   │         │         ├────────>│         │
   │         │         │ invoke(interface, method, params)
   │         │         │<────────┤         │
   │         │         │   8.断言结果        │
   │         │         │   assert response == expected
   │         │         │   9.记录执行结果    │
   │         │         ├─────────────────────>│
   │         │         │<─────────────────────┤
   │         │         │ 10.生成测试报告     │
   │         │         │ report = generate()│
   │         │         ├─────────────────────>│
   │         │         │<─────────────────────┤
   │ 11.查看测试报告                         │
   ├────────>│         │         │         │
   │<────────┤         │         │         │
   │         │         │         │         │
```

---

## 三、数据库设计

### 3.1 E-R 图

```
┌─────────────┐
│    User     │
│ (用户表)     │
└──────┬──────┘
       │ 1:N
       ↓
┌─────────────┐        ┌─────────────┐
│ Repository  │        │  PRDReview  │
│ (仓库表)     │        │ (PRD评审)   │
└──────┬──────┘        └──────┬──────┘
       │ 1:N                  │ 1:N
       ↓                      ↓
┌─────────────┐        ┌─────────────┐
│ CodeReview  │        │  TestCase   │
│ (代码评审)   │────────│ (测试用例)   │
└──────┬──────┘  1:N   └──────┬──────┘
       │                      │ 1:N
       │ 1:N                  ↓
       ↓                ┌─────────────┐
┌─────────────┐        │TestExecution│
│FeedbackRule │        │ (测试执行)   │
│ (反馈规则)   │        └──────┬──────┘
└─────────────┘               │ N:1
                               ↓
                        ┌─────────────┐
                        │ TestReport  │
                        │ (测试报告)   │
                        └─────────────┘
```

### 3.2 核心表结构设计

#### 3.2.1 用户与权限表

```sql
-- 用户表 (使用Django内置User模型扩展)
CREATE TABLE user_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id),
    role VARCHAR(20) NOT NULL DEFAULT 'developer', -- pm, developer, tester, leader
    department VARCHAR(100),
    dingtalk_user_id VARCHAR(100),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_user_profile_role ON user_profile(role);
```

#### 3.2.2 仓库配置表

```sql
-- 仓库表
CREATE TABLE repository (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    git_url VARCHAR(500) NOT NULL,
    auth_type VARCHAR(20) NOT NULL, -- password, ssh
    username VARCHAR(100),
    password_encrypted TEXT, -- AES加密
    ssh_key_encrypted TEXT,  -- AES加密
    local_path VARCHAR(500) NOT NULL,
    
    -- 钉钉配置
    dingtalk_webhook VARCHAR(500),
    dingtalk_secret VARCHAR(200),
    
    -- 评审配置
    high_risk_threshold DECIMAL(3,2) DEFAULT 0.70,
    medium_risk_threshold DECIMAL(3,2) DEFAULT 0.40,
    
    -- 关键文件规则 (JSON格式)
    critical_patterns JSONB DEFAULT '[]',
    noise_patterns JSONB DEFAULT '[]',
    
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_repository_active ON repository(is_active);
CREATE INDEX idx_repository_created_by ON repository(created_by);
```

#### 3.2.3 代码评审表

```sql
-- 代码评审记录表
CREATE TABLE code_review (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repository(id),
    branch VARCHAR(100) NOT NULL,
    commit_hash VARCHAR(40) NOT NULL,
    commit_message TEXT,
    author VARCHAR(100),
    commit_time TIMESTAMP,
    
    -- 评审结果
    risk_score DECIMAL(4,3) NOT NULL, -- 0.000-1.000
    risk_level VARCHAR(20) NOT NULL,  -- HIGH, MEDIUM, LOW
    ai_review_content TEXT NOT NULL,
    ai_model VARCHAR(50) DEFAULT 'deepseek-coder',
    
    -- 文件变更 (JSON格式)
    changed_files JSONB NOT NULL,
    -- [{status: "A/M/D", path: "xxx.java", is_critical: true}, ...]
    diff_content TEXT,
    
    -- 反馈
    feedback_status VARCHAR(20) DEFAULT 'PENDING',
    -- PENDING, CORRECT, FALSE_POSITIVE, MISSED
    feedback_comment TEXT,
    feedback_by INTEGER REFERENCES auth_user(id),
    feedback_at TIMESTAMP,
    
    -- 推送状态
    dingtalk_sent BOOLEAN DEFAULT FALSE,
    dingtalk_sent_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(repository_id, commit_hash)
);

CREATE INDEX idx_code_review_repo_branch ON code_review(repository_id, branch);
CREATE INDEX idx_code_review_risk_level ON code_review(risk_level);
CREATE INDEX idx_code_review_created_at ON code_review(created_at DESC);
CREATE INDEX idx_code_review_author ON code_review(author);
CREATE INDEX idx_code_review_feedback ON code_review(feedback_status);
```

#### 3.2.4 PRD评审表

```sql
-- PRD评审表
CREATE TABLE prd_review (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL, -- word, md, pdf
    file_size INTEGER,
    
    -- AI提取的结构化内容
    background TEXT,
    user_stories JSONB DEFAULT '[]',
    -- [{story: "xxx", acceptance: "xxx"}, ...]
    requirements JSONB DEFAULT '[]',
    -- [{id: "REQ001", description: "xxx", priority: "P0"}, ...]
    
    -- 评审维度得分
    completeness_score DECIMAL(4,3), -- 完整性 0-1
    consistency_score DECIMAL(4,3),  -- 一致性 0-1
    risk_score DECIMAL(4,3),         -- 风险 0-1
    overall_score DECIMAL(4,3),      -- 综合得分
    
    -- AI建议
    ai_suggestions TEXT,
    issues_found JSONB DEFAULT '[]',
    -- [{type: "completeness", description: "xxx", severity: "high"}, ...]
    
    -- 人工评审
    review_status VARCHAR(20) DEFAULT 'PENDING',
    -- PENDING, APPROVED, REJECTED
    review_comment TEXT,
    reviewed_by INTEGER REFERENCES auth_user(id),
    reviewed_at TIMESTAMP,
    
    created_by INTEGER NOT NULL REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prd_review_created_by ON prd_review(created_by);
CREATE INDEX idx_prd_review_status ON prd_review(review_status);
CREATE INDEX idx_prd_review_score ON prd_review(overall_score DESC);
```

#### 3.2.5 测试用例表

```sql
-- 测试用例表
CREATE TABLE test_case (
    id SERIAL PRIMARY KEY,
    prd_review_id INTEGER REFERENCES prd_review(id),
    code_review_id INTEGER REFERENCES code_review(id),
    
    case_id VARCHAR(50) NOT NULL UNIQUE, -- TC001, TC002...
    title VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL, -- FUNCTION, BOUNDARY, EXCEPTION, PERFORMANCE
    priority VARCHAR(10) NOT NULL, -- P0, P1, P2
    
    -- 用例内容
    precondition TEXT,
    steps JSONB NOT NULL, -- ["step1", "step2", ...]
    expected_result TEXT NOT NULL,
    
    -- Dubbo调用配置
    dubbo_interface VARCHAR(200),
    dubbo_method VARCHAR(100),
    dubbo_params JSONB DEFAULT '{}',
    dubbo_group VARCHAR(50),
    dubbo_version VARCHAR(20),
    
    -- 评审
    review_status VARCHAR(20) DEFAULT 'PENDING',
    review_comment TEXT,
    reviewed_by INTEGER REFERENCES auth_user(id),
    reviewed_at TIMESTAMP,
    
    -- 统计
    execution_count INTEGER DEFAULT 0,
    last_execution_status VARCHAR(20),
    last_execution_at TIMESTAMP,
    
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_test_case_prd ON test_case(prd_review_id);
CREATE INDEX idx_test_case_code ON test_case(code_review_id);
CREATE INDEX idx_test_case_type ON test_case(type);
CREATE INDEX idx_test_case_priority ON test_case(priority);
```

#### 3.2.6 测试执行表

```sql
-- 测试执行记录表
CREATE TABLE test_execution (
    id SERIAL PRIMARY KEY,
    test_case_id INTEGER NOT NULL REFERENCES test_case(id),
    execution_batch VARCHAR(100) NOT NULL, -- 批次号: BATCH_20260119_001
    
    status VARCHAR(20) NOT NULL, -- RUNNING, PASSED, FAILED, ERROR
    
    -- 请求响应
    request_data JSONB,
    response_data JSONB,
    execution_time DECIMAL(10,3), -- 执行耗时(秒)
    
    -- 错误信息
    error_message TEXT,
    stack_trace TEXT,
    
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_test_execution_case ON test_execution(test_case_id);
CREATE INDEX idx_test_execution_batch ON test_execution(execution_batch);
CREATE INDEX idx_test_execution_status ON test_execution(status);
CREATE INDEX idx_test_execution_time ON test_execution(executed_at DESC);

-- 测试报告表
CREATE TABLE test_report (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- 统计
    total_cases INTEGER NOT NULL,
    passed_cases INTEGER NOT NULL,
    failed_cases INTEGER NOT NULL,
    error_cases INTEGER NOT NULL,
    skipped_cases INTEGER DEFAULT 0,
    pass_rate DECIMAL(5,2), -- 通过率百分比
    
    -- 时间
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration DECIMAL(10,2), -- 总耗时(秒)
    
    -- 报告文件
    report_file VARCHAR(500), -- HTML报告路径
    
    -- 环境信息
    environment JSONB DEFAULT '{}',
    -- {dubbo_registry: "xxx", python_version: "3.11", ...}
    
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_test_report_batch ON test_report(batch_id);
CREATE INDEX idx_test_report_time ON test_report(created_at DESC);
```

#### 3.2.7 反馈规则表

```sql
-- 反馈优化规则表
CREATE TABLE feedback_rule (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(20) NOT NULL, -- WHITELIST, BLACKLIST
    pattern TEXT NOT NULL, -- 正则表达式或关键词
    description TEXT,
    weight DECIMAL(3,2) DEFAULT 1.0, -- 权重 0.0-2.0
    
    -- 统计
    feedback_count INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5,2) DEFAULT 0.0,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_rule_type ON feedback_rule(rule_type);
CREATE INDEX idx_feedback_rule_active ON feedback_rule(is_active);
```

---

## 四、关键技术方案

### 4.1 Git 集成方案

**技术选型**: GitPython 3.1+

**核心功能**:
```python
class GitService:
    """Git 仓库操作服务"""
    
    def __init__(self, repo_config: Repository):
        self.repo = repo_config
        self.local_path = Path(repo_config.local_path)
    
    def ensure_repo(self):
        """确保仓库已克隆"""
        if not self.local_path.exists():
            self._clone()
        else:
            self._fetch()
    
    def get_today_commits(self, branch: str) -> List[str]:
        """获取今日新提交"""
        repo = git.Repo(self.local_path)
        today = date.today().strftime("%Y-%m-%d")
        commits = list(repo.iter_commits(
            f'origin/{branch}',
            since=f'{today} 00:00:00'
        ))
        return [c.hexsha for c in commits]
    
    def get_diff_and_files(self, commit_hash: str) -> Tuple[str, List[dict]]:
        """获取 Diff 和文件变更"""
        repo = git.Repo(self.local_path)
        commit = repo.commit(commit_hash)
        
        # 获取 Diff
        if commit.parents:
            diff = commit.parents[0].diff(commit, create_patch=True, unified=5)
        else:
            # 首次提交
            diff = commit.diff(git.NULL_TREE, create_patch=True)
        
        # 获取文件列表
        files = []
        for d in diff:
            files.append({
                'status': d.change_type,  # A/M/D/R
                'path': d.b_path or d.a_path,
                'is_critical': self._is_critical_file(d.b_path or d.a_path)
            })
        
        diff_text = '\n'.join([d.diff.decode('utf-8', errors='replace') for d in diff])
        return diff_text, files
```

### 4.2 AI 评审引擎

**多模型支持架构**:
```python
class AIReviewEngine:
    """AI评审引擎 - 支持多模型"""
    
    def __init__(self):
        self.models = {
            'deepseek': DeepSeekClient(),
            'claude': ClaudeClient(),
            'gpt4': GPT4Client()
        }
    
    def review_code(
        self,
        diff: str,
        files: List[dict],
        commit_msg: str,
        model: str = 'deepseek',
        multi_model_vote: bool = False
    ) -> ReviewResult:
        """代码评审"""
        
        if multi_model_vote:
            # 多模型投票模式
            results = []
            for model_name in ['deepseek', 'claude', 'gpt4']:
                result = self._single_model_review(
                    model_name, diff, files, commit_msg
                )
                results.append(result)
            
            # 投票算法：取平均风险分，综合建议
            return self._merge_results(results)
        else:
            # 单模型模式
            return self._single_model_review(model, diff, files, commit_msg)
    
    def _single_model_review(
        self, 
        model: str, 
        diff: str, 
        files: List[dict],
        commit_msg: str
    ) -> ReviewResult:
        """单个模型评审"""
        
        # 构造 Prompt
        prompt = self._build_prompt(diff, files, commit_msg)
        
        # 调用 AI
        client = self.models[model]
        response = client.chat(prompt)
        
        # 解析结果
        risk_score = self._extract_risk_score(response)
        issues = self._extract_issues(response)
        
        return ReviewResult(
            risk_score=risk_score,
            risk_level=self._get_risk_level(risk_score),
            content=response,
            issues=issues,
            model=model
        )