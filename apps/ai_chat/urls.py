"""
AI对话URL路由
"""
from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    # 页面视图
    path('', views.ai_chat_page, name='ai_chat_page'),
    path('conversation/<int:conversation_id>/', 
         views.conversation_detail_page, 
         name='conversation_detail_page'),
    
    # API视图
    path('api/conversations/', 
         views.ConversationListView.as_view(), 
         name='conversation_list_api'),
    path('api/conversations/<int:pk>/', 
         views.ConversationDetailView.as_view(), 
         name='conversation_detail_api'),
    path('api/conversations/<int:conversation_id>/messages/', 
         views.MessageListView.as_view(), 
         name='message_list_api'),
    path('api/chat/', 
         views.chat_view, 
         name='chat_api'),
    path('api/chat/stream/', 
         views.chat_stream_view, 
         name='chat_stream_api'),
    path('api/save_message/', 
         views.save_message_view, 
         name='save_message_api'),
    path('api/conversations/<int:conversation_id>/clear/', 
         views.clear_conversation_history, 
         name='clear_conversation_api'),
    path('api/conversations/stats/', 
         views.get_conversation_stats, 
         name='conversation_stats_api'),
]
