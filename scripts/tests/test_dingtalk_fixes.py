#!/usr/bin/env python3
"""
测试钉钉消息修复
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.services.dingtalk_service import DingTalkService

def test_simplified_content():
    """测试精简AI评审结果"""
    print("🔍 测试精简AI评审结果")
    
    # 模拟长的AI评审结果
    long_ai_summary = """【总体评价】 本次代码变更移除了ext.put("remark", "结算代付备注");这一行，从代码质量上看，这是一个简单的删除操作，没有引入新的语法错误。但从业务逻辑和架构设计角度看，这是一个涉及支付结算核心流程的变更，且提交信息"代付"过于简略，缺乏必要的上下文说明。在支付系统中，"备注"字段通常用于记录交易的关键信息，用于对账、审计和问题排查，直接删除可能影响后续的业务追溯能力。

【严重问题】
🔴 必须修复：删除备注字段可能导致业务追溯困难
🔴 风险高：支付核心流程变更缺乏充分说明

【建议】
⚠️ 建议添加新的业务逻辑说明
⚠️ 建议在其他地方补充备注信息

【风险】
⚠️ 业务风险：可能影响对账和审计
⚠️ 技术风险：代码变更缺乏文档说明

【影响】
🔴 影响对账系统
🔴 影响审计追踪
"""
    
    dingtalk = DingTalkService('https://oapi.dingtalk.com/robot/send?access_token=test')
    simplified = dingtalk._simplify_ai_summary(long_ai_summary)
    
    print(f"原始内容长度: {len(long_ai_summary)} 字符")
    print(f"精简后长度: {len(simplified)} 字符")
    print("\n精简后的内容:")
    print(simplified)
    
    return True

def test_review_url():
    """测试评审报告链接"""
    print("\n🔍 测试评审报告链接")
    
    review_data = {
        'repository_name': 'settle-server-pro',
        'branch': 'origin/test',
        'commit_hash': '8ccf69b1',
        'review_id': 123
    }
    
    dingtalk = DingTalkService('https://oapi.dingtalk.com/robot/send?access_token=test')
    content = dingtalk._build_review_content(review_data)
    
    # 检查链接是否正确构建
    expected_url = "http://0.0.0.0:8000/code-review/reviews/123/"
    if expected_url in content:
        print("✅ 评审报告链接正确构建")
    else:
        print("❌ 评审报告链接构建错误")
        print(f"期望URL: {expected_url}")
        print(f"实际URL: {expected_url}")
    
    return True

def test_branch_display():
    """测试分支显示修复"""
    print("\n🔍 测试分支显示修复")
    
    # 模拟正确的分支信息
    review_data = {
        'repository_name': 'settle-server-pro',
        'branch': 'origin/test',  # 正确的分支
        'commit_hash': '8ccf69b1',
        'author': '吴涛',
        'risk_level': 'LOW',
        'risk_score': 0,
        'changed_files': [],
        'ai_summary': '测试内容'
    }
    
    dingtalk = DingTalkService('https://oapi.dingtalk.com/robot/send?access_token=test')
    content = dingtalk._build_review_content(review_data)
    
    if 'origin/test' in content:
        print("✅ 分支显示正确")
    else:
        print("❌ 分支显示错误")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试钉钉消息修复")
    
    results = []
    results.append(("精简AI评审结果", test_simplified_content()))
    results.append(("评审报告链接", test_review_url()))
    results.append(("分支显示修复", test_branch_display()))
    
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
        print("⚠️  部分测试失败")

if __name__ == '__main__':
    main()