"""
知识库URL配置
Knowledge Base URL Configuration
"""
from django.urls import path
from . import views

app_name = 'knowledge_base'

urlpatterns = [
    # 页面路由
    path('', views.knowledge_base_list, name='list'),
    path('detail/<int:pk>/', views.knowledge_base_detail, name='detail'),
    path('upload/', views.knowledge_base_upload, name='upload'),
    path('chat/', views.knowledge_base_chat, name='chat'),
    
    # API路由
    path('api/documents/', views.KnowledgeDocumentListView.as_view(), name='api_documents_list'),
    path('api/documents/<int:pk>/', views.KnowledgeDocumentDetailView.as_view(), name='api_documents_detail'),
    path('api/documents/upload/', views.KnowledgeDocumentUploadView.as_view(), name='api_documents_upload'),
    path('api/documents/<int:pk>/delete/', views.KnowledgeDocumentDeleteView.as_view(), name='api_documents_delete'),
    path('api/documents/search/', views.KnowledgeDocumentSearchView.as_view(), name='api_documents_search'),
    path('api/query/', views.KnowledgeQueryView.as_view(), name='api_query'),
    path('api/entities/', views.KnowledgeEntityListView.as_view(), name='api_entities'),
    path('api/relations/', views.KnowledgeRelationListView.as_view(), name='api_relations'),
]