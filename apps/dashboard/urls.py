from django.urls import path
from .views import DashboardStatsView, RiskTrendView, RepositoryRankingView, DeveloperRankingView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('trend/', RiskTrendView.as_view(), name='dashboard-trend'),
    path('repository-ranking/', RepositoryRankingView.as_view(), name='dashboard-repo-ranking'),
    path('developer-ranking/', DeveloperRankingView.as_view(), name='dashboard-dev-ranking'),
]
