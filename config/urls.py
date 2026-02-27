"""
URL configuration for 熵减X-AI.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from apps.core import views as core_views
from apps.repository import urls as repo_urls
from apps.code_review import urls as review_urls
from apps.prd_review import urls as prd_urls
from apps.test_case import urls as test_urls
from apps.feedback import views as feedback_views

from apps.users.views import EncryptedLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 页面视图
    path('', include('apps.ai_chat.urls', namespace='home_chat')), # 首页直接指向 AI Chat
    path('dashboard/', core_views.dashboard, name='dashboard'), # 原首页改为 /dashboard/
    path('health/', core_views.health_check, name='health_check'),
    
    # 智能体聚合页
    path('product-agent/', core_views.product_agent_view, name='product_agent'),
    path('developer-agent/', core_views.developer_agent_view, name='developer_agent'),
    
    path('repository/', core_views.repository_list, name='repository_list'),
    path('repository/create/', core_views.repository_create, name='repository_create'),
    path('repository/<int:pk>/', core_views.repository_detail, name='repository_detail'),
    path('repository/<int:pk>/update/', core_views.repository_update, name='repository_update'),
    path('code-review/reviews/', core_views.code_review_list, name='code_review_list'),
    path('code-review/reviews/<int:pk>/', core_views.code_review_detail, name='code_review_detail'),
    path('prd-review/prd-reviews/', core_views.prd_review_list_v2, name='prd_review_list'),
    path('prd-review/prd-reviews/old/', core_views.prd_review_list, name='prd_review_list_old'),
    path('prd-review/prd-reviews/<int:pk>/', core_views.prd_review_detail, name='prd_review_detail'),
    path('prd-review/prd-reviews/<int:pk>/edit/', core_views.prd_review_edit, name='prd_review_edit'),
    path('test-case/test-cases/', core_views.test_case_list, name='test_case_list'),
    path('test-case/test-cases/<int:pk>/', core_views.test_case_detail, name='test_case_detail'),
    path('test-case/test-cases/generate/', core_views.test_case_generate, name='test_case_generate'),
    path('feedback/feedback-rules/', feedback_views.feedback_rules_list, name='feedback_rules_list'),
    path('meeting-assistant/', include('apps.meeting_assistant.urls')),
    path('ai-chat/', include('apps.ai_chat.urls', namespace='ai_chat')),
    
    # 登录 (使用自定义加密视图)
    path('accounts/login/', EncryptedLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 平台管理
    path('platform-management/', include('apps.platform_management.urls')),
    
    # API v1
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/repository/', include('apps.repository.urls')),
    path('api/v1/code-review/', include('apps.code_review.urls')),
    path('api/v1/prd-review/', include('apps.prd_review.urls')),
    path('api/v1/test-case/', include('apps.test_case.urls')),
    path('api/v1/feedback/', include('apps.feedback.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/knowledge/', include('apps.knowledge_base.urls', namespace='knowledge_base')), # 保持API路径，添加namespace供代理使用
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
