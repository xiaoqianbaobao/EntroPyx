import os
import git
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from django.conf import settings
import base64
import logging
from urllib.parse import urlparse, quote


class GitService:
    """Git仓库操作服务"""
    
    def __init__(self, repository):
        self.repository = repository
        self.local_path = Path(repository.local_path)
        self.logger = logging.getLogger(__name__)
    
    def _decode_password(self, password_encrypted: str) -> Optional[str]:
        """
        直接返回原始密码，不做任何解码
        
        Args:
            password_encrypted: 原始密码
            
        Returns:
            原始密码
        """
        if not password_encrypted:
            return None
        
        # 直接返回原始密码
        password = password_encrypted.strip()
        
        if password and len(password) > 0:
            self.logger.debug(f"使用原始密码")
            return password
        else:
            self.logger.warning("密码为空")
            return None
    
    def ensure_repo(self) -> bool:
        """
        确保仓库已克隆或更新
        Returns:
            bool: 是否是首次克隆
        """
        if not self.local_path.exists():
            return self._clone()
        else:
            return self._fetch()
    
    def _clone(self) -> bool:
        """克隆仓库"""
        try:
            import os

            # 确保父目录存在
            self.local_path.parent.mkdir(parents=True, exist_ok=True)

            repo_url = self.repository.git_url
            original_url = repo_url  # 保存原始URL

            # 检查是否需要认证
            if self.repository.auth_type == 'password':
                username = self.repository.username
                password_encrypted = self.repository.password_encrypted

                # 只有当有有效密码时才添加认证信息
                if username and password_encrypted:
                    # 解密密码
                    password = self._decode_password(password_encrypted)

                    if password:
                        # 解析原始URL
                        parsed = urlparse(repo_url)

                        # 构建带认证的URL (仅HTTPS)
                        if parsed.scheme in ('http', 'https'):
                            # 检查URL是否已包含密码
                            if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
                                # URL已包含用户名和密码,不需要再次添加
                                self.logger.info(f"URL已包含认证信息,跳过添加: {original_url}")
                                repo_url = original_url
                            elif '@' in parsed.netloc:
                                # URL已包含用户名,只添加密码
                                user_part, host_part = parsed.netloc.split('@', 1)
                                # 使用latin-1编码,因为密码可能包含非UTF-8字符
                                encoded_password = quote(password, safe='', encoding='latin-1')
                                repo_url = f"{parsed.scheme}://{user_part}:{encoded_password}@{host_part}{parsed.path}"
                                self.logger.info(f"使用认证信息克隆仓库(已有用户名): {original_url} -> {parsed.scheme}://{user_part}:*****@{host_part}{parsed.path}")
                            else:
                                # URL不包含用户名,添加用户名和密码
                                encoded_username = quote(username, safe='')
                                # 使用latin-1编码,因为密码可能包含非UTF-8字符
                                encoded_password = quote(password, safe='', encoding='latin-1')
                                repo_url = f"{parsed.scheme}://{encoded_username}:{encoded_password}@{parsed.netloc}{parsed.path}"
                                self.logger.info(f"使用认证信息克隆仓库: {original_url} -> {parsed.scheme}://{encoded_username}:*****@{parsed.netloc}{parsed.path}")
                    else:
                        self.logger.warning("密码解密失败或为空，不使用认证")
                else:
                    self.logger.warning("用户名或密码为空，不使用认证")
            else:
                self.logger.info("不使用密码认证")

            # 准备Git环境变量（禁用交互式提示）
            git_env = os.environ.copy()
            git_env['GIT_TERMINAL_PROMPT'] = '0'
            
            self.logger.info(f"开始克隆仓库到: {self.local_path}")
            
            # 执行克隆（禁用交互式提示）
            repo = git.Repo.clone_from(
                repo_url,
                self.local_path,
                branch='master',
                depth=1,  # 浅克隆
                env=git_env  # 传递环境变量
            )
            
            self.logger.info("仓库克隆成功")
            
            # 确保克隆后有正确的 refspec 配置
            with repo.config_writer() as cfg:
                cfg.set_value('remote "origin"', 'fetch', '+refs/heads/*:refs/remotes/origin/*')
            
            return True
        except Exception as e:
            self.logger.error(f"克隆仓库失败: {str(e)}")
            raise GitException(f"克隆仓库失败: {str(e)}")
    
    def _fetch(self) -> bool:
        """更新仓库"""
        try:
            repo = git.Repo(str(self.local_path))
            
            # 检查并确保远程 origin 有正确的 refspec 配置
            try:
                origin = repo.remotes.origin
                # 检查是否存在 fetch refspec
                if not origin.exists():
                    raise GitException("远程 origin 不存在")

                # 检查是否有refspec配置
                try:
                    fetch_refspec = origin.config_reader.get('fetch')
                    if not fetch_refspec:
                        raise ValueError("no refspec")
                except (KeyError, ValueError):
                    # 没有refspec,添加默认配置
                    with repo.config_writer() as cfg:
                        cfg.set_value(f'remote "{origin.name}"', 'fetch', '+refs/heads/*:refs/remotes/origin/*')
                    # 重新加载远程配置
                    origin = repo.remotes.origin
            except Exception as config_error:
                raise GitException(f"远程仓库配置错误: {str(config_error)}")
            
            # 准备Git环境变量（禁用交互式提示）
            git_env = {'GIT_TERMINAL_PROMPT': '0'}  # 强制禁用所有终端提示
            
            # 如果需要认证，临时修改远程URL包含凭证
            original_url = origin.url
            if self.repository.auth_type == 'password':
                username = self.repository.username
                password_encrypted = self.repository.password_encrypted

                if username and password_encrypted:
                    # 解密密码
                    password = self._decode_password(password_encrypted)

                    if password:
                        parsed = urlparse(original_url)
                        if parsed.scheme in ('http', 'https'):
                            # 检查URL是否已包含密码
                            if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
                                # URL已包含用户名和密码,不需要再次添加
                                self.logger.info(f"URL已包含认证信息,跳过添加: {original_url}")
                                auth_url = original_url
                            elif '@' in parsed.netloc:
                                # URL已包含用户名,只添加密码
                                user_part, host_part = parsed.netloc.split('@', 1)
                                # 使用latin-1编码,因为密码可能包含非UTF-8字符
                                encoded_password = quote(password, safe='', encoding='latin-1')
                                auth_url = f"{parsed.scheme}://{user_part}:{encoded_password}@{host_part}{parsed.path}"
                                self.logger.info(f"使用认证信息更新仓库(已有用户名): {original_url} -> {parsed.scheme}://{user_part}:*****@{host_part}{parsed.path}")
                            else:
                                # URL不包含用户名,添加用户名和密码
                                encoded_username = quote(username, safe='')
                                # 使用latin-1编码,因为密码可能包含非UTF-8字符
                                encoded_password = quote(password, safe='', encoding='latin-1')
                                auth_url = f"{parsed.scheme}://{encoded_username}:{encoded_password}@{parsed.netloc}{parsed.path}"
                                self.logger.info(f"使用认证信息更新仓库: {original_url} -> {parsed.scheme}://{encoded_username}:*****@{parsed.netloc}{parsed.path}")

                            # 临时设置带凭证的URL
                            with repo.config_writer() as cfg:
                                cfg.set_value(f'remote "{origin.name}"', 'url', auth_url)

                            # 重新加载远程配置
                            origin = repo.remotes.origin
                    else:
                        self.logger.warning("密码解密失败或为空，不使用认证")
                else:
                    self.logger.warning("用户名或密码为空，不使用认证")
            else:
                self.logger.info("不使用密码认证")
            
            self.logger.info(f"开始fetch仓库: {self.local_path}")
            
            try:
                # 执行 fetch（禁用交互式提示）
                with repo.git.custom_environment(**git_env):
                    origin.fetch()
                
                self.logger.info("仓库更新成功")
            finally:
                # 恢复原始URL（移除凭证）
                if origin.url != original_url:
                    try:
                        with repo.config_writer() as cfg:
                            cfg.set_value(f'remote "{origin.name}"', 'url', original_url)
                        self.logger.info("恢复原始URL")
                    except Exception as e:
                        self.logger.warning(f"恢复URL失败: {str(e)}")
                        # 恢复失败不影响主要功能
                        pass
            
            return False  # 不是首次克隆
        except GitException:
            raise
        except Exception as e:
            self.logger.error(f"更新仓库失败: {str(e)}")
            raise GitException(f"更新仓库失败: {str(e)}")
    
    def get_today_commits(self, branch: str = 'master', all_branches: bool = False, days: int = 7) -> List[Dict]:
        """获取指定天数内的提交

        Args:
            branch: 分支名(当all_branches=False时使用)
            all_branches: 是否获取所有分支的提交
            days: 获取多少天内的提交（默认7天）

        Returns:
            提交列表
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            repo = git.Repo(str(self.local_path))
            since_date = timezone.now() - timedelta(days=days)

            # 确定要查询的分支
            if all_branches:
                # 先fetch所有远程分支
                self.logger.info(f"开始fetch所有远程分支（获取最近{days}天的提交）...")
                try:
                    # 使用git命令fetch所有远程分支
                    import os
                    git_env = {'GIT_TERMINAL_PROMPT': '0'}
                    # 先尝试解除浅克隆限制
                    try:
                        repo.git.fetch('--unshallow', env=git_env)
                        self.logger.info("解除浅克隆限制完成")
                    except Exception as unshallow_error:
                        # 可能不是浅克隆,或者已经解除
                        self.logger.debug(f"解除浅克隆限制跳过: {str(unshallow_error)}")

                    # 然后fetch所有分支
                    repo.git.fetch('--all', env=git_env)
                    self.logger.info("fetch所有远程分支完成")
                except Exception as e:
                    self.logger.warning(f"fetch所有远程分支失败: {str(e)}")

                # 获取所有远程分支
                branches = [b.name for b in repo.remotes.origin.fetch()]
                self.logger.info(f"获取所有分支的提交,共 {len(branches)} 个分支")
            else:
                # 只获取指定分支
                branches = [f'origin/{branch}']

            # 收集所有提交(去重)
            seen_commits = set()
            all_commits = []

            for branch_ref in branches:
                try:
                    commits = list(repo.iter_commits(
                        branch_ref,
                        since=since_date.strftime('%Y-%m-%d 00:00:00')
                    ))

                    for c in commits:
                        # 去重,避免同一个提交在多个分支中出现
                        if c.hexsha not in seen_commits:
                            seen_commits.add(c.hexsha)
                            all_commits.append({
                                'hash': c.hexsha,
                                'message': c.message.strip(),
                                'author': c.author.name,
                                'author_email': c.author.email,
                                'committed_datetime': c.committed_datetime,
                                'parents': [p.hexsha for p in c.parents],
                                'branch': branch_ref  # 记录提交所在的分支
                            })
                except Exception as e:
                    self.logger.warning(f"获取分支 {branch_ref} 的提交失败: {str(e)}")
                    continue

            # 按提交时间排序
            all_commits.sort(key=lambda x: x['committed_datetime'], reverse=True)

            self.logger.info(f"获取到 {len(all_commits)} 条提交（最近{days}天）")
            return all_commits
        except Exception as e:
            raise GitException(f"获取提交记录失败: {str(e)}")
    
    def get_diff_and_files(self, commit_hash: str) -> Tuple[str, List[Dict]]:
        """
        获取Diff和文件变更列表
        
        Returns:
            Tuple[diff_content, files_list]
        """
        try:
            repo = git.Repo(str(self.local_path))
            commit = repo.commit(commit_hash)
            
            # 获取Diff
            if commit.parents:
                diffs = commit.parents[0].diff(
                    commit,
                    create_patch=True,
                    unified=5
                )
            else:
                # 首次提交
                diffs = commit.diff(git.NULL_TREE, create_patch=True)
            
            # 解析文件变更
            files = []
            diff_content_parts = []
            
            for d in diffs:
                file_info = {
                    'status': d.change_type,  # A/M/D/R
                    'path': d.b_path or d.a_path,
                    'is_critical': self._is_critical_file(d.b_path or d.a_path),
                    'new_path': d.b_path,
                    'old_path': d.a_path
                }
                files.append(file_info)
                
                # 收集Diff文本
                if d.diff:
                    diff_content_parts.append(
                        d.diff.decode('utf-8', errors='replace')
                    )
            
            diff_content = '\n'.join(diff_content_parts)
            return diff_content, files
            
        except Exception as e:
            raise GitException(f"获取Diff失败: {str(e)}")
    
    def _is_critical_file(self, file_path: str) -> bool:
        """判断是否为关键文件"""
        patterns = self.repository.critical_patterns or []
        for pattern in patterns:
            if self._match_pattern(file_path, pattern.get('pattern', '')):
                return True
        return False
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """简单路径匹配（支持通配符）"""
        from fnmatch import fnmatch
        return fnmatch(path, pattern)
    
    def get_file_content(self, commit_hash: str, file_path: str) -> str:
        """获取文件内容"""
        try:
            repo = git.Repo(str(self.local_path))
            commit = repo.commit(commit_hash)
            blob = commit.tree / file_path
            return blob.data_stream.read().decode('utf-8')
        except Exception as e:
            raise GitException(f"获取文件内容失败: {str(e)}")
    
    def get_all_branches(self) -> List[str]:
        """获取所有远程分支"""
        try:
            import os
            repo = git.Repo(str(self.local_path))
            
            # 准备Git环境变量（禁用交互式提示）
            git_env = {'GIT_TERMINAL_PROMPT': '0'}
            
            # 保存原始URL（用于恢复）
            origin = repo.remotes.origin
            original_url = origin.url
            
            # 如果需要认证，临时修改远程URL包含凭证
            if self.repository.auth_type == 'password':
                username = self.repository.username
                password_encrypted = self.repository.password_encrypted

                if username and password_encrypted:
                    try:
                        password = self._decode_password(password_encrypted)
                        if password and len(password) > 0:
                            parsed = urlparse(original_url)
                            if parsed.scheme in ('http', 'https'):
                                # 检查URL是否已包含密码
                                if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
                                    # URL已包含用户名和密码,不需要再次添加
                                    self.logger.info(f"URL已包含认证信息,跳过添加: {original_url}")
                                    auth_url = original_url
                                elif '@' in parsed.netloc:
                                    # URL已包含用户名,只添加密码
                                    user_part, host_part = parsed.netloc.split('@', 1)
                                    # 使用latin-1编码,因为密码可能包含非UTF-8字符
                                    encoded_password = quote(password, safe='', encoding='latin-1')
                                    auth_url = f"{parsed.scheme}://{user_part}:{encoded_password}@{host_part}{parsed.path}"
                                    self.logger.info(f"使用认证信息获取分支(已有用户名): {original_url} -> {parsed.scheme}://{user_part}:*****@{host_part}{parsed.path}")
                                else:
                                    # URL不包含用户名,添加用户名和密码
                                    encoded_username = quote(username, safe='')
                                    auth_url = f"{parsed.scheme}://{encoded_username}:{encoded_password}@{parsed.netloc}{parsed.path}"
                                    self.logger.info(f"使用认证信息获取分支: {original_url} -> {parsed.scheme}://{encoded_username}:*****@{parsed.netloc}{parsed.path}")

                                # 临时设置带凭证的URL
                                with repo.config_writer() as cfg:
                                    cfg.set_value(f'remote "{origin.name}"', 'url', auth_url)

                                # 重新加载远程配置
                                origin = repo.remotes.origin
                    except Exception as e:
                        # 解密失败或URL解析失败，使用原始URL
                        self.logger.warning(f"认证信息处理失败: {str(e)}")
            
            try:
                # 确保远程配置正确并执行 fetch（禁用交互式提示）
                with repo.git.custom_environment(**git_env):
                    try:
                        # 先尝试 fetch，如果没有 refspec 会抛出异常
                        origin.fetch()
                    except git.exc.GitCommandError as fetch_error:
                        if "no refspec set" in str(fetch_error):
                            # 添加默认的 refspec
                            with repo.config_writer() as cfg:
                                cfg.set_value(f'remote "{origin.name}"', 'fetch', '+refs/heads/*:refs/remotes/origin/*')
                            origin = repo.remotes.origin
                            origin.fetch()
                    
                    branches = [b.name for b in origin.fetch()]
                    return branches
            finally:
                # 恢复原始URL（移除凭证）
                if original_url and origin.url != original_url:
                    try:
                        with repo.config_writer() as cfg:
                            cfg.set_value(f'remote "{origin.name}"', 'url', original_url)
                    except Exception:
                        # 恢复失败不影响主要功能
                        pass
        except Exception as e:
            raise GitException(f"获取分支列表失败: {str(e)}")
    
    def get_commit_count(self, branch: str = 'master') -> int:
        """获取分支提交总数"""
        try:
            repo = git.Repo(str(self.local_path))
            return repo.iter_commits(f'origin/{branch}').count()
        except Exception as e:
            raise GitException(f"获取提交数失败: {str(e)}")


class GitException(Exception):
    """Git操作异常"""
    pass