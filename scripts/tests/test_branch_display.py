#!/usr/bin/env python3
"""
测试分支显示问题
"""
import os
import sys

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/csq/workspace/bestBugBot')

import django
django.setup()

from apps.repository.services.git_service import GitService
from apps.repository.models import Repository

def test_branch_in_commits():
    """测试commit对象中的branch字段"""
    print("🔍 测试commit对象中的branch字段")
    
    # 获取一个仓库
    try:
        repo = Repository.objects.first()
        if not repo:
            print("❌ 没有找到仓库")
            return False
        
        git_service = GitService(repo)
        
        # 测试获取不同分支的提交
        print(f"\n测试仓库: {repo.name}")
        
        # 测试单个分支
        commits_master = git_service.get_today_commits('master', all_branches=False, days=1)
        print(f"master分支提交数: {len(commits_master)}")
        if commits_master:
            print(f"  第一个提交的branch字段: {commits_master[0].get('branch', 'None')}")
        
        # 测试所有分支
        commits_all = git_service.get_today_commits('master', all_branches=True, days=1)
        print(f"所有分支提交数: {len(commits_all)}")
        if commits_all:
            print(f"  第一个提交的branch字段: {commits_all[0].get('branch', 'None')}")
            
            # 显示前5个提交的分支信息
            print("  前5个提交的分支信息:")
            for i, commit in enumerate(commits_all[:5]):
                print(f"    {i+1}. {commit['hash'][:8]} - {commit.get('branch', 'None')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_code_review_branch_storage():
    """测试CodeReview模型中branch字段的存储"""
    print("\n🔍 测试CodeReview模型中branch字段的存储")
    
    try:
        from apps.code_review.models import CodeReview
        
        # 获取一些评审记录
        reviews = CodeReview.objects.all()[:5]
        print(f"找到 {len(reviews)} 条评审记录")
        
        for i, review in enumerate(reviews):
            print(f"  {i+1}. {review.repository.name} - {review.branch} - {review.commit_hash[:8]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试分支显示问题")
    
    results = []
    results.append(("commit对象branch字段", test_branch_in_commits()))
    results.append(("CodeReview存储branch字段", test_code_review_branch_storage()))
    
    print("\n" + "="*60)
    print("📋 测试结果总结")
    print("="*60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，需要进一步修复")

if __name__ == '__main__':
    main()
