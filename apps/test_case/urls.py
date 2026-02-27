from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestCaseViewSet, TestReportViewSet, TestExecutionView, GenerateTestCasesView

router = DefaultRouter()
router.register(r'test-cases', TestCaseViewSet, basename='test-case')
router.register(r'test-reports', TestReportViewSet, basename='test-report')

urlpatterns = [
    path('', include(router.urls)),
    path('execute/', TestExecutionView.as_view(), name='test-execute'),
    path('generate/', GenerateTestCasesView.as_view(), name='test-generate'),
]
