from django.urls import path
from apps.core import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('health/', views.health_check, name='health_check'),
    path('repository/', views.repository_list, name='repository_list'),
    path('code-review/', views.code_review_list, name='code_review_list'),
    path('prd-review/', views.prd_review_list, name='prd_review_list'),
    path('test-case/', views.test_case_list, name='test_case_list'),
]
