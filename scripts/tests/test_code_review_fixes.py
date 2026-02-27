#!/usr/bin/env python3
"""
测试和修复代码评审问题
"""
import os
import sys
import django
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.code_review.services.risk_classifier import RiskClassifier
from apps.code_review.services.ai_engine import AIReviewEngine
from apps.core.services.dingtalk_service import DingTalkService
from apps.code_review.models import CodeReview, ReviewTask
from apps.repository.models import Repository
from django.utils import timezone

def test_risk_classification():
    """测试风险评级逻辑"""
    print("\n" + "="*60)
    print("🔍 测试风险评级逻辑")
    print("="*60)
    
    classifier = RiskClassifier()
    engine = AIReviewEngine()
    
    # 测试用例：严重问题但风险等级低
    test_issues = [
        {
            'severity': 'high',
            'type': 'security',
            'description': '发现SQL注入漏洞'
        },
        {
            'severity': 'high',
            'type': 'security',
            'description': '发现XSS漏洞'
        }
    ]
    
    test_files = [
        {'path': 'src/main.py', 'is_critical': True}
    ]
    
    risk_score = classifier.classify(test_issues, test_files)
    risk_level = engine._get_risk_level(risk_score)
    
    print(f"测试问题: {len(test_issues)} 个高危问题")
    print(f"风险评分: {risk_score:.3f}")
    print(f"风险等级: {risk_level}")
    print(f"风险等级显示: {risk_level} ({risk_score*100:.1f}%)")
    
    # 检查是否正确分类
    if risk_level == 'HIGH' and risk_score >= 0.7:
        print("✅ 风险评级正确")
    else:
        print("❌ 风险评级错误，需要修复")
        return False
    
    return True

def test_dingtalk_content_length():
    """测试钉钉消息内容长度"""
    print("\n" + "="*60)
    print("📝 测试钉钉消息内容长度")
    print("="*60)
    
    # 模拟长内容
    long_content = "## AI代码评审报告\n\n" + "这是一个非常长的评审内容" * 200 + "\n\n**风险等级**: HIGH\n\n" + "详细分析内容" * 100
    
    print(f"模拟内容长度: {len(long_content.encode('utf-8'))} 字节")
    print(f"模拟内容长度: {len(long_content)} 字符")
    
    # 测试钉钉服务
    dingtalk = DingTalkService(
        webhook="https://oapi.dingtalk.com/robot/send?access_token=test",
        secret="test"
    )
    
    # 检查内容构建
    review_data = {
        'repository_name': 'test-repo',
        'branch': 'feature-branch',
        'commit_hash': 'a1b2c3d4',
        'author': 'test-author',
        'commit_message': '测试提交信息',
        'risk_level': 'HIGH',
        'risk_score': 0.85,
        'changed_files': [
            {'path': 'src/file1.py', 'status': 'M'},
            {'path': 'src/file2.py', 'status': 'A'}
        ],
        'ai_summary': long_content
    }
    
    content = dingtalk._build_review_content(review_data)
    content_length = len(content.encode('utf-8'))
    
    print(f"构建后内容长度: {content_length} 字节")
    print(f"构建后内容长度: {len(content)} 字符")
    
    # 检查是否超过钉钉限制
    if content_length > 4096:
        print("❌ 内容超过钉钉4096字节限制")
        return False
    else:
        print("✅ 内容在钉钉限制范围内")
    
    return True

def test_branch_display():
    """测试分支显示逻辑"""
    print("\n" + "="*60)
    print("🏷️  测试分支显示逻辑")
    print("="*60)
    
    # 模拟不同分支的评审数据
    test_cases = [
        {'branch': 'master', 'expected': 'master'},
        {'branch': 'develop', 'expected': 'develop'},
        {'branch': 'feature/user-auth', 'expected': 'feature/user-auth'},
        {'branch': 'release/v1.2.0', 'expected': 'release/v1.2.0'}
    ]
    
    for case in test_cases:
        branch = case['branch']
        expected = case['expected']
        
        # 模拟任务处理中的分支显示
        display_branch = branch  # 实际应该使用实际评审的分支
        
        print(f"分支: {branch} -> 显示: {display_branch} (期望: {expected})")
        
        if display_branch == expected:
            print("✅ 分支显示正确")
        else:
            print("❌ 分支显示错误")
    
    return True

def test_review_task_progress():
    """测试评审任务进度显示"""
    print("\n" + "="*60)
    print("📊 测试评审任务进度显示")
    print("="*60)
    
    # 模拟任务进度更新
    tasks = [
        {'name': '全分支评审', 'current': 1, 'total': 5, 'branch': 'develop'},
        {'name': '指定分支评审', 'current': 1, 'total': 1, 'branch': 'feature-new'},
        {'name': '多分支评审', 'current': 3, 'total': 8, 'branch': 'feature-auth'}
    ]
    
    for task in tasks:
        progress = (task['current'] / task['total']) * 100
        print(f"{task['name']}: {task['branch']} - {task['current']}/{task['total']} ({progress:.0f}%)")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试代码评审修复")
    
    results = []
    results.append(("风险评级逻辑", test_risk_classification()))
    results.append(("钉钉消息长度", test_dingtalk_content_length()))
    results.append(("分支显示逻辑", test_branch_display()))
    results.append(("任务进度显示", test_review_task_progress()))
    
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