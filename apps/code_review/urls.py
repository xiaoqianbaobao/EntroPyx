from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.code_review.views import (
    CodeReviewViewSet,
    ScheduledReviewConfigViewSet,
    RealtimeMonitorConfigViewSet
)

router = DefaultRouter()
router.register(r'reviews', CodeReviewViewSet, basename='code-review')
router.register(r'scheduled-configs', ScheduledReviewConfigViewSet, basename='scheduled-config')
router.register(r'realtime-configs', RealtimeMonitorConfigViewSet, basename='realtime-config')

urlpatterns = [
    path('', include(router.urls)),
]