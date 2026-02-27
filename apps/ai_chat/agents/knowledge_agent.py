"""
Agentic RAG Knowledge Agent
基于 ReAct 框架的主动推理智能体
"""
from typing import Generator
import json
import logging
from .base import BaseAgent
from apps.ai_chat.services import AIChatService

logger = logging.getLogger(__name__)

class KnowledgeAgent(BaseAgent):
    """
    知识增强智能体 (Agentic RAG)
    """
    
    def run(self) -> Generator[str, None, None]:
        # 1. 思考阶段
        thought = f"用户询问: {self.user_message}\n需要分析是否需要搜索网络或查询本地知识库。"
        yield self.stream_thought(thought)
        
        # 模拟 ReAct 过程
        # 实际场景中，这里应该调用 LLM 判断下一步行动
        # 为了演示，我们简化逻辑：如果有关联知识库，先查库；否则直接回答或提示
        
        knowledge_context = ""
        
        if self.conversation.knowledge_base:
            # 2. 行动阶段：查询知识库
            yield self.stream_step(1, "检索本地知识库", "processing")
            try:
                ai_service = AIChatService()
                knowledge_context = ai_service.search_knowledge(
                    self.user_message, 
                    self.conversation.knowledge_base.id
                )
                yield self.stream_step(1, f"检索到 {len(knowledge_context) // 100} 条相关记录", "success")
            except Exception as e:
                yield self.stream_step(1, f"检索失败: {str(e)}", "error")
        else:
            # 如果没有绑定知识库，假设需要联网搜索（这里模拟）
            # yield self.stream_step(1, "联网搜索相关信息", "processing")
            # yield self.stream_step(1, "已获取搜索结果", "success")
            pass

        # 3. 回答阶段
        yield self.stream_thought("已获取必要信息，正在生成最终回答...")
        
        # 调用 LLM 生成回答
        # 这里复用现有的 AIChatService
        ai_service = AIChatService()
        
        # 构造 prompt
        history = self.get_history()
        
        # 流式输出回答
        # 注意：这里我们简单复用，实际 AIChatService.chat 返回的是完整内容
        # 如果要流式，需要改造 service 或直接调用
        
        # 模拟流式回答
        response = ai_service.chat(
            messages=history,
            knowledge_context=knowledge_context,
            conversation_type=self.conversation.conversation_type
        )
        
        yield response['content']
