"""
AI对话服务
集成DeepSeek API和知识库
"""
import json
import time
import requests
from typing import Dict, List, Optional
from django.conf import settings
from django.db.models import Q
from apps.knowledge_base.models import KnowledgeDocument


class AIChatService:
    """AI对话服务"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model or getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-coder')
        self.api_base = getattr(settings, 'DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
        self.max_tokens = 2000
        self.temperature = 0.7
    
    def chat(self, messages: List[Dict], knowledge_context: str = None, 
             conversation_type: str = 'general', repository_id: int = None, knowledge_base_id: int = None) -> Dict:
        """
        发送对话消息
        
        Args:
            messages: 对话历史，格式：[{"role": "user/assistant", "content": "消息内容"}]
            knowledge_context: 知识库上下文（已弃用，保留兼容）
            conversation_type: 对话类型 ('chat' 或 'agent')
            repository_id: 关联仓库ID
            knowledge_base_id: 关联知识库ID
            
        Returns:
            Dict: {"content": "回复内容", "tokens_used": 100, "knowledge_references": []}
        """
        # 硬编码新 API 配置
        api_url = "https://ocrserver.bestpay.com.cn/new/kjqxggpiunyitolh-serving/v1/chat/completions"
        api_key = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkRIRmJwb0lVcXJZOHQyenBBMnFYZkNtcjVWTzVaRXI0UnpIVV8tZW52dlEiLCJ0eXAiOiJKV1QifQ.eyJleHAiOjIwNzA4NTkyMDEsImlhdCI6MTc1NTQ5OTIwMSwiaXNzIjoia2pxeGdncGl1bnlpdG9saC1zZXJ2aW5nIiwic3ViIjoia2pxeGdncGl1bnlpdG9saC1zZXJ2aW5nIn0.es1OGw3drT0cTwtld1tNtXuCofejuQUDhswG_qvbjQHyBqGcLd5xSZD08U9586xDiYN2crLuT2OB3UT0j1wvIEGYZxL4R8mnbGL7MSBJCiEepP-AxOi4wmMSnkxW5lozKpmuFM-Oe3CcuTb6ZkM-J7INHPdcWsZb7DrGfkBA9-aVSvmxheIvFpkV4pi89BdblPtWQX-B4ZvlHCnQbbIoF-w90iCxyZq7cc4BLadHks-VutQvVbOjqz5Jnvc03QPeCz_zH4LMG-hvQUpe6hCOZVyRcfAQMJg51V5iqnPh-X2eOEQMPy6zj62Nq8nppOtPRHgJm9pz3Pxdm_Z4tJnvrw"
        
        try:
            start_time = time.time()
            
            # 1. 检索上下文（如果指定了仓库或知识库）
            retrieved_context = ""
            user_query = messages[-1]['content']
            
            if repository_id:
                repo_context = self._search_repository(repository_id, user_query)
                if repo_context:
                    retrieved_context += f"\n【代码仓库参考】\n{repo_context}\n"
            
            if knowledge_base_id:
                kb_context = self._search_knowledge_base(knowledge_base_id, user_query)
                if kb_context:
                    retrieved_context += f"\n【知识库参考】\n{kb_context}\n"
            
            # 兼容旧参数
            if knowledge_context:
                retrieved_context += f"\n{knowledge_context}\n"
            
            # 2. 构建系统提示词
            system_prompt = self._build_system_prompt(conversation_type, retrieved_context)
            
            # 3. 构建消息列表
            api_messages = [{"role": "system", "content": system_prompt}]
            api_messages.extend(messages[-10:])  # 只保留最近10条消息
            
            # 4. 调用API
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-ai/DeepSeek-V2.5", # 使用新接口支持的模型名
                    "messages": api_messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False
                },
                timeout=120,
                verify=False # 忽略SSL证书验证
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            
            # 提取知识库引用
            knowledge_references = self._extract_knowledge_references(content)
            
            response_time = time.time() - start_time
            
            return {
                "content": content,
                "tokens_used": tokens_used,
                "knowledge_references": knowledge_references,
                "response_time": response_time,
                "model": self.model
            }
            
        except Exception as e:
            import logging
            logging.error(f"AI对话失败: {str(e)}")
            return {
                "content": f"抱歉，对话处理失败: {str(e)}",
                "tokens_used": 0,
                "knowledge_references": [],
                "response_time": 0,
                "model": self.model,
                "error": str(e)
            }

    def stream_chat(self, messages: List[Dict], knowledge_context: str = None, 
                   conversation_type: str = 'general', repository_id: int = None, knowledge_base_id: int = None):
        """
        流式发送对话消息
        """
        try:
            # 优先从数据库获取配置
            from apps.platform_management.models import LLMConfig
            llm_config = LLMConfig.objects.filter(is_active=True).first()
            
            if llm_config:
                api_url = llm_config.api_base.rstrip('/') + '/chat/completions'
                api_key = llm_config.api_key
                model = llm_config.model_name
            else:
                # 硬编码新 API 配置
                api_url = "https://ocrserver.bestpay.com.cn/new/kjqxggpiunyitolh-serving/v1/chat/completions"
                api_key = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkRIRmJwb0lVcXJZOHQyenBBMnFYZkNtcjVWTzVaRXI0UnpIVV8tZW52dlEiLCJ0eXAiOiJKV1QifQ.eyJleHAiOjIwNzA4NTkyMDEsImlhdCI6MTc1NTQ5OTIwMSwiaXNzIjoia2pxeGdncGl1bnlpdG9saC1zZXJ2aW5nIiwic3ViIjoia2pxeGdncGl1bnlpdG9saC1zZXJ2aW5nIn0.es1OGw3drT0cTwtld1tNtXuCofejuQUDhswG_qvbjQHyBqGcLd5xSZD08U9586xDiYN2crLuT2OB3UT0j1wvIEGYZxL4R8mnbGL7MSBJCiEepP-AxOi4wmMSnkxW5lozKpmuFM-Oe3CcuTb6ZkM-J7INHPdcWsZb7DrGfkBA9-aVSvmxheIvFpkV4pi89BdblPtWQX-B4ZvlHCnQbbIoF-w90iCxyZq7cc4BLadHks-VutQvVbOjqz5Jnvc03QPeCz_zH4LMG-hvQUpe6hCOZVyRcfAQMJg51V5iqnPh-X2eOEQMPy6zj62Nq8nppOtPRHgJm9pz3Pxdm_Z4tJnvrw"
                model = "deepseek-ai/DeepSeek-V2.5"
            
            # 1. 检索上下文
            retrieved_context = ""
            user_query = messages[-1]['content']
            
            if repository_id:
                repo_context = self._search_repository(repository_id, user_query)
                if repo_context:
                    retrieved_context += f"\n【代码仓库参考】\n{repo_context}\n"
            
            if knowledge_base_id:
                kb_context = self._search_knowledge_base(knowledge_base_id, user_query)
                if kb_context:
                    retrieved_context += f"\n【知识库参考】\n{kb_context}\n"
            
            if knowledge_context:
                retrieved_context += f"\n{knowledge_context}\n"
            
            # 2. 构建系统提示词
            system_prompt = self._build_system_prompt(conversation_type, retrieved_context)
            
            # 3. 构建消息列表
            api_messages = [{"role": "system", "content": system_prompt}]
            api_messages.extend(messages[-10:])
            
            # 4. 调用API (流式)
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": api_messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": True # 开启流式
                },
                timeout=120,
                verify=False,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            import logging
            logging.error(f"AI流式对话失败: {str(e)}")
            yield f"Error: {str(e)}"

    def _search_repository(self, repository_id: int, query: str) -> str:
        """检索代码仓库内容"""
        # 简单实现：查询最近的代码评审记录或关键文件
        # 实际应对接向量数据库或代码搜索服务
        from apps.code_review.models import CodeReview
        reviews = CodeReview.objects.filter(repository_id=repository_id).order_by('-created_at')[:3]
        
        context = ""
        for review in reviews:
            context += f"提交: {review.commit_hash[:7]} - {review.commit_message}\n"
            context += f"评审摘要: {review.ai_summary[:200]}...\n\n"
        return context

    def _search_knowledge_base(self, kb_id: int, query: str) -> str:
        """检索知识库内容"""
        from apps.knowledge_base.rag import RAGEngine
        
        # 使用 RAG 引擎进行检索
        rag_engine = RAGEngine()
        
        # 如果指定了知识库ID，可以作为 metadata 过滤条件 (假设 RAGEngine 支持 filter)
        # 这里暂时全局搜索，因为 RAGEngine 目前设计为单集合
        results = rag_engine.search(query, top_k=3)
        
        context = ""
        for res in results:
            title = res.get('metadata', {}).get('title', '未知文档')
            content = res.get('content', '')
            score = res.get('score', 0)
            context += f"文档: {title} (相关度: {score:.2f})\n片段: {content}\n\n"
            
        return context
    
    def _build_system_prompt(self, conversation_type: str, knowledge_context: str = None) -> str:
        """
        构建系统提示词
        
        Args:
            conversation_type: 对话类型 ('chat' 或 'agent')
            knowledge_context: 知识库上下文
            
        Returns:
            str: 系统提示词
        """
        if conversation_type == 'agent':
            base_prompt = """你是一个高阶智能研发Agent，具备执行复杂软件工程任务的能力。
