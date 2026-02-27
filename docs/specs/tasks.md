# 任务分解清单 (Tasks Breakdown)

## 阶段一：基础架构升级与代码评审智能体 (Phase 1: Agent Infrastructure & Code Review Agent)

### 1.1 数据库与模型迁移 (Database & Models)
- [ ] 扩展 `Conversation` 模型：
    - 添加 `current_mode` (chat, code_review_flow, agent_rag)。
    - 添加 `context_data` (JSONField) 存储对话上下文（如 `repo_id`）。
- [ ] 扩展 `Repository` 模型：
    - 添加 `dingtalk_webhook` 字段。
- [ ] 执行数据库迁移 (`makemigrations`, `migrate`)。

### 1.2 智能体核心框架 (Agent Core)
- [ ] 创建 `apps/ai_chat/agents/` 目录。
- [ ] 实现 `BaseAgent` 基类：
    - 定义 `run(query, context)` 抽象方法。
    - 定义 `get_response()` 和 `update_state()`。
- [ ] 实现 `Dispatcher` 调度器：
    - 在 `chat_stream_view` 中根据 `current_mode` 或用户输入关键字进行路由。

### 1.3 代码评审智能体实现 (Code Review Agent Implementation)
- [ ] 实现 `CodeReviewAgent` 类：
    - 状态机设计：`INIT` -> `ASK_REPO` -> `ASK_MODE` -> `ASK_BRANCH` -> `EXECUTING` -> `DONE`。
    - `handle_input(user_msg)`: 处理用户输入并更新状态。
    - `execute_review()`: 执行核心评审逻辑。
- [ ] 工具函数集成：
    - `git_pull(repo_path)`: 拉取最新代码。
    - `get_diff(repo_path, source, target)`: 获取分支 Diff。
    - `dingtalk_notify(webhook, content)`: 发送钉钉消息。
- [ ] 集成 DeepSeek API 进行评审分析。

### 1.4 前端交互增强 (Frontend Enhancements)
- [ ] 修改 `ai_chat.js`：
    - 支持解析后端 SSE 推送的结构化事件（如 `[STEP_UPDATE]: {"step": 1, "status": "done"}`）。
    - 渲染步骤条组件（Step Progress Bar）。
- [ ] 优化输入框交互：
    - 当处于 `ASK_REPO` 状态时，尝试提供仓库自动补全（可选）。

---

## 阶段二：Agentic RAG 智能体 (Phase 2: Agentic RAG / Knowledge Agent)

### 2.1 搜索工具集成 (Search Tools)
- [ ] 集成 Web Search API (如 Serper/Google/Bing，或使用模拟搜索)。
- [ ] 实现 `WebSearchTool` 类。

### 2.2 知识库检索增强 (Knowledge Retrieval)
- [ ] 优化现有的 `AIChatService.search_knowledge` 方法，使其支持更灵活的查询参数。
- [ ] 实现 `KnowledgeBaseTool` 类。

### 2.3 推理循环实现 (Reasoning Loop)
- [ ] 实现 `KnowledgeAgent` 类（继承自 `BaseAgent`）。
- [ ] 实现 ReAct (Reasoning + Acting) 循环：
    - `Thought`: 分析当前状态。
    - `Action`: 选择工具（Search 或 Knowledge）。
    - `Observation`: 获取工具执行结果。
    - `Final Answer`: 生成最终回复。
- [ ] 提示词工程 (Prompt Engineering)：设计用于 Agentic RAG 的系统提示词。

### 2.4 前端展示 (Frontend Display)
- [ ] 支持折叠/展开“思考过程” (`<details>`).
- [ ] 渲染引用来源（Citation）。
