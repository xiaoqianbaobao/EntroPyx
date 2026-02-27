"""
NLP服务
Natural Language Processing Service

注意: 这是一个简化版本，实际使用可以集成LLM或更复杂的NLP方法
"""
import json
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class NLPService:
    """NLP处理服务基类"""
    
    def __init__(self):
        self.name = "Base NLP Service"
    
    def generate_meeting_summary(self, full_text: str, transcripts, recording) -> Dict:
        """
        生成会议纪要
        
        Args:
            full_text: 完整的会议文本
            transcripts: 转写片段列表
            recording: 录音对象
        
        Returns:
            Dict: 纪要数据
        """
        raise NotImplementedError("Subclass must implement this method")
    
    def extract_key_points(self, text: str) -> List[str]:
        """提取关键要点"""
        raise NotImplementedError("Subclass must implement this method")
    
    def extract_decisions(self, text: str) -> List[str]:
        """提取决策事项"""
        raise NotImplementedError("Subclass must implement this method")
    
    def extract_action_items(self, text: str) -> List[Dict]:
        """提取待办任务"""
        raise NotImplementedError("Subclass must implement this method")
    
    def classify_opinions(self, text: str) -> List[Dict]:
        """分类评审意见"""
        raise NotImplementedError("Subclass must implement this method")


class RuleBasedNLPService(NLPService):
    """基于规则的NLP服务"""
    
    def __init__(self):
        super().__init__()
        self.name = "Rule-based NLP Service"
    
    def generate_meeting_summary(self, full_text: str, transcripts, recording) -> Dict:
        """使用规则生成会议纪要"""
        try:
            import jieba.analyse
        except ImportError:
            logger.warning("jieba not installed, using simple extraction")
            jieba = None
        
        # 提取关键词
        key_points = self.extract_key_points(full_text) if jieba else []
        
        # 提取决策和待办
        decisions = self.extract_decisions(full_text)
        action_items = self.extract_action_items(full_text)
        
        # 分类意见
        opinions = self.classify_opinions(full_text)
        
        return {
            'title': f"{recording.meeting_title} - 会议纪要",
            'summary': f"本次会议于{recording.meeting_date.strftime('%Y-%m-%d %H:%M')}举行，主要讨论了代码评审相关事项。",
            'key_points': key_points,
            'decisions': decisions,
            'action_items': action_items,
            'opinions': opinions
        }
    
    def extract_key_points(self, text: str) -> List[str]:
        """使用jieba提取关键词"""
        try:
            import jieba.analyse
            keywords = jieba.analyse.extract_tags(text, topK=10)
            return keywords
        except ImportError:
            # 简单的关键词提取
            words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
            from collections import Counter
            counter = Counter(words)
            return [word for word, count in counter.most_common(10)]
    
    def extract_decisions(self, text: str) -> List[str]:
        """使用正则表达式提取决策事项"""
        decision_patterns = [
            r'决定[：:](.*?)([。\n])',
            r'确定[：:](.*?)([。\n])',
            r'通过[：:](.*?)([。\n])',
            r'同意[：:](.*?)([。\n])',
        ]
        
        decisions = []
        for pattern in decision_patterns:
            matches = re.findall(pattern, text)
            decisions.extend([m[0].strip() for m in matches])
        
        return decisions[:10]
    
    def extract_action_items(self, text: str) -> List[Dict]:
        """使用正则表达式提取待办任务"""
        action_patterns = [
            r'(需要|要|请)(.*?)(完成|处理|跟进|修改|优化)(.*?)([。\n])',
        ]
        
        action_items = []
        for pattern in action_patterns:
            matches = re.findall(pattern, text)
            for match in matches[:5]:
                task = ''.join(match)
                action_items.append({
                    'task': task,
                    'assignee': '',
                    'deadline': ''
                })
        
        return action_items
    
    def classify_opinions(self, text: str) -> List[Dict]:
        """使用规则分类评审意见"""
        opinions = []
        
        # 按句子分割
        sentences = re.split(r'[。\n]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_lower = sentence.lower()
            
            # 分类逻辑
            if any(word in sentence_lower for word in ['改进', '优化', '建议', '可以']):
                opinions.append({
                    'type': 'suggestion',
                    'content': sentence,
                    'priority': 'medium'
                })
            elif any(word in sentence_lower for word in ['问题', '错误', 'bug', '异常']):
                opinions.append({
                    'type': 'issue',
                    'content': sentence,
                    'priority': 'high'
                })
            elif any(word in sentence_lower for word in ['同意', '通过', '决定']):
                opinions.append({
                    'type': 'decision',
                    'content': sentence,
                    'priority': 'low'
                })
            elif any(word in sentence_lower for word in ['风险', '隐患', '警告']):
                opinions.append({
                    'type': 'risk',
                    'content': sentence,
                    'priority': 'high'
                })
        
        return opinions[:10]


class LLMNLPService(NLPService):
    """
    基于LLM的NLP服务
    需要集成Ollama或其他LLM服务
    """
    
    def __init__(self, model_name='qwen2.5:7b'):
        super().__init__()
        self.name = "LLM-based NLP Service"
        self.model_name = model_name
        self.client = None
    
    def _load_client(self):
        """加载LLM客户端"""
        if self.client is not None:
            return
        
        try:
            from ollama import Client
            self.client = Client(host='http://localhost:11434')
            logger.info("Ollama client loaded successfully")
        except ImportError:
            logger.warning("Ollama not installed")
            raise ImportError("Please install ollama: pip install ollama")
        except Exception as e:
            logger.error(f"Failed to load Ollama client: {str(e)}")
            raise
    
    def generate_meeting_summary(self, full_text: str, transcripts, recording) -> Dict:
        """使用LLM生成会议纪要"""
        try:
            self._load_client()
            
            # 构建prompt
            prompt = f"""
请根据以下会议转写内容，生成结构化的会议纪要。

会议信息:
- 标题: {recording.meeting_title}
- 时间: {recording.meeting_date}
- 参会人员: {recording.participants}

会议内容:
{full_text[:4000]}

请以JSON格式输出，包含以下字段:
{{
    "title": "会议标题",
    "summary": "会议摘要(3-5句话)",
    "key_points": ["要点1", "要点2", ...],
    "decisions": ["决策1", "决策2", ...],
    "action_items": [
        {{"task": "任务描述", "assignee": "负责人", "deadline": "截止日期"}},
        ...
    ],
    "opinions": [
        {{"type": "issue|suggestion|decision|risk|positive", "content": "意见内容", "priority": "high|medium|low"}},
        ...
    ]
}}
"""
            
            response = self.client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            
            try:
                result = json.loads(response['message']['content'])
                return result
            except json.JSONDecodeError:
                logger.warning("LLM output is not valid JSON, falling back to rule-based")
                return self._fallback_to_rules(full_text, transcripts, recording)
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {str(e)}")
            return self._fallback_to_rules(full_text, transcripts, recording)
    
    def _fallback_to_rules(self, full_text: str, transcripts, recording):
        """降级到规则方法"""
        rule_service = RuleBasedNLPService()
        return rule_service.generate_meeting_summary(full_text, transcripts, recording)


def get_nlp_service(service_type='rule', **kwargs):
    """
    获取NLP服务实例
    
    Args:
        service_type: 服务类型 ('rule', 'llm')
        **kwargs: 其他参数
    
    Returns:
        NLPService实例
    """
    if service_type == 'llm':
        try:
            return LLMNLPService(**kwargs)
        except:
            logger.warning("LLM service not available, falling back to rule-based")
            return RuleBasedNLPService()
    else:
        return RuleBasedNLPService()
