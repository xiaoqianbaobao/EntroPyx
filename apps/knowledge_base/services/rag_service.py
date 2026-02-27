"""
RAG服务 - 检索增强生成
支持向量检索和AI生成
"""
import json
import re
from typing import List, Dict, Optional
from django.conf import settings
import requests


class RAGService:
    """RAG检索增强生成服务"""
    
    def __init__(self, api_key: str = None, model: str = 'deepseek-chat'):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model
        self.api_base = settings.DEEPSEEK_API_BASE
    
    def embed_text(self, text: str) -> List[float]:
        """
        将文本转换为向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            向量表示
        """
        # 这里简化处理，实际应该使用专门的embedding模型
        # 可以使用OpenAI的embedding API或其他向量模型
        # 这里使用简单的文本特征作为示例
        
        # 简单的字符级特征向量（仅用于演示）
        # 实际生产环境应使用专业的embedding模型
        text_lower = text.lower()
        features = []
        
        # 基于字符频率的特征
        for char in 'abcdefghijklmnopqrstuvwxyz0123456789':
            features.append(text_lower.count(char) / (len(text) + 1))
        
        # 基于词长度的特征
        words = text.split()
        features.append(len(words) / (len(text) + 1))
        features.append(sum(len(w) for w in words) / (len(words) + 1) if words else 0)
        
        # 填充到固定长度
        while len(features) < 384:  # 常见的向量维度
            features.append(0.0)
        
        return features[:384]
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数 (0-1)
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def retrieve_relevant_docs(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        检索相关文档块
        
        Args:
            query: 查询文本
            chunks: 文档块列表 [{'content': str, 'embedding': list, 'metadata': dict}]
            top_k: 返回前k个最相关的文档块
            
        Returns:
            相关文档块列表
        """
        if not chunks:
            return []
        
        # 将查询转换为向量
        query_embedding = self.embed_text(query)
        
        # 计算相似度
        scored_chunks = []
        for chunk in chunks:
            chunk_embedding = chunk.get('embedding', [])
            if chunk_embedding:
                score = self.similarity(query_embedding, chunk_embedding)
                scored_chunks.append({
                    'chunk': chunk,
                    'score': score
                })
        
        # 按相似度排序
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回top_k个
        return [item['chunk'] for item in scored_chunks[:top_k]]
    
    def generate_response(
        self,
        query: str,
        context_docs: List[Dict],
        conversation_history: List[Dict] = None
    ) -> str:
        """
        生成AI响应
        
        Args:
            query: 用户查询
            context_docs: 检索到的相关文档
            conversation_history: 对话历史
            
        Returns:
            AI响应
        """
        # 构建上下文
        context = "\n\n".join([
            f"文档片段{i+1}:\n{doc['content']}"
            for i, doc in enumerate(context_docs)
        ])
        
        # 构建对话历史
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-5:]:  # 只使用最近5条消息
                role = "用户" if msg['role'] == 'user' else "AI助手"
                history_text += f"{role}: {msg['content']}\n"
        
        # 构建prompt - 简化版本，让用户自己控制对话内容
        prompt = f"""## 参考文档
{context}

## 对话历史
{history_text}

## 用户输入
{query}

请基于以上信息回答用户的问题。"""
        
        # 调用AI模型
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一位专业的代码评审专家和产品经理。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            # 返回基于上下文的简单回答
            if context_docs:
                return f"基于文档内容，我找到以下相关信息：\n\n{context_docs[0]['content'][:500]}..."
            else:
                return "抱歉，我没有找到相关的文档信息来回答您的问题。"
    
    def stream_generate_response(
        self,
        query: str,
        context_docs: List[Dict],
        conversation_history: List[Dict] = None
    ):
        """
        流式生成AI响应
        
        Args:
            query: 用户查询
            context_docs: 检索到的相关文档
            conversation_history: 对话历史
            
        Yields:
            响应片段
        """
        # 构建上下文
        context = "\n\n".join([
            f"文档片段{i+1}:\n{doc['content']}"
            for i, doc in enumerate(context_docs)
        ])
        
        # 构建对话历史
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-5:]:
                role = "用户" if msg['role'] == 'user' else "AI助手"
                history_text += f"{role}: {msg['content']}\n"
        
        # 构建prompt - 简化版本
        prompt = f"""## 参考文档
{context}

## 对话历史
{history_text}

## 用户输入
{query}

请基于以上信息回答用户的问题。"""
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一位专业的代码评审专家和产品经理。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stream": True
                },
                timeout=120,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            json_data = json.loads(data)
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                delta = json_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            # 如果流式失败，返回完整响应
            full_response = self.generate_response(query, context_docs, conversation_history)
            yield full_response
