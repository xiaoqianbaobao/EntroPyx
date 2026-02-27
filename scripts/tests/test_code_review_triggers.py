#!/usr/bin/env python3
"""
代码评审触发模式测试脚本
"""
import os
import django
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.code_review.models import (
    ScheduledReviewConfig,
    RealtimeMonitorConfig,
    CodeReview,
    ReviewTask,
    TriggerMode
)
from apps.repository.models import Repository
from apps.users.models import User


def test_scheduled_config():
    """测试创建定时评审配置"""
    print("=" * 50)
    print("测试：创建定时评审配置")
    print("=" * 50)
    
    # 获取第一个仓库
    repo = Repository.objects.first()
    if not repo:
        print("❌ 没有找到仓库，请先创建仓库")
        return
    
    # 获取第一个用户
    user = User.objects.first()
    if not user:
        print("❌ 没有找到用户，请先创建用户")
        return
    
    # 创建定时评审配置 - 中午12点
    config, created = ScheduledReviewConfig.objects.get_or_create(
        name="中午批量评审",
        defaults={
            'description': '每天中午12点批量评审所有仓库',
            'cron_expression': '0 12 * * *',
            'branches': ['master', 'develop'],
            'review_all_branches': False,
            'is_active': True,
            'notify_on_complete': True,
            'created_by': user
        }
    )
    
    if created:
        config.repositories.add(repo)
        print(f"✅ 创建定时评审配置成功: {config.name}")
        print(f"   - Cron表达式: {config.cron_expression}")
        print(f"   - 评审分支: {config.branches}")
        print(f"   - 关联仓库: {repo.name}")
    else:
        print(f"⚠️  定时评审配置已存在: {config.name}")
    
    # 创建定时评审配置 - 傍晚18点
    config2, created = ScheduledReviewConfig.objects.get_or_create(
        name="傍晚批量评审",
        defaults={
            'description': '每天傍晚18点批量评审所有仓库',
            'cron_expression': '0 18 * * *',
            'branches': ['master', 'develop'],
            'review_all_branches': False,
            'is_active': True,
            'notify_on_complete': True,
            'created_by': user
        }
    )
    
    if created:
        config2.repositories.add(repo)
        print(f"✅ 创建定时评审配置成功: {config2.name}")
        print(f"   - Cron表达式: {config2.cron_expression}")
    else:
        print(f"⚠️  定时评审配置已存在: {config2.name}")


def test_realtime_monitor():
    """测试创建实时监控配置"""
    print("\n" + "=" * 50)
    print("测试：创建实时监控配置")
    print("=" * 50)
    
    # 获取第一个仓库
    repo = Repository.objects.first()
    if not repo:
        print("❌ 没有找到仓库，请先创建仓库")
        return
    
    # 创建或更新实时监控配置
    config, created = RealtimeMonitorConfig.objects.get_or_create(
        repository=repo,
        defaults={
            'is_active': True,
            'monitored_branches': ['master', 'develop'],
            'check_interval': 60,
            'auto_review': True,
            'notify_on_new_commit': True,
            'notify_level': 'MEDIUM'
        }
    )
    
    if created:
        print(f"✅ 创建实时监控配置成功")
        print(f"   - 仓库: {repo.name}")
        print(f"   - 监控分支: {config.monitored_branches}")
        print(f"   - 检查间隔: {config.check_interval}秒")
        print(f"   - 自动评审: {config.auto_review}")
        print(f"   - 通知级别: {config.notify_level}")
    else:
        print(f"⚠️  实时监控配置已存在")
        print(f"   - 状态: {'启用' if config.is_active else '禁用'}")


