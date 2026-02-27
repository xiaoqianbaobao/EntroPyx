"""AI服务模块 - 集成DeepSeek API进行PRD评审"""
import json
import requests
from typing import Dict, List
from django.conf import settings


class PRDAnalyzer:
    """PRD文档分析器"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model or settings.DEEPSEEK_MODEL
        self.api_base = settings.DEEPSEEK_API_BASE
    
    def analyze(self, content: str) -> Dict:
        """
        分析PRD文档
        
        Args:
            content: PRD文档内容
            
        Returns:
            Dict: 分析结果
        """
        prompt = self._build_prompt(content)
        response = self._call_ai(prompt)
        return self._parse_response(response)
    
    def analyze_file(self, file_path: str, file_type: str) -> Dict:
        """
        分析PRD文件
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            Dict: 分析结果
        """
        content = self._read_file(file_path, file_type)
        return self.analyze(content)
    
    def _read_file(self, file_path: str, file_type: str) -> str:
        """读取文件内容"""
        if file_type == 'pdf':
            return self._read_pdf(file_path)
        elif file_type == 'word':
            return self._read_word(file_path)
        elif file_type == 'md':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    def _read_pdf(self, file_path: str) -> str:
        """读取PDF文件"""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            return "PDF解析库未安装，无法读取PDF文件。"
        except Exception as e:
            return f"PDF解析失败: {str(e)}"
    
    def _read_word(self, file_path: str) -> str:
        """读取Word文件"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except ImportError:
            return "Word解析库未安装，无法读取Word文件。"
        except Exception as e:
            return f"Word解析失败: {str(e)}"
    
    def _build_prompt(self, content: str) -> str:
        """构建分析Prompt"""
        return f"""请评审以下PRD文档，输出JSON格式结果：

PRD内容：
{content[:5000]}

输出格式要求：
{{
    "completeness_score": 0.0-1.0,
    "consistency_score": 0.0-1.0,
    "risk_score": 0.0-1.0,
    "overall_score": 0.0-1.0,
    "background": "需求背景摘要（50字内）",
    "user_stories": [{{"story": "用户故事", "acceptance": ["验收标准"]}}],
    "requirements": [{{"id": "REQ001", "description": "需求描述", "priority": "P0"}}],
    "issues": [{{"type": "completeness|consistency|risk", "severity": "high|medium|low", "description": "问题", "suggestion": "建议"}}],
    "suggestions": "整体建议（100字内）"
}}"""
    
    def _call_ai(self, prompt: str) -> str:
        """调用AI API"""
        try:
            # 优先从数据库获取配置
            from apps.platform_management.models import LLMConfig
            llm_config = LLMConfig.objects.filter(is_active=True).first()
            
            if llm_config:
                api_url = llm_config.api_base.rstrip('/') + '/chat/completions'
                api_key = llm_config.api_key
                model = llm_config.model_name
            else:
                # 回退到硬编码配置
                api_url = "https://ocrserver.bestpay.com.cn/new/kjqxggpiunyitolh-serving/v1/chat/completions"
                api_key = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkRIRmJwb0lVcXJZOHQyenBBMnFYZkNtcjVWTzVaRXI0UnpIVV8tZW52dlEiLCJ0eXAiOiJKV1QifQ.eyJleHAiOjIwNzA4NTkyMDEsImlhdCI6MTc1NTQ5OTIwMSwiaXNzIjoia2pxeGdncGl1bnlpdG9saC1zZXJ2aW5nIiwic3ViIjoia2pxeGdncGl1bnlpdG9saC1zZXJ2aW5nIn0.es1OGw3drT0cTwtld1tNtXuCofejuQUDhswG_qvbjQHyBqGcLd5xSZD08U9586xDiYN2crLuT2OB3UT0j1wvIEGYZxL4R8mnbGL7MSBJCiEepP-AxOi4wmMSnkxW5lozKpmuFM-Oe3CcuTb6ZkM-J7INHPdcWsZb7DrGfkBA9-aVSvmxheIvFpkV4pi89BdblPtWQX-B4ZvlHCnQbbIoF-w90iCxyZq7cc4BLadHks-VutQvVbOjqz5Jnvc03QPeCz_zH4LMG-hvQUpe6hCOZVyRcfAQMJg51V5iqnPh-X2eOEQMPy6zj62Nq8nppOtPRHgJm9pz3Pxdm_Z4tJnvrw"
                model = "deepseek-ai/DeepSeek-V2.5"
            
            import requests
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "你是一位资深产品经理和业务分析师。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "stream": False 
                },
                timeout=180,
                verify=False
            )
            response.raise_for_status()
            
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            import logging
            logging.error(f'AI API调用失败: {str(e)}')
            return f"Error: {str(e)}"
    
    def _mock_response(self) -> str:
        """返回模拟响应"""
        return json.dumps({
            "completeness_score": 0.75,
            "consistency_score": 0.80,
            "risk_score": 0.65,
            "overall_score": 0.73,
            "background": "这是一个支付系统优化项目，旨在提升支付成功率和用户体验。",
            "user_stories": [
                {"story": "作为用户，我希望快速完成支付", "acceptance": ["支付流程不超过3步", "支付成功率>99%"]}
            ],
            "requirements": [
                {"id": "REQ001", "description": "支持多种支付方式", "priority": "P0"},
                {"id": "REQ002", "description": "支付状态实时同步", "priority": "P1"}
            ],
            "issues": [
                {
                    "type": "completeness",
                    "severity": "medium",
                    "description": "缺少异常场景的详细处理流程",
                    "suggestion": "补充网络超时、银行回调异常等场景的处理逻辑"
                }
            ],
            "suggestions": "整体结构清晰，建议补充更多异常场景的处理逻辑。"
        }, ensure_ascii=False)
    
    def _parse_response(self, response: str) -> Dict:
        """解析AI响应"""
        import re
        
        # 提取JSON
        json_match = None
        if '```json' in response:
            json_match = re.search(r'```json\n(.+?)\n```', response, re.DOTALL)
        elif '{' in response:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                # 创建简单的模拟Match对象
                class MockMatch:
                    def __init__(self, value):
                        self._value = value
                    def group(self, n):
                        return self._value
                json_match = MockMatch(json_str)
        
        if json_match:
            try:
                result = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                result = self._default_result()
        else:
            result = self._default_result()
        
        # 确保字段完整
        for key in ['completeness_score', 'consistency_score', 'risk_score', 'overall_score']:
            result.setdefault(key, 0.5)
        result.setdefault('issues', [])
        result.setdefault('user_stories', [])
        result.setdefault('requirements', [])
        
        return result
    
    def _default_result(self) -> Dict:
        """默认结果"""
        return {
            'completeness_score': 0.5,
            'consistency_score': 0.5,
            'risk_score': 0.5,
            'overall_score': 0.5,
            'background': '',
            'user_stories': [],
            'requirements': [],
            'issues': [{'type': 'completeness', 'severity': 'medium', 'description': '无法解析PRD内容', 'suggestion': '请检查文档格式'}],
            'suggestions': ''
        }