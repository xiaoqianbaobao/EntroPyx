#!/usr/bin/env python3
"""
测试基于Repository配置的代码评审触发模式
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.repository.models import Repository
from apps.code_review.models import CodeReview, TriggerMode

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def test_repository_configs():
    """测试Repository配置"""
    print_section("测试：Repository配置")
    
    repositories = Repository.objects.all()
    
    if not repositories.exists():
        print("❌ 没有找到仓库")
        return
    
    for repo in repositories:
        print(f"\n📦 仓库: {repo.name}")
        print(f"   - 手动触发: {'✅' if repo.enable_manual_review else '❌'}")
        print(f"   - 定时评审: {'✅' if repo.enable_scheduled_review else '❌'}")
        if repo.enable_scheduled_review:
            print(f"     Cron表达式: {repo.scheduled_review_cron or '未设置'}")
        print(f"   - 实时监控: {'✅' if repo.enable_realtime_monitor else '❌'}")
        if repo.enable_realtime_monitor:
            print(f"     监控间隔: {repo.realtime_monitor_interval}秒")
            print(f"     监控分支: {repo.realtime_monitor_branches or [repo.review_branch]}")
        print(f"   - 自动评审: {'✅' if repo.auto_review_on_new_commit else '❌'}")
        print(f"   - 评审完成通知: {'✅' if repo.notify_on_review_complete else '❌'}")
        print(f"   - 通知阈值: {repo.notify_risk_threshold}")

def test_trigger_modes():
    """测试触发模式统计"""
    print_section("测试：触发模式统计")
    
    reviews = CodeReview.objects.all()
    
    if not reviews.exists():
        print("❌ 没有找到代码评审记录")
        return
    
    stats = {
        TriggerMode.MANUAL: 0,
        TriggerMode.SCHEDULED: 0,
        TriggerMode.REALTIME: 0,
        TriggerMode.WEBHOOK: 0,
    }
    
    for review in reviews:
        mode = review.trigger_mode or TriggerMode.MANUAL
        if mode in stats:
            stats[mode] += 1
    
    print(f"\n📊 代码评审触发模式统计:")
    print(f"   - 手动触发: {stats[TriggerMode.MANUAL]}条")
    print(f"   - 定时任务: {stats[TriggerMode.SCHEDULED]}条")
    print(f"   - 实时监控: {stats[TriggerMode.REALTIME]}条")
    print(f"   - Webhook: {stats[TriggerMode.WEBHOOK]}条")
    print(f"   - 总计: {reviews.count()}条")

def test_update_repository_config():
    """测试更新Repository配置"""
    print_section("测试：更新Repository配置")
    
    repositories = Repository.objects.all()
    
    if not repositories.exists():
        print("❌ 没有找到仓库")
        return
    
    # 更新第一个仓库的配置
    repo = repositories.first()
    
    print(f"\n📦 更新仓库: {repo.name}")
    
    # 启用实时监控
    repo.enable_realtime_monitor = True
    repo.realtime_monitor_interval = 60
    repo.realtime_monitor_branches = ['master', 'develop']
    repo.auto_review_on_new_commit = True
    repo.notify_on_review_complete = True
    repo.notify_risk_threshold = 'MEDIUM'
    
    repo.save()
    
    print(f"\n✅ 配置已更新:")
    print(f"   - 实时监控: ✅ 启用")
    print(f"   - 监控间隔: 60秒")
    print(f"   - 监控分支: ['master', 'develop']")
    print(f"   - 自动评审: ✅ 启用")
    print(f"   - 评审完成通知: ✅ 启用")
    print(f"   - 通知阈值: MEDIUM")

def main():
    print("\n" + "=" * 60)
    print("基于Repository配置的代码评审触发模式测试")
    print("=" * 60)
    
    try:
        # 测试Repository配置
        test_repository_configs()
        
        # 测试触发模式统计
        test_trigger_modes()
        
        # 测试更新Repository配置
        test_update_repository_config()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
        print("\n💡 使用说明:")
        print("   1. 在仓库配置页面可以设置:")
        print("      - 启用手动触发")
        print("      - 启用定时评审（设置Cron表达式）")
        print("      - 启用实时监控（设置监控间隔和分支）")
        print("   2. Celery Beat会自动执行定时任务")
        print("   3. 实时监控任务每分钟检查一次新提交")
        print("   4. 发现新提交后自动触发评审并发送钉钉通知")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()