import time
import hmac
import hashlib
import base64
import requests
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


class DingTalkService:
    """钉钉消息推送服务"""
    
    def __init__(self, webhook: str, secret: str = None):
        self.webhook = webhook
        self.secret = secret
    
    def send_review_notification(
        self,
        review_data: Dict,
        at_users: List[str] = None
    ) -> bool:
        """
        发送代码评审通知
        
        Args:
            review_data: 评审数据
            at_users: @用户列表
            
        Returns:
            bool: 是否发送成功
        """
        # 构建消息内容
        content = self._build_review_content(review_data)
        
        # 直接发送，不拆分
        return self._send_markdown_message("AI代码评审报告", content, at_users)
    
    def _build_review_content(self, review_data: Dict) -> str:
        """构建评审消息内容（Markdown格式）"""
        risk_emoji = {
            'HIGH': '🔴',
            'MEDIUM': '🟠',
            'LOW': '🟢'
        }
        
        emoji = risk_emoji.get(review_data.get('risk_level'), '🟢')
        
        # 提取关键信息
        repository_name = review_data.get('repository_name', '')
        branch = review_data.get('branch', '')
        commit_hash = review_data.get('commit_hash', '')[:8]
        author = review_data.get('author', '')
        risk_level = review_data.get('risk_level', '')
        risk_score = review_data.get('risk_score', 0) * 100
        commit_message = review_data.get('commit_message', '')
        changed_files = review_data.get('changed_files', [])
        ai_summary = review_data.get('ai_summary', '暂无详细评审内容')
        
        # 构建基础信息部分
        content = f"""## AI代码评审报告 {emoji}

**仓库**: {repository_name}
**分支**: {branch}
**提交**: `{commit_hash}`
**作者**: {author}
**风险等级**: {risk_level} ({risk_score:.0f}%)

---

### 📝 提交信息
> {commit_message}

### 📁 变更文件 ({len(changed_files)}个)
"""
        
        # 添加变更文件列表（最多显示5个）
        for i, f in enumerate(changed_files):
            if i >= 5:
                content += f"... 等共 {len(changed_files)} 个文件\n"
                break
            emoji_map = {'A': '➕', 'M': '📝', 'D': '❌', 'R': '🔄'}
            file_emoji = emoji_map.get(f.get('status', ''), '📄')
            critical = ' ⚠️' if f.get('is_critical') else ''
            content += f"- {file_emoji} `{f['path']}`{critical}\n"
        
        content += "\n### 🔍 AI评审结论\n\n"
        
        # 精简AI评审结果，提取关键信息
        # 假设 ai_summary 是 Markdown 格式，我们尝试提取 Summary 部分
        # 如果 ai_summary 包含 "## 总结" 或 "**总结**" 等标记，提取其后内容
        
        # 简单处理：如果 ai_summary 很长，截取前500字符，并保留格式
        if len(ai_summary) > 500:
            summary_preview = ai_summary[:500] + "..."
        else:
            summary_preview = ai_summary
            
        content += summary_preview
        
        # 添加查看全部评审的链接
        # 优先使用 review_id 生成链接
        if review_data.get('review_id'):
            review_url = f"http://192.168.3.215:8000/code-review/reviews/{review_data.get('review_id')}/"
        else:
            review_url = f"http://192.168.3.215:8000/code-review/reviews/?repository={repository_name}&commit={commit_hash}"
            
        content += f"\n\n👉 [**查看完整评审报告**]({review_url})\n\n"
        
        content += "---\n*来自 熵减X-AI 智能研发平台*"
        
        return content
    
    def _simplify_ai_summary(self, ai_summary: str) -> str:
        """
        精简AI评审结果，只保留关键信息和严重问题
        
        Args:
            ai_summary: 原始AI评审结果
            
        Returns:
            str: 精简后的评审结果
        """
        if not ai_summary or len(ai_summary) < 100:
            return ai_summary
        
        # 提取关键信息
        lines = ai_summary.split('\n')
        simplified_lines = []
        critical_issues = []
        has_critical = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 识别严重问题关键词
            critical_keywords = ['🔴', '🔴严重', '🔴高风险', '⚠️', '⚠️警告', '必须修复', '修复', '问题', '错误']
            if any(keyword in line for keyword in critical_keywords):
                critical_issues.append(line)
                has_critical = True
            
            # 保留总体评价和关键点
            elif any(keyword in line for keyword in ['【总体评价】', '【建议】', '【风险】', '【影响】']):
                simplified_lines.append(line)
        
        # 构建精简内容
        result = ""
        
        # 添加总体评价
        for line in lines:
            if '【总体评价】' in line:
                result += f"{line}\n\n"
                break
        
        # 添加严重问题
        if critical_issues:
            result += "**🔴 严重问题**\n\n"
            for issue in critical_issues[:3]:  # 最多显示3个严重问题
                result += f"- {issue}\n"
            result += "\n"
        
        # 添加关键建议
        for line in lines:
            if '【建议】' in line:
                result += f"{line}\n\n"
                break
        
        # 添加风险提示
        for line in lines:
            if '【风险】' in line:
                result += f"{line}\n\n"
                break
        
        # 如果没有识别到关键信息，返回前200字
        if not result.strip() or len(result) < 50:
            result = ai_summary[:200] + "..." if len(ai_summary) > 200 else ai_summary
        
        # 添加警告提示
        if has_critical:
            result += "\n⚠️ **请优先处理上述严重问题！**\n\n"
        
        return result
    
    def _send_markdown_message(
        self,
        title: str,
        content: str,
        at_mobiles: List[str] = None
    ) -> bool:
        """
        发送 Markdown 消息（一次性发送，不拆分）
        
        Args:
            title: 消息标题
            content: 消息内容（Markdown格式）
            at_mobiles: @用户手机号列表
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 如果配置了加签密钥，需要签名
            if self.secret:
                timestamp, sign = self._sign()
                url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.webhook
            
            # 电脑端钉钉 Markdown 最佳实践：一级标题前不加空格，段落间空一行，代码块用 ``` 包裹
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": content
                },
                "at": {
                    "atMobiles": at_mobiles or [],
                    "isAtAll": False
                }
            }
            
            logger.info(f"发送钉钉消息到: {self.webhook[:50]}...")
            logger.info(f"消息内容长度: {len(content.encode('utf-8'))} 字节")
            
            response = requests.post(
                url,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode', -1) == 0:
                logger.info("钉钉消息发送成功")
                return True
            else:
                logger.error(f"钉钉消息发送失败: {result.get('errmsg')}")
                return False
            
        except Exception as e:
            logger.error(f"钉钉消息发送异常: {str(e)}")
            return False
    
    def _sign(self) -> Tuple[str, str]:
        """生成签名"""
        timestamp = str(int(time.time() * 1000))
        
        string_to_sign = f"{timestamp}\n{self.secret}"
        
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        sign = base64.b64encode(hmac_code).decode()
        
        return timestamp, sign