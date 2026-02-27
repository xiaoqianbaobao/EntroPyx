"""
Code Review Service
统一封装代码评审的业务逻辑，供 Agent 和 Task 调用
"""
import logging
import requests
from apps.repository.models import Repository
from apps.repository.services.git_service import GitService
from apps.ai_chat.services import AIChatService

logger = logging.getLogger(__name__)

class CodeReviewService:
    """
    代码评审服务
    """
    
    def pull_repo(self, repo_id: int) -> bool:
        """
        拉取仓库代码
        :param repo_id: 仓库ID
        :return: 是否成功
        """
        try:
            repo = Repository.objects.get(id=repo_id)
            logger.info(f"Start pulling repo: {repo.name}")
            
            # 使用 GitService 拉取/更新仓库
            git_service = GitService(repo)
            git_service.ensure_repo()
            return True
        except Exception as e:
            logger.error(f"Failed to pull repo {repo_id}: {e}")
            raise e

    def get_diff(self, repo_id: int, source: str, target: str = 'master', scope_type: str = 'head', scope_value: str = None) -> str:
        """
        获取代码变更
        :param repo_id: 仓库ID
        :param source: 源分支/Commit/HEAD
        :param target: 目标分支
        :param scope_type: 范围类型 (head, author, count, since, hash)
        :param scope_value: 范围值
        :return: Diff 内容
        """
        try:
            repo = Repository.objects.get(id=repo_id)
            logger.info(f"Getting diff for {repo.name}: {source} -> {target}, scope={scope_type}:{scope_value}")
            
            git_service = GitService(repo)
            
            # 分支对比模式（保持原样）
            # 简单的启发式判断：如果 source 看起来像 hash (40位hex或短hash) 且不包含 '/'，则视为 commit
            # 否则视为分支名
            is_branch_mode = '/' in source or (len(source) < 7 and source != 'HEAD') or (scope_type == 'head' and source != 'HEAD' and not source.isdigit())
            
            # 特殊处理：如果明确指定了范围类型，则不是普通分支对比
            if scope_type != 'head' and scope_type != 'hash':
                 is_branch_mode = False

            if is_branch_mode:
                # 获取分支 Diff
                repo_path = repo.local_path
                import git
                r = git.Repo(repo_path)
                
                # 确保远程分支已更新
                # origin = r.remotes.origin
                
                # 构建引用名称
                source_ref = source if source.startswith('origin/') else f'origin/{source}'
                target_ref = target if target.startswith('origin/') else f'origin/{target}'
                
                return r.git.diff(f'{target_ref}...{source_ref}')
            
            # Commit 模式下的不同策略
            repo_path = repo.local_path
            import git
            r = git.Repo(repo_path)
            
            commits = []
            
            if scope_type == 'author':
                # 获取指定作者的最近提交
                # git log --author="name" -n 5
                commits = list(r.iter_commits('HEAD', author=scope_value, max_count=5))
                if not commits:
                    return f"No commits found for author: {scope_value}"
                # 评审这些提交的变更
                # 简单起见，取最近一次提交的 Diff，或者聚合所有 Diff
                # 这里聚合最近5次
                diffs = []
                for commit in commits:
                    diffs.append(r.git.show(commit.hexsha))
                return "\n\n".join(diffs)
                
            elif scope_type == 'count':
                # 获取最近 N 个提交
                count = int(scope_value) if scope_value.isdigit() else 1
                commits = list(r.iter_commits('HEAD', max_count=count))
                diffs = []
                for commit in commits:
                    diffs.append(r.git.show(commit.hexsha))
                return "\n\n".join(diffs)
                
            elif scope_type == 'since':
                # 获取指定时间之后的提交
                # git log --since="1 day ago"
                commits = list(r.iter_commits('HEAD', since=scope_value))
                if not commits:
                    return f"No commits found since: {scope_value}"
                diffs = []
                for commit in commits:
                    diffs.append(r.git.show(commit.hexsha))
                return "\n\n".join(diffs)
                
            elif scope_type == 'hash':
                # 指定 Hash
                return r.git.show(source)
                
            else:
                # 默认 HEAD (最近一次提交)
                return r.git.show('HEAD')
            
        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            raise e
            
    def review_code(self, diff_content: str) -> str:
        """
        评审代码（同步调用）
        :param diff_content: Diff 内容
        :return: 评审结果
        """
        try:
            # 如果 diff 内容太长，截断（避免超出 Token 限制）
            max_len = 10000
            if len(diff_content) > max_len:
                diff_content = diff_content[:max_len] + "\n... (Diff truncated due to length)"
                
            ai_service = AIChatService()
            prompt = f"""请作为一位资深技术专家，对以下代码变更进行代码评审。
关注点：
1. 潜在的 Bug 和逻辑错误
2. 安全漏洞
3. 代码风格和可维护性
4. 性能问题

代码变更 (Diff):
```diff
{diff_content}
```

请输出 Markdown 格式的评审报告。
"""
            response = ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                conversation_type='code_review'
            )
            return response['content']
            
        except Exception as e:
            logger.error(f"Failed to review code: {e}")
            return f"评审过程中发生错误: {str(e)}"

    def send_dingtalk_notification(self, repo_id: int, content: str) -> bool:
        """
        发送钉钉通知
        :param repo_id: 仓库ID
        :param content: 消息内容
        :return: 是否成功
        """
        try:
            repo = Repository.objects.get(id=repo_id)
            if not repo.dingtalk_webhook:
                logger.warning(f"Repo {repo.name} has no DingTalk webhook configured.")
                return False
                
            # 构造钉钉消息
            # 截取摘要，避免消息过长
            summary = content[:500] + "..." if len(content) > 500 else content
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"[{repo.name}] 代码评审报告",
                    "text": f"### 🤖 代码评审报告\n\n**仓库**: {repo.name}\n\n{summary}\n\n[查看详情](http://localhost:8000/ai-chat/)" # TODO: 替换为真实域名
                }
            }
            
            response = requests.post(repo.dingtalk_webhook, json=payload, timeout=10)
            response.raise_for_status()
            
            # 检查钉钉返回的 errcode
            res_json = response.json()
            if res_json.get('errcode') != 0:
                logger.error(f"DingTalk API error: {res_json}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to send DingTalk notification: {e}")
            return False