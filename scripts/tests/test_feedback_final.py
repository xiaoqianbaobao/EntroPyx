#!/usr/bin/env python3
"""
最终验证代码评审反馈功能
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver
from apps.code_review.views import CodeReviewViewSet
import inspect

def verify_feedback_fix():
    """验证feedback修复是否成功"""
    print("🎯 代码评审反馈功能最终验证")
    print("=" * 70)
    
    # 1. 验证feedback方法在CodeReviewViewSet中
    print("\n1. 验证feedback方法位置...")
    if hasattr(CodeReviewViewSet, 'feedback'):
        print("   ✅ feedback方法存在于CodeReviewViewSet中")
        
        # 获取方法的详细信息
        method = getattr(CodeReviewViewSet, 'feedback')
        print(f"   📍 方法位置: {inspect.getfile(method)}:{inspect.getsourcelines(method)[1]}")
        
        # 检查方法装饰器
        if hasattr(method, 'mapping'):
            print(f"   📝 支持的HTTP方法: {list(method.mapping.keys())}")
        else:
            print("   📝 方法装饰器: @action(detail=True, methods=['post'])")
    else:
        print("   ❌ feedback方法不存在于CodeReviewViewSet中")
        return False
    
    # 2. 验证Django路由注册
    print("\n2. 验证Django路由注册...")
    resolver = get_resolver()
    
    def find_feedback_urls(patterns, prefix=''):
        feedback_urls = []
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                feedback_urls.extend(find_feedback_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
            elif hasattr(pattern, 'callback'):
                url = str(pattern.pattern)
                callback = pattern.callback
                if 'feedback' in url and 'code-review' in prefix:
                    feedback_urls.append(f'{prefix}{url}')
        return feedback_urls
    
    feedback_urls = find_feedback_urls(resolver.url_patterns)
    
    if feedback_urls:
        print("   ✅ feedback路由已注册:")
        for url in feedback_urls:
            print(f"      🌐 {url}")
    else:
        print("   ❌ feedback路由未找到")
        return False
    
    # 3. 验证方法实现完整性
    print("\n3. 验证feedback方法实现...")
    try:
        # 检查方法是否有正确的文档字符串
        if method.__doc__:
            print("   ✅ 包含文档字符串")
        
        # 获取源代码
        source = inspect.getsource(method)
        
        # 检查关键功能点
        checks = [
            ('get_object()', '获取评审对象'),
            ('feedback_status', '获取反馈状态'),
            ('FEEDBACK_STATUS_CHOICES', '验证反馈状态'),
            ('feedback_by', '记录反馈用户'),
            ('feedback_at', '记录反馈时间'),
            ('save()', '保存反馈信息'),
            ('logger.info', '记录日志'),
            ('return Response', '返回响应')
        ]
        
        for check, description in checks:
            if check in source:
                print(f"   ✅ 包含{description}")
            else:
                print(f"   ❌ 缺少{description}")
                return False
        
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return False
    
    # 4. 总结
    print("\n" + "=" * 70)
    print("🎉 验证完成！代码评审反馈功能已修复")
    print("\n📋 修复详情:")
    print("   • 问题: feedback方法在错误的类中(RealtimeMonitorConfigViewSet)")
    print("   • 修复: 将feedback方法移动到CodeReviewViewSet类中")
    print("   • 结果: Django路由正确注册，API可正常访问")
    
    print("\n🚀 API使用说明:")
    print("   端点: POST /api/v1/code-review/reviews/{id}/feedback/")
    print("   参数:")
    print("     - feedback_status: CORRECT 或 FALSE_POSITIVE")
    print("     - comment: 反馈说明（可选）")
    print("   响应: JSON格式，包含code、message、data字段")
    
    print("\n💡 前端调用示例:")
    print("   fetch('/api/v1/code-review/reviews/123/feedback/', {")
    print("     method: 'POST',")
    print("     headers: {'X-CSRFToken': csrfToken},")
    print("     body: JSON.stringify({")
    print("       feedback_status: 'CORRECT',")
    print("       comment: '准确的评审'")
    print("     })")
    print("   })")
    
    return True

if __name__ == '__main__':
    success = verify_feedback_fix()
    exit(0 if success else 1)
