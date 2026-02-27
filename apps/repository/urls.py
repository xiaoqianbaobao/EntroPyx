from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RepositoryViewSet, RepositorySyncView, RepositoryBranchesView

router = DefaultRouter()
router.register(r'repositories', RepositoryViewSet, basename='repository')

urlpatterns = [
    path('', include(router.urls)),
    path('repositories/<int:pk>/sync/', RepositorySyncView.as_view(), name='repository-sync'),
    path('repositories/<int:pk>/branches/', RepositoryBranchesView.as_view(), name='repository-branches'),
]
