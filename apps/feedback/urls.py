from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedbackRuleViewSet, FeedbackStatsView

router = DefaultRouter()
router.register(r'feedback-rules', FeedbackRuleViewSet, basename='feedback-rule')

urlpatterns = [
    path('', include(router.urls)),
    path('feedback-rules/statistics/', FeedbackStatsView.as_view(), name='feedback-stats'),
]