你的职责包括但不限于：
1. 代码评审：深入分析代码逻辑，发现潜在Bug、安全漏洞和性能瓶颈。
2. 重构建议：提供具体的代码重构方案，提升代码可读性和可维护性。
3. PRD分析：评审产品需求文档，指出逻辑漏洞、边界情况缺失等问题。
4. 测试生成：根据需求或代码自动生成覆盖率高的测试用例。

请以资深技术专家的口吻回答，回答应包含具体的操作步骤、代码示例或文档草稿。
"""
        else: # chat
            base_prompt = """你是一个专业的研发知识助手，专注于解答软件开发相关的问题。
你的职责是：
1. 基于提供的知识库和代码仓库信息，回答用户的技术咨询。
2. 解释复杂的业务逻辑和代码实现。
3. 提供技术方案的建议和对比。

请以乐于助人的技术顾问口吻回答，回答应准确、清晰，并引用参考资料。
"""
        
        if knowledge_context:
            base_prompt += f"\n【参考上下文】\n以下是检索到的相关信息，请优先基于这些信息回答：\n{knowledge_context}\n"
            
        return base_prompt
    
    def _extract_knowledge_references(self, content: str) -> List[Dict]:
        """
        从回复中提取知识库引用
        
        Args:
            content: AI回复内容
            
        Returns:
            List[Dict]: 引用列表
        """
        references = []
        
        # 简单的提取逻辑，可以根据实际情况优化
        if "【知识库参考】" in content:
            # 提取文档ID和标题
            import re
            matches = re.findall(r'文档: (.+?)\n', content)
            for match in matches:
                references.append({
                    "title": match,
                    "type": "knowledge_base"
                })
        
        return references
    
    def _mock_response(self, messages: List[Dict], knowledge_context: str = None) -> Dict:
        """
        模拟响应（用于测试或API密钥未配置时）
        
        Args:
            messages: 对话历史
            knowledge_context: 知识库上下文
            
        Returns:
            Dict: 模拟的响应
        """
        import time
        time.sleep(1)  # 模拟网络延迟
        
        last_message = messages[-1]['content'] if messages else "你好"
        
        mock_responses = {
            "你好": "你好！我是AI智能评审助手，可以帮助你进行代码评审、PRD分析、测试用例生成等工作。请问有什么可以帮你的吗？",
            "代码": "我可以帮助你进行代码评审。你可以：\n\n1. 上传代码片段，我会分析代码质量\n2. 询问最佳实践和优化建议\n3. 生成单元测试用例\n4. 检查潜在的安全问题\n\n请提供具体的代码或问题。",
            "PRD": "我可以帮助你评审PRD文档。我可以检查：\n\n1. 需求完整性\n2. 一致性和可行性\n3. 用户体验设计\n4. 技术实现方案\n\n你可以上传PRD文档或直接描述需求。",
            "测试": "我可以帮助你生成测试用例。请告诉我：\n\n1. 测试什么功能？\n2. 有哪些业务场景？\n3. 需要覆盖哪些边界条件？\n\n我会为你生成全面的测试用例。",
        }
        
        response_content = "这是一个模拟的AI回复。请在.env文件中配置DEEPSEEK_API_KEY以启用真实的AI对话功能。\n\n"
        
        if knowledge_context:
            response_content += f"【基于知识库】我参考了知识库信息，相关内容如下：\n{knowledge_context[:500]}\n\n"
        
        for keyword, mock_response in mock_responses.items():
            if keyword in last_message:
                response_content += mock_response
                break
        else:
            response_content += f"你说了：{last_message}\n\n这是一个关于'{last_message[:50]}'的模拟回复。"
        
        return {
            "content": response_content,
            "tokens_used": 100,
            "knowledge_references": [],
            "response_time": 1.0,
            "model": "mock-model",
            "is_mock": True
        }