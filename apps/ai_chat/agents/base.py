"""
智能体基础框架
定义 BaseAgent 类，规范 Agent 的接口和行为
"""
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Generator, List, Optional

class BaseAgent(ABC):
    """
    智能体基类
    """
    
    def __init__(self, conversation, user_message: str):
        """
        初始化智能体
        :param conversation: Conversation 模型实例
        :param user_message: 用户最新输入的消息
        """
        self.conversation = conversation
        self.user_message = user_message
        self.context = conversation.context_data or {}
        
    def update_context(self, key: str, value: Any):
        """更新上下文数据"""
        self.context[key] = value
        self.conversation.context_data = self.context
        self.conversation.save(update_fields=['context_data'])
        
    def set_mode(self, mode: str):
        """切换对话模式"""
        self.conversation.current_mode = mode
        self.conversation.save(update_fields=['current_mode'])
        
    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史"""
        messages = self.conversation.messages.all().order_by('created_at')
        # 取最近的消息，但保留system prompt（如果有）
        # 这里简化处理，直接取最近N条
        recent_messages = messages[max(0, messages.count() - limit):]
        return [{"role": msg.role, "content": msg.content} for msg in recent_messages]
    
    @abstractmethod
    def run(self) -> Generator[str, None, None]:
        """
        运行智能体，生成流式响应
        子类必须实现此方法
        """
        pass
        
    def stream_step(self, step_id: int, title: str, status: str = 'processing'):
        """
        发送步骤更新事件
        格式: [STEP_UPDATE]: {"id": 1, "title": "拉取代码", "status": "processing"}
        status: processing, success, error
        """
        event_data = {
            "id": step_id,
            "title": title,
            "status": status
        }
        return f"[STEP_UPDATE]: {json.dumps(event_data)}"

    def stream_thought(self, content: str):
        """
        发送思考过程
        格式: [THOUGHT]: 正在分析代码...
        """
        return f"[THOUGHT]: {content}"
