from django.urls import path
from . import views

app_name = 'platform_management'

urlpatterns = [
    # 平台管理首页
    path('', views.dashboard_view, name='dashboard'),
    path('api/llm-config/update/', views.update_llm_config, name='update_llm_config'),
    
    # 智能体管理
    path('agents/', views.agent_list_view, name='agent_list'),
    path('agents/create/', views.agent_create_view, name='agent_create'),
    path('agents/<int:pk>/', views.agent_detail_view, name='agent_detail'),
    path('agents/<int:pk>/update/', views.agent_update_view, name='agent_update'),
    path('agents/<int:pk>/delete/', views.agent_delete_view, name='agent_delete'),
    
    # 工作流编排
    path('workflows/', views.workflow_list_view, name='workflow_list'),
    path('workflows/create/', views.workflow_create_view, name='workflow_create'),
    path('workflows/<int:pk>/', views.workflow_detail_view, name='workflow_detail'),
    
    # 知识库管理（重定向或包装）
    path('knowledge/', views.knowledge_base_proxy_view, name='knowledge_base'),
]