import json
import re
from typing import Dict, List, Optional
from django.conf import settings


class AIReviewEngine:
    """AI评审引擎"""
    
    def __init__(self, api_key: str = None, model: str = 'deepseek-coder'):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model
        self.api_base = settings.DEEPSEEK_API_BASE
    
    def review(
        self,
        diff_content: str,
        files: List[Dict],
        commit_message: str,
        commit_hash: str = None
    ) -> Dict:
        """
        执行AI代码评审
        
        Args:
            diff_content: Git Diff内容
            files: 文件变更列表
            commit_message: 提交信息
            commit_hash: 提交Hash
            
        Returns:
            Dict: 评审结果
        """
        # 1. 构建Prompt
        prompt = self._build_prompt(diff_content, files, commit_message)
        
        # 2. 调用AI模型
        response = self._call_ai(prompt)
        
        # 3. 解析结果
        result = self._parse_response(response)
        
        # 4. 风险分类
        from .risk_classifier import RiskClassifier
        risk_classifier = RiskClassifier()
        result['risk_score'] = risk_classifier.classify(
            result.get('issues', []),
            files
        )
        result['risk_level'] = self._get_risk_level(result['risk_score'])
        
        return result
    
    def _build_prompt(
        self,
        diff_content: str,
        files: List[Dict],
        commit_message: str
    ) -> str:
        """构建评审Prompt"""
        prompt = f"""
你是一位资深代码评审专家，请对以下代码变更进行评审。

## 提交信息
**Message**: {commit_message}

## 变更文件 ({len(files)}个)
"""
        for f in files:
            prompt += f"- [{f['status']}] {f['path']}"
            if f.get('is_critical'):
                prompt += " [关键文件]"
            prompt += "\n"

        # 限制diff长度
        max_diff_length = 15000
        diff_preview = diff_content[:max_diff_length] if len(diff_content) > max_diff_length else diff_content

        prompt += f"""
## 代码变更 (Diff)
```
{diff_preview}
```

## 评审要求

请从以下几个维度进行分析：

### 1. 安全风险 (Security)
- SQL注入、XSS、CSRF
- 认证授权问题
- 敏感信息处理
- 加密解密逻辑

### 2. 性能问题 (Performance)
- 循环效率
- 数据库查询优化
- 内存使用
- 缓存策略

### 3. 可靠性 (Reliability)
- 空指针处理
- 异常处理完整性
- 事务一致性
- 幂等性保证

### 4. 可维护性 (Maintainability)
- 代码重复
- 硬编码
- 代码复杂度
- 命名规范

## 输出格式

你是一位15年支付结算专家，请用中文输出评审结果，严格按照以下格式：

【总体评价】
(对本次代码变更的整体评价，包括代码质量、业务逻辑、架构设计等方面)

【关键风险】
(列出本次代码变更中发现的关键风险点，包括但不限于：
- 资金安全风险
- 数据一致性风险
- 并发控制风险
- 业务逻辑漏洞
- 性能瓶颈
- 安全漏洞)

【优化建议】
(针对发现的问题提供具体的优化建议，包括代码改进、架构优化、流程改进等)

【总结】是否建议合并
(给出明确的建议：建议合并/建议修改后合并/不建议合并，并说明理由)
"""
        return prompt
    
    def _call_ai(self, prompt: str) -> str:
        """调用AI模型"""
        import requests
        import logging
        logger = logging.getLogger(__name__)
        
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
            
            logger.info(f"正在调用DeepSeek API: {api_url}, 模型: {model}")
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "你是一位专业的代码评审专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "stream": False
                },
                timeout=60,
                verify=False
            )
            
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            logger.info(f"DeepSeek API调用成功，返回内容长度: {len(content)}")
            return content
        except requests.exceptions.RequestException as e:
            error_msg = f"调用DeepSeek API失败: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "summary": error_msg,
                "issues": [],
                "praise": [],
                "ai_content": error_msg
            }, ensure_ascii=False)
        except Exception as e:
            error_msg = f"解析DeepSeek API响应失败: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "summary": error_msg,
                "issues": [],
                "praise": [],
                "ai_content": error_msg
            }, ensure_ascii=False)
    
    def _mock_response(self, prompt: str) -> str:
        """返回模拟响应（用于开发和测试）"""
        return json.dumps({
            "summary": "代码整体质量良好，建议关注异常处理逻辑",
            "issues": [
                {
                    "type": "reliability",
                    "severity": "medium",
                    "file": "example.java",
                    "line": 45,
                    "description": "建议增加空值检查",
                    "suggestion": "添加 if (obj == null) return;",
                    "code_snippet": "obj.doSomething();"
                }
            ],
            "praise": [
                "代码结构清晰",
                "命名规范良好"
            ]
        }, ensure_ascii=False)
    
    def _parse_response(self, response: str) -> Dict:
        """解析AI响应"""
        # 提取JSON内容
        json_match = re.search(r'```json\n(.+?)\n```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            result = json.loads(json_str)
        else:
            # 尝试直接解析
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # 如果无法解析为JSON，将文本响应转换为结构化数据
                result = {
                    'summary': 'AI评审已完成',
                    'issues': [],
                    'praise': [],
                    'ai_content': response
                }
        
        # 确保字段完整
        result.setdefault('summary', 'AI评审已完成')
        result.setdefault('issues', [])
        result.setdefault('praise', [])
        result.setdefault('ai_content', response)
        
        return result
    
    def _get_risk_level(self, score: float) -> str:
        """根据风险评分获取风险等级"""
        if score >= 0.7:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
