# 熵减X-AI 智能体系统与Agentic RAG 2.0 升级规格说明书

## 1. 概述 (Overview)

本版本旨在将 AI Chat 模块从简单的问答服务升级为具备自主规划、工具调用和多轮对话能力的**智能体调度系统 (Agent Orchestration System)**。
主要涵盖两大核心智能体：
1.  **代码评审智能体 (Code Review Agent)**：支持多轮对话配置、分支对比评审、实时步骤反馈与钉钉通知。
2.  **知识增强智能体 (Knowledge Agent / RAG 2.0)**：基于 Agentic RAG 架构，从被动检索升级为主动推理，集成网络搜索与本地知识库。

---

## 2. 核心功能规格 (Feature Specifications)

### 2.1 智能调度中心 (Central Dispatcher)
作为 AI Chat 的大脑，负责意图识别与任务分发。

*   **意图识别 (Intent Recognition)**：
    *   根据用户输入判断意图：`code_review` (代码评审), `knowledge_qa` (知识问答), `general_chat` (通用闲聊)。
    *   **上下文感知**：能够根据上一轮对话状态维持当前任务（例如处于代码评审配置阶段）。
*   **工具注册表 (Tool Registry)**：
    *   维护所有可用工具的定义与调用接口。
    *   支持动态加载工具（如搜索工具、Git工具、通知工具）。

### 2.2 代码评审智能体 (Code Review Agent)
一个专注于代码质量分析的任务型智能体。

*   **多轮对话配置 (Slot Filling)**：
    *   **触发**：用户输入“我要评审代码”或“评审 [仓库名]”。
    *   **参数收集**：
        *   **仓库选择**：若未指定，列出可选仓库供用户选择（或输入）。
        *   **评审模式**：询问是“单次提交评审 (Commit Review)”还是“分支对比评审 (Branch Review)”。
        *   **分支选择**：若选择分支评审，询问“源分支”和“目标分支”（默认 master）。
*   **执行工作流 (Workflow Execution)**：
    1.  **拉取仓库 (Git Pull)**：更新本地仓库代码。
    2.  **获取 Diff (Get Diff)**：根据模式获取变更内容（`git show` 或 `git diff`）。
    3.  **智能评审 (AI Review)**：调用 DeepSeek API 分析 Diff，关注 Bug、安全漏洞、代码规范。
    4.  **生成报告 (Report Generation)**：汇总评审意见。
    5.  **发送通知 (Notify)**：将报告摘要发送至钉钉群（需配置 Webhook）。
*   **实时反馈 (Live Feedback)**：
    *   在对话框中以“步骤流 (Step Stream)”形式显示当前进展（如 `> [执行中] 正在拉取仓库...`）。
    *   完成后显示 `Done` 状态。

### 2.3 Agentic RAG 智能体 (Knowledge Agent)
基于 RAG 2.0 架构的主动推理智能体。

*   **主动推理 (Active Reasoning)**：
    *   不再仅仅检索一次，而是基于 ReAct (Reasoning + Acting) 框架。
    *   **思考 (Thought)**：分析问题需要哪些信息。
    *   **行动 (Action)**：决定检索本地知识库还是搜索互联网。
    *   **观察 (Observation)**：阅读检索结果，判断是否满足需求。
    *   **回答 (Answer)**：综合信息生成最终答案。
*   **工具集 (Tools)**：
    *   **本地知识库工具 (Local Knowledge Tool)**：检索向量数据库（Chroma/Milvus）。
    *   **网络搜索工具 (Web Search Tool)**：调用搜索引擎 API（如 Bing/Google/Serper）获取实时信息。
    *   **网页抓取工具 (Web Scraper)**：获取搜索结果的具体内容。

---

## 3. 技术架构 (Technical Architecture)

### 3.1 后端架构 (Backend)
*   **Agent Framework**：
    *   在 `apps/ai_chat/agents/` 下构建轻量级 Agent 框架。
    *   `BaseAgent`: 定义 `run()`, `plan()`, `execute_tool()` 接口。
    *   `CodeReviewAgent`: 继承 BaseAgent，实现状态机（State Machine）。
    *   `KnowledgeAgent`: 继承 BaseAgent，实现 ReAct 循环。
*   **状态管理 (State Management)**：
    *   利用 Django Cache 或 Database 存储会话状态（`conversation_id` -> `current_agent`, `agent_state`, `slots`）。
*   **流式响应增强 (Streaming Enhancement)**：
    *   扩展 SSE (Server-Sent Events) 协议，支持结构化事件（`status_update`, `thought_process`, `final_answer`）。

### 3.2 前端架构 (Frontend)
*   **智能体 UI 组件**：
    *   **步骤条 (Step Indicator)**：用于显示代码评审的 4 个步骤状态。
    *   **思维链展示 (CoT Display)**：用于折叠/展开 Agentic RAG 的思考过程（"Thinking..."）。
*   **交互逻辑**：
    *   支持渲染后端返回的 Markdown + 自定义组件标记。
    *   增强输入框，支持在特定状态下（如选择分支）提供自动补全或快捷选项。

---

## 4. 交互设计 (Interaction Design)

### 4.1 代码评审场景
> **User**: 我要评审 entropyx-ai 仓库。
> **Agent**: 好的。请选择评审模式：
> 1. 单次提交评审
> 2. 分支对比评审 (Current vs Master)
> **User**: 2
> **Agent**: 明白。请确认源分支名称（默认为当前分支）：
> **User**: dev
> **Agent**: 开始执行分支对比评审 (dev -> master)...
> *   [√] 步骤1: 拉取仓库... 完成
> *   [√] 步骤2: 获取 Diff (3 files changed)... 完成
> *   [>] 步骤3: 调用 DeepSeek API 进行评审... (正在进行)
> *   [ ] 步骤4: 发送钉钉群通知...
> **Agent**: (评审完成后) 评审已完成！发现 2 个潜在 Bug，详情如下... [钉钉通知已发送]

### 4.2 Agentic RAG 场景
> **User**: 分析一下最新的 DeepSeek V3 技术特点，并结合本地知识库中的部署文档给出建议。
> **Agent**: (进入思考模式)
> *   *Thought: 用户需要 DeepSeek V3 的最新特点（需要联网）和本地部署建议（需要查库）。*
> *   *Action: SearchWeb("DeepSeek V3 technical features")*
> *   *Observation: 获取到 V3 的 MoE 架构、性能数据...*
> *   *Action: SearchKnowledge("DeepSeek deployment guide")*
> *   *Observation: 获取到本地关于 GPU 显存要求的文档...*
> *   *Final Answer:* DeepSeek V3 的主要技术特点是... 结合您的本地环境，建议配置...

---

## 5. 数据库变更 (Database Changes)

*   **Conversation**:
    *   新增 `current_mode` (varchar): 记录当前对话所属模式（chat, code_review_flow, agent_rag）。
    *   新增 `context_data` (json): 存储多轮对话的槽位数据（如 `repo_id`, `branch`）。
*   **Repository**:
    *   新增 `dingtalk_webhook` (varchar): 存储钉钉机器人地址。
