"""
AI对话视图
"""
import json
import time
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer, 
    MessageSerializer, 
    ChatRequestSerializer, 
    ChatResponseSerializer
)
from .services import AIChatService


# ==================== 页面视图 ====================

def ai_chat_page(request):
    """AI对话主页面"""
    # 获取用户的对话列表
    conversations = Conversation.objects.filter(
        is_active=True
    ).order_by('-updated_at')[:20]
    
    # 获取知识库列表（用于选择）
    from apps.knowledge_base.models import KnowledgeDocument
    knowledge_docs = KnowledgeDocument.objects.filter(status='completed')
    
    # 获取仓库列表（用于选择）
    from apps.repository.models import Repository
    repositories = Repository.objects.filter(is_active=True)
    
    return render(request, 'ai_chat/chat.html', {
        'conversations': conversations,
        'knowledge_docs': knowledge_docs,
        'repositories': repositories,
    })


def conversation_detail_page(request, conversation_id):
    """对话详情页面"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    messages = conversation.messages.all().order_by('created_at')
    
    return render(request, 'ai_chat/conversation.html', {
        'conversation': conversation,
        'messages': messages,
    })


# ==================== API视图 ====================

class ConversationListView(generics.ListCreateAPIView):

    """对话列表API"""

    serializer_class = ConversationSerializer

    permission_classes = [AllowAny]

    

    def get_queryset(self):

        # 返回所有对话，无需用户过滤

        return Conversation.objects.filter(is_active=True).order_by('-updated_at')

    

    def perform_create(self, serializer):

        serializer.save()


class ConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """对话详情API"""
    serializer_class = ConversationSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        # 返回所有对话，无需用户过滤
        return Conversation.objects.all()
    
    def perform_destroy(self, instance):
        # 软删除
        instance.is_active = False
        instance.save()


class MessageListView(generics.ListAPIView):
    """消息列表API"""
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        # 不再基于用户过滤，直接根据对话ID获取消息
        return Message.objects.filter(
            conversation_id=conversation_id
        ).order_by('created_at')


@api_view(['POST'])
@permission_classes([AllowAny])
def chat_view(request):
    """
    对话API
    支持新建会话或继续已有会话
    """
    # 验证请求数据
    serializer = ChatRequestSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # 获取或创建对话
        conversation = None
        if 'conversation_id' in data:
            # 继续已有对话
            conversation = Conversation.objects.get(
                id=data['conversation_id']
            )
        else:
            # 创建新对话
            # 如果用户已登录，使用登录用户；否则创建或使用默认用户
            user = request.user if request.user.is_authenticated else None
            
            # 如果没有用户，尝试创建一个默认访客用户
            if user is None:
                try:
                    user, created = get_user_model().objects.get_or_create(
                        username='guest',
                        defaults={
                            'email': 'guest@example.com',
                            'is_active': True
                        }
                    )
                except Exception as e:
                    print(f"创建访客用户失败: {e}")
                    # 如果仍然失败，尝试获取第一个用户
                    user = get_user_model().objects.first()
                    if user is None:
                        raise Exception("无法获取用户，请联系管理员")
            
            print(f"创建对话，用户ID: {user.id}, 用户名: {user.username}")
            
            # 处理外键关联
            from apps.knowledge_base.models import KnowledgeDocument
            from apps.repository.models import Repository
            
            knowledge_base = None
            if data.get('knowledge_base_id'):
                try:
                    knowledge_base = KnowledgeDocument.objects.get(id=data['knowledge_base_id'])
                except KnowledgeDocument.DoesNotExist:
                    pass
            
            repository = None
            if data.get('repository_id'):
                try:
                    repository = Repository.objects.get(id=data['repository_id'])
                except Repository.DoesNotExist:
                    pass
            
            conversation = Conversation.objects.create(
                title=data['message'][:50] + '...' if len(data['message']) > 50 else data['message'],
                user=user,
                conversation_type=data.get('conversation_type', 'general'),
                knowledge_base=knowledge_base,
                repository=repository
            )
            print(f"对话创建成功，对话ID: {conversation.id}")
        
        # 保存用户消息
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=data['message']
        )
        
        # 准备对话历史
        messages = conversation.messages.all().order_by('created_at')
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # 搜索知识库
        knowledge_context = None
        if conversation.knowledge_base:
            ai_service = AIChatService()
            knowledge_context = ai_service.search_knowledge(
                data['message'], 
                conversation.knowledge_base.id
            )
        
        # 调用AI服务
        ai_service = AIChatService()
        ai_response = ai_service.chat(
            messages=history,
            knowledge_context=knowledge_context,
            conversation_type=conversation.conversation_type
        )
        
        # 保存AI回复
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response['content'],
            knowledge_references=ai_response.get('knowledge_references', []),
            tokens_used=ai_response.get('tokens_used', 0),
            response_time=ai_response.get('response_time', 0.0)
        )
        
        # 更新对话时间
        conversation.save()  # 自动更新updated_at
        
        # 返回响应
        response_data = {
            'conversation_id': conversation.id,
            'message_id': assistant_message.id,
            'role': 'assistant',
            'content': ai_response['content'],
            'knowledge_references': ai_response.get('knowledge_references', []),
            'tokens_used': ai_response.get('tokens_used', 0),
            'response_time': ai_response.get('response_time', 0.0)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Conversation.DoesNotExist:
        return Response(
            {'error': '对话不存在'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import logging
        logging.error(f"对话处理失败: {str(e)}")
        return Response(
            {'error': f'对话处理失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_conversation_history(request, conversation_id):
    """清空对话历史（软删除对话）"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # 软删除对话（如果有is_active字段）或物理删除
        # 这里假设模型有is_active字段，如果没有则直接删除
        if hasattr(conversation, 'is_active'):
            conversation.is_active = False
            conversation.save()
        else:
            conversation.delete()
        
        return Response({
            'status': 'success',
            'message': '对话已删除'
        })
        
    except Exception as e:
        return Response(
            {'error': f'删除失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def save_message_view(request):
    """
    保存消息到数据库
    用于流式输出后保存完整的AI回复
    """
    conversation_id = request.data.get('conversation_id')
    role = request.data.get('role')
    content = request.data.get('content')
    
    if not conversation_id or not role or not content:
        return Response(
            {'error': '缺少必要参数'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        # 计算token数量（简单估算：字符数/4）
        tokens_used = max(1, len(content) // 4)
        
        message = Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            tokens_used=tokens_used
        )
        
        return Response({
            'success': True,
            'message_id': message.id
        })
    except Conversation.DoesNotExist:
        return Response(
            {'error': '对话不存在'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'保存失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_conversation_stats(request):
    """获取对话统计"""
    
    stats = {
        'total_conversations': Conversation.objects.count(),
        'active_conversations': Conversation.objects.filter(is_active=True).count(),
        'total_messages': Message.objects.count(),
        'total_tokens': Message.objects.filter(
            role='assistant'
        ).aggregate(total=Sum('tokens_used'))['total'] or 0
    }
    
    return Response(stats)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def chat_stream_view(request):
    """
    流式对话API
    支持实时流式输出AI回复
    """
    from django.http import StreamingHttpResponse
    
    # 获取参数 (兼容GET和POST)
    if request.method == 'GET':
        data = request.GET.dict()
        # 简单验证
        if 'message' not in data:
            return Response({'message': '缺少message参数'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # 验证请求数据
        serializer = ChatRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
    
    # 提取额外参数
    conversation_id = data.get('conversation_id') or data.get('session_id')
    message_content = data.get('message')
    conversation_type = data.get('conversation_type', 'general')
    repository_id = data.get('repository_id')
    knowledge_base_id = data.get('knowledge_base_id')
    
    # 转换ID类型
    if repository_id: repository_id = int(repository_id)
    if knowledge_base_id: knowledge_base_id = int(knowledge_base_id)
    
    def generate_stream():
        """生成流式响应"""
        try:
            # 获取或创建对话
            conversation = None
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                    # 更新对话配置（如果提供了新的）
                    if conversation_type: conversation.conversation_type = conversation_type
                    if repository_id: conversation.repository_id = repository_id
                    if knowledge_base_id: conversation.knowledge_base_id = knowledge_base_id
                    conversation.save()
                except Conversation.DoesNotExist:
                    pass
            
            if not conversation:
                # 创建新对话
                user = request.user if request.user.is_authenticated else None
                if user is None:
                    try:
                        user, _ = get_user_model().objects.get_or_create(
                            username='guest',
                            defaults={'email': 'guest@example.com', 'is_active': True}
                        )
                    except Exception:
                        user = get_user_model().objects.first()
                
                conversation = Conversation.objects.create(
                    title=message_content[:50],
                    user=user,
                    conversation_type=conversation_type,
                    repository_id=repository_id,
                    knowledge_base_id=knowledge_base_id
                )
            
            # 先输出conversation_id作为元数据
            yield f"[CONVERSATION_ID:{conversation.id}]"
            
            # 保存用户消息
            Message.objects.create(
                conversation=conversation,
                role='user',
                content=message_content
            )
            
            # 准备对话历史
            messages = conversation.messages.all().order_by('created_at')
            history = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            # 调用 Service 进行流式对话
            ai_service = AIChatService()
            full_response = ""
            
            for chunk in ai_service.stream_chat(
                messages=history,
                conversation_type=conversation.conversation_type,
                repository_id=conversation.repository_id,
                knowledge_base_id=conversation.knowledge_base_id
            ):
                yield chunk
                full_response += chunk
            
            # 保存AI回复消息
            if full_response:
                Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=full_response
                )
            
            # 发送流结束标记
            yield "[STREAM_DONE]"
            
        except Exception as e:
            yield f"\n[对话处理失败: {str(e)}][STREAM_DONE]"
    
    return StreamingHttpResponse(
        generate_stream(),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )