"""
会议助手URL配置
Meeting Assistant URL Configuration
"""
from django.urls import path
from . import views

app_name = 'meeting_assistant'

urlpatterns = [
    # 页面路由
    path('', views.meeting_list, name='meeting_list'),
    path('upload/', views.meeting_upload, name='meeting_upload'),
    path('realtime-record/', views.realtime_record, name='realtime_record'),
    path('detail/<int:pk>/', views.meeting_detail, name='meeting_detail'),
    path('summary/<int:pk>/', views.summary_detail, name='summary_detail'),
    path('knowledge-graph/', views.knowledge_graph, name='knowledge_graph'),
    
    # API路由
    path('api/recordings/', views.RecordingListView.as_view(), name='api_recording_list'),
    path('api/recordings/bulk-delete/', views.RecordingBulkDeleteView.as_view(), name='api_recording_bulk_delete'),
    path('api/recordings/<int:pk>/', views.RecordingDetailView.as_view(), name='api_recording_detail'),
    path('api/recordings/upload/', views.RecordingUploadView.as_view(), name='api_recording_upload'),
    path('api/recordings/<int:pk>/audio/', views.RecordingAudioPlayView.as_view(), name='api_recording_audio'),
    path('api/recordings/<int:pk>/status/', views.RecordingStatusView.as_view(), name='api_recording_status'),
    
    path('api/summaries/', views.SummaryListView.as_view(), name='api_summary_list'),
    path('api/summaries/<int:pk>/', views.SummaryDetailView.as_view(), name='api_summary_detail'),
    path('api/recordings/<int:recording_id>/generate-summary/', views.GenerateSummaryView.as_view(), name='api_generate_summary'),
    path('api/summaries/<int:pk>/export/', views.ExportSummaryView.as_view(), name='api_export_summary'),
    
    path('api/opinions/', views.OpinionListView.as_view(), name='api_opinion_list'),
    path('api/opinions/<int:pk>/', views.OpinionDetailView.as_view(), name='api_opinion_detail'),
    
    # 知识图谱API
    path('api/kg/search/', views.KGSearchView.as_view(), name='api_kg_search'),
    path('api/kg/entities/<int:entity_id>/', views.KGEntityDetailView.as_view(), name='api_kg_entity_detail'),
]