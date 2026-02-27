"""
Code Review Agent
"""
from typing import Generator
import json
import logging
from .base import BaseAgent
from apps.repository.models import Repository
from apps.code_review.services import CodeReviewService
from apps.ai_chat.services import AIChatService

logger = logging.getLogger(__name__)

class CodeReviewAgent(BaseAgent):
    """
    代码评审智能体
    状态机：
    - INIT: 初始状态，等待用户输入仓库
    - ASK_REPO: 询问仓库
    - ASK_MODE: 询问评审模式（commit vs branch）
    - ASK_BRANCH: 询问分支
    - EXECUTING: 执行评审中
    - DONE: 评审完成
    """
    
    def run(self) -> Generator[str, None, None]:
        # 获取当前状态
        current_state = self.conversation.context_data.get('state', 'INIT')
        
        # 状态机路由
        if current_state == 'INIT':
            yield from self.handle_init()
        elif current_state == 'ASK_REPO':
            yield from self.handle_ask_repo()
        elif current_state == 'ASK_MODE':
            yield from self.handle_ask_mode()
        elif current_state == 'ASK_SCOPE':
            yield from self.handle_ask_scope()
        elif current_state == 'ASK_AUTHOR':
            yield from self.handle_ask_author()
        elif current_state == 'ASK_COUNT':
            yield from self.handle_ask_count()
        elif current_state == 'ASK_SINCE':
            yield from self.handle_ask_since()
        elif current_state == 'ASK_HASH':
            yield from self.handle_ask_hash()
        elif current_state == 'ASK_BRANCH':
            yield from self.handle_ask_branch()
        else:
            yield "当前状态未知，重置为初始状态。"
            self.update_context('state', 'INIT')

    def handle_init(self):
        """初始状态处理"""
        # 尝试从用户输入中提取仓库名
        repos = Repository.objects.filter(is_active=True)
        repo_names = [r.name for r in repos]
        
        # 简单匹配：如果输入包含某个仓库名
        matched_repo = None
        for repo in repos:
            if repo.name in self.user_message:
                matched_repo = repo
                break
        
        if matched_repo:
            self.update_context('repo_id', matched_repo.id)
            self.update_context('repo_name', matched_repo.name)
            self.update_context('state', 'ASK_MODE')
            yield f"已识别仓库：**{matched_repo.name}**。\n\n请选择评审模式：\n1. 单次提交评审 (默认)\n2. 分支对比评审"
        else:
            self.update_context('state', 'ASK_REPO')
            repo_list_str = "\n".join([f"- {r.name}" for r in repos])
            yield f"请指定要评审的代码仓库。可选仓库：\n{repo_list_str}"

    def handle_ask_repo(self):
        """询问仓库阶段"""
        repos = Repository.objects.filter(is_active=True)
        matched_repo = None
        for repo in repos:
            if repo.name in self.user_message:
                matched_repo = repo
                break
        
        if matched_repo:
            self.update_context('repo_id', matched_repo.id)
            self.update_context('repo_name', matched_repo.name)
            self.update_context('state', 'ASK_MODE')
            yield f"已确认仓库：**{matched_repo.name}**。\n\n请选择评审模式：\n1. 单次提交评审 (默认)\n2. 分支对比评审"
        else:
            yield "未找到指定仓库，请重新输入正确的仓库名称。"

    def handle_ask_mode(self):
        """询问模式阶段"""
        msg = self.user_message.strip()
        if "分支" in msg or "2" in msg:
            self.update_context('review_mode', 'branch')
            self.update_context('state', 'ASK_BRANCH')
            yield "已选择**分支对比评审**模式。\n请输入要对比的源分支名称（例如 `dev` 或 `feature/xxx`），目标分支默认为 `master`。"
        else:
            self.update_context('review_mode', 'commit')
            self.update_context('state', 'ASK_SCOPE') # 进入范围选择
            yield "已选择**单次提交评审**模式。\n\n请选择评审范围（基准）：\n1. 最新提交 (HEAD)\n2. 某位作者的提交\n3. 最近 N 个提交\n4. 指定时间之后的提交\n5. 指定 Commit Hash"

    def handle_ask_scope(self):
        """询问评审范围阶段"""
        msg = self.user_message.strip()
        
        if "作者" in msg or "2" in msg:
            self.update_context('scope_type', 'author')
            self.update_context('state', 'ASK_AUTHOR')
            yield "请输入作者姓名或邮箱（例如 `zhangsan`）："
        elif "最近" in msg or "个" in msg or "3" in msg:
            self.update_context('scope_type', 'count')
            self.update_context('state', 'ASK_COUNT')
            yield "请输入要评审的最近提交数量（例如 `5`）："
        elif "时间" in msg or "4" in msg:
            self.update_context('scope_type', 'since')
            self.update_context('state', 'ASK_SINCE')
            yield "请输入起始时间（例如 `1 day ago`, `2023-10-01`）："
        elif "hash" in msg.lower() or "5" in msg:
            self.update_context('scope_type', 'hash')
            self.update_context('state', 'ASK_HASH')
            yield "请输入 Commit Hash："
        else:
            # 默认为 HEAD
            self.update_context('scope_type', 'head')
            self.update_context('source_branch', 'HEAD')
            yield from self.execute_review()

    def handle_ask_author(self):
        self.update_context('scope_value', self.user_message.strip())
        yield from self.execute_review()

    def handle_ask_count(self):
        self.update_context('scope_value', self.user_message.strip())
        yield from self.execute_review()

    def handle_ask_since(self):
        self.update_context('scope_value', self.user_message.strip())
        yield from self.execute_review()

    def handle_ask_hash(self):
        self.update_context('source_branch', self.user_message.strip()) # 直接作为 source
        yield from self.execute_review()

    def handle_ask_branch(self):
        """询问分支阶段"""
        branch_name = self.user_message.strip()
        self.update_context('source_branch', branch_name)
        self.update_context('target_branch', 'master') # 默认 master
        yield from self.execute_review()

    def execute_review(self):
        """执行评审逻辑"""
        self.update_context('state', 'EXECUTING')
        repo_id = self.context.get('repo_id')
        repo_name = self.context.get('repo_name')
        mode = self.context.get('review_mode', 'commit')
        source_branch = self.context.get('source_branch', 'HEAD') # 默认为 HEAD
        
        yield f"🚀 开始对 **{repo_name}** 进行评审...\n\n"
        
        # 实例化服务
        review_service = CodeReviewService()
        
        # 步骤1：拉取代码
        yield self.stream_step(1, "拉取最新代码", "processing")
        try:
            review_service.pull_repo(repo_id)
            yield self.stream_step(1, "拉取最新代码", "success")
        except Exception as e:
            yield self.stream_step(1, f"拉取代码失败: {str(e)}", "error")
            # 即使拉取失败也尝试继续，或者直接返回
            return

        # 步骤2：获取 Diff
        yield self.stream_step(2, "分析代码变更 (Diff)", "processing")
        diff_content = ""
        try:
            # 默认 target 为 master，后续可配置
            target_branch = self.context.get('target_branch', 'master')
            
            # 如果是 commit 模式，source 可能需要获取最新的 commit hash
            # 目前简化处理，假设 source_branch 存储了分支名或 commit hash
            if mode == 'commit':
                # 如果是 commit 模式但没有指定具体 hash，可以默认取 HEAD
                if not source_branch or source_branch == 'HEAD':
                     # 这里需要 GitService 支持获取最新 commit，暂时传 'HEAD' 让 GitService 处理
                     pass
            
            diff_content = review_service.get_diff(
                repo_id, 
                source_branch, 
                target_branch, 
                scope_type=self.context.get('scope_type', 'head'),
                scope_value=self.context.get('scope_value')
            )
            yield self.stream_step(2, "分析代码变更 (Diff)", "success")
        except Exception as e:
            yield self.stream_step(2, f"获取变更失败: {str(e)}", "error")
            return

        # 步骤3：AI 评审
        yield self.stream_step(3, "DeepSeek 智能评审中", "processing")
        ai_review_result = ""
        try:
            # 调用 review_code，它内部会调用 AI 服务
            # 注意：review_code 目前是同步返回完整结果
            ai_review_result = review_service.review_code(diff_content)
            
            # 流式输出结果（模拟打字机效果，因为 review_code 是同步的）
            # 如果 AIChatService 支持流式返回，这里可以优化
            chunk_size = 10
            for i in range(0, len(ai_review_result), chunk_size):
                yield ai_review_result[i:i+chunk_size]
                # import time
                # time.sleep(0.01) # 微小延迟增加真实感
            
            yield "\n"
            yield self.stream_step(3, "DeepSeek 智能评审中", "success")
        except Exception as e:
            yield self.stream_step(3, f"AI 评审失败: {str(e)}", "error")
            return

        # 步骤4：发送通知
        yield self.stream_step(4, "发送钉钉通知", "processing")
        try:
            success = review_service.send_dingtalk_notification(repo_id, ai_review_result)
            if success:
                yield self.stream_step(4, "发送钉钉通知", "success")
            else:
                yield self.stream_step(4, "发送钉钉通知 (未配置或发送失败)", "processing") # 状态以此提示
        except Exception as e:
            yield self.stream_step(4, f"发送通知失败: {str(e)}", "error")

        yield "\n✅ **评审流程结束**"
        
        # 重置状态，允许下一次评审
        self.update_context('state', 'INIT')
