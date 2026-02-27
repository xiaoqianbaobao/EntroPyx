"""
Celery configuration for 熵减X-AI.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ai_review_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Celery Beat 定时任务配置
app.conf.beat_schedule = {
    # 每分钟执行一次实时监控任务（检查所有启用了实时监控的仓库）
    'realtime-monitor-all': {
        'task': 'apps.code_review.tasks.check_all_realtime_monitors',
        'schedule': crontab(),  # 每分钟执行
    },
}

app.conf.timezone = 'Asia/Shanghai'