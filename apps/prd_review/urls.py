from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PRDReviewViewSet, PRDReviewApproveView, PRDReviewStartView

router = DefaultRouter()
router.register(r'prd-reviews', PRDReviewViewSet, basename='prd-review')

urlpatterns = [
    path('', include(router.urls)),
    path('prd-reviews/<int:pk>/approve/', PRDReviewApproveView.as_view(), name='prd-review-approve'),
    path('prd-reviews/<int:pk>/review/', PRDReviewStartView.as_view(), name='prd-review-start'),
]