def test_manual_trigger():
    """测试手动触发评审"""
    print("\n" + "=" * 50)
    print("测试：手动触发评审")
    print("=" * 50)
    
    from apps.code_review.tasks import trigger_manual_review
    
    repo = Repository.objects.first()
    if not repo:
        print("❌ 没有找到仓库，请先创建仓库")
        return
    
    user = User.objects.first()
    
    # 触发手动评审
    task = trigger_manual_review.delay(
        repository_id=repo.id,
        branch='master',
        all_branches=False,
        triggered_by_id=user.id if user else None
    )
    
    print(f"✅ 手动评审任务已触发")
    print(f"   - 任务ID: {task.id}")
    print(f"   - 仓库: {repo.name}")
    print(f"   - 分支: master")
    print(f"\n💡 使用以下命令查看任务状态:")
    print(f"   GET /api/v1/code-reviews/task-status/?task_id={task.id}")


def test_webhook_trigger():
    """测试Webhook触发评审"""
    print("\n" + "=" * 50)
    print("测试：Webhook触发评审")
    print("=" * 50)
    
    from apps.code_review.tasks import webhook_review_task
    
    repo = Repository.objects.first()
    if not repo:
        print("❌ 没有找到仓库，请先创建仓库")
        return
    
    # 模拟GitLab/GitHub推送
    result = webhook_review_task.delay(
        repository_id=repo.id,
        commit_hash='test_webhook_commit_hash',
        branch='master',
        author='测试用户',
        author_email='test@example.com',
        commit_message='Webhook测试提交'
    )
    
    print(f"✅ Webhook评审任务已触发")
    print(f"   - 仓库: {repo.name}")
    print(f"   - Commit: test_webhook_commit_hash")
    print(f"   - 作者: 测试用户")
    print("\n💡 实际使用时，在GitLab/GitHub中配置Webhook URL:")
    print(f"   POST https://your-domain.com/api/v1/code-reviews/webhook-trigger/")


def show_summary():
    """显示配置摘要"""
    print("\n" + "=" * 50)
    print("配置摘要")
    print("=" * 50)
    
    # 定时评审配置
    scheduled_configs = ScheduledReviewConfig.objects.all()
    print(f"\n📅 定时评审配置: {scheduled_configs.count()}个")
    for config in scheduled_configs:
        status = "✅ 启用" if config.is_active else "❌ 禁用"
        print(f"   - {config.name} ({config.cron_expression}) {status}")
    
    # 实时监控配置
    realtime_configs = RealtimeMonitorConfig.objects.all()
    print(f"\n👁️  实时监控配置: {realtime_configs.count()}个")
    for config in realtime_configs:
        status = "✅ 启用" if config.is_active else "❌ 禁用"
        print(f"   - {config.repository.name} {status}")
    
    # 代码评审记录
    reviews = CodeReview.objects.all()
    print(f"\n📊 代码评审记录: {reviews.count()}条")
    print(f"   - 手动触发: {reviews.filter(trigger_mode='MANUAL').count()}条")
    print(f"   - 定时任务: {reviews.filter(trigger_mode='SCHEDULED').count()}条")
    print(f"   - 实时监控: {reviews.filter(trigger_mode='REALTIME').count()}条")
    print(f"   - Webhook: {reviews.filter(trigger_mode='WEBHOOK').count()}条")
    
    # 风险统计
    print(f"\n🎯 风险统计:")
    print(f"   - 高风险: {reviews.filter(risk_level='HIGH').count()}条")
    print(f"   - 中风险: {reviews.filter(risk_level='MEDIUM').count()}条")
    print(f"   - 低风险: {reviews.filter(risk_level='LOW').count()}条")


def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("代码评审触发模式测试")
    print("=" * 50)
    
    try:
        # 测试定时评审配置
        test_scheduled_config()
        
        # 测试实时监控配置
        test_realtime_monitor()
        
        # 测试手动触发
        test_manual_trigger()
        
        # 测试Webhook触发
        test_webhook_trigger()
        
        # 显示摘要
        show_summary()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成！")
        print("=" * 50)
        print("\n📖 详细使用说明请查看: CODE_REVIEW_GUIDE.md")
        print("\n🚀 启动服务:")
        print("   python3 manage.py runserver")
        print("   celery -A config worker -l info")
        print("   celery -A config beat -l info")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()