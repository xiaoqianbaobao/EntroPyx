#!/usr/bin/env python3
"""
直接测试feedback方法
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.code_review.views import CodeReviewViewSet

def test_feedback_direct():
    """直接测试feedback方法"""
    print("🔍 直接测试feedback方法")
    
    # 检查CodeReviewViewSet类
    if hasattr(CodeReviewViewSet, 'feedback'):
        print("✅ feedback方法在类中")
        
        # 检查方法装饰器
        import inspect
        feedback_method = getattr(CodeReviewViewSet, 'feedback')
        print(f"反馈方法: {feedback_method}")
        print(f"方法签名: {inspect.signature(feedback_method)}")
        
        # 检查是否有@action装饰器
        if hasattr(feedback_method, 'detail'):
            print(f"✅ @action装饰器存在，detail={feedback_method.detail}")
        else:
            print("❌ @action装饰器不存在")
            
    else:
        print("❌ feedback方法不在类中")
        
        # 检查所有方法
        print("\n所有方法:")
        for name in dir(CodeReviewViewSet):
            if not name.startswith('_'):
                method = getattr(CodeReviewViewSet, name)
                if callable(method):
                    print(f"  {name}")
    
    # 测试路由器注册
    print("\n测试路由器注册:")
    from rest_framework.routers import DefaultRouter
    
    router = DefaultRouter()
    router.register(r'reviews', CodeReviewViewSet, basename='code-review')
    
    print(f"注册的路由数量: {len(router.urls)}")
    for i, url in enumerate(router.urls):
        if 'feedback' in str(url.pattern):
            print(f"  ✅ 找到feedback路由: {url.pattern}")

if __name__ == '__main__':
    test_feedback_direct()
