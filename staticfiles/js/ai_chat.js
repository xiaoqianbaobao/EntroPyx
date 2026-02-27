/**
 * AI对话前端逻辑
 */

// 全局变量
let currentConversationId = null;
let isLoading = false;

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    // 绑定键盘事件
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            // Shift+Enter换行，Enter发送
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage(e);
            }
        });
    }
    
    // 加载对话列表
    loadConversationList();
    
    // 初始化新建对话状态
    newConversation();
    
    console.log('AI Chat initialized');
});

/**
 * 新建对话
 */
function newConversation() {
    console.log('newConversation called');
    
    // 重置当前对话
    currentConversationId = null;
    
    // 清空消息区域并显示空消息
    const messageArea = document.getElementById('messageArea');
    if (messageArea) {
        messageArea.innerHTML = `
            <div class="text-center text-muted py-5" id="emptyMessage">
                <i class="bi bi-robot" style="font-size: 3rem; color: #adb5bd;"></i>
                <p class="mt-3 mb-4 fs-5 fw-light" style="color: #6c757d;">AI 智能助手</p>
                <p class="text-secondary mb-4">随时为您提供代码评审、PRD分析、测试用例等专业建议</p>
            </div>
        `;
    }
    
    // 重置标题
    const titleElement = document.getElementById('currentConversationTitle');
    if (titleElement) {
        titleElement.textContent = '新建对话';
    }
    
    const metaElement = document.getElementById('conversationMeta');
    if (metaElement) {
        metaElement.textContent = '';
    }
    
    // 清空输入框
    const inputElement = document.getElementById('messageInput');
    if (inputElement) {
        inputElement.value = '';
    }
    
    // 显示设置面板
    const settingsElement = document.getElementById('conversationSettings');
    if (settingsElement) {
        settingsElement.style.display = 'block';
        console.log('Settings panel displayed');
    } else {
        console.error('conversationSettings element not found');
    }
    
    // 移除所有对话项的激活状态
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 聚焦到输入框
    if (inputElement) {
        inputElement.focus();
    }
}

/**
 * 加载对话列表
 */
async function loadConversationList() {
    try {
        const response = await fetch('/ai-chat/api/conversations/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (!response.ok) {
            throw new Error('加载对话列表失败');
        }
        
        const conversations = await response.json();
        
        // 更新对话列表（这里可以优化为增量更新）
        // 暂时不做处理，因为Django模板已经渲染了初始列表
        
    } catch (error) {
        console.error('加载对话列表失败:', error);
        showToast('加载对话列表失败', 'error');
    }
}

/**
 * 加载指定对话
 */
async function loadConversation(conversationId) {
    if (isLoading) return;
    
    isLoading = true;
    currentConversationId = conversationId;
    
    try {
        // 显示加载状态
        showLoading();
        
        // 获取对话详情
        const conversationResponse = await fetch(`/ai-chat/api/conversations/${conversationId}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (!conversationResponse.ok) {
            throw new Error('加载对话失败');
        }
        
        const conversation = await conversationResponse.json();
        
        // 更新标题
        document.getElementById('currentConversationTitle').textContent = conversation.title;
        document.getElementById('conversationMeta').textContent = 
            `类型: ${conversation.conversation_type} | 更新: ${new Date(conversation.updated_at).toLocaleString()}`;
        
        // 获取消息列表
        const messagesResponse = await fetch(`/ai-chat/api/conversations/${conversationId}/messages/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (!messagesResponse.ok) {
            throw new Error('加载消息失败');
        }
        
        const messages = await messagesResponse.json();
        
        // 渲染消息
        renderMessages(messages);
        
        // 隐藏空消息提示
        document.getElementById('emptyMessage').style.display = 'none';
        
        // 隐藏设置面板
        document.getElementById('conversationSettings').style.display = 'none';
        
        // 设置激活状态
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[onclick="loadConversation(${conversationId})"]`).classList.add('active');
        
    } catch (error) {
        console.error('加载对话失败:', error);
        showToast('加载对话失败', 'error');
    } finally {
        hideLoading();
        isLoading = false;
    }
}

/**
 * 渲染消息列表
 */
function renderMessages(messages) {
    const messageArea = document.getElementById('messageArea');
    messageArea.innerHTML = '';
    
    messages.forEach(message => {
        appendMessage(message.role, message.content, message.knowledge_references);
    });
    
    // 滚动到底部
    scrollToBottom();
}

/**
 * 发送消息
 */
async function sendMessage(event) {
    event.preventDefault();
    
    if (isLoading) return;
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // 清空输入框
    messageInput.value = '';
    
    // 如果是新建对话，获取设置
    let conversationType = 'general';
    let knowledgeBaseId = null;
    let repositoryId = null;
    
    if (!currentConversationId) {
        conversationType = document.getElementById('conversationType').value;
        knowledgeBaseId = document.getElementById('knowledgeBaseSelect').value || null;
        repositoryId = document.getElementById('repositorySelect').value || null;
    }
    
    // 显示用户消息
    appendMessage('user', message);
    
    // 隐藏空消息提示
    document.getElementById('emptyMessage').style.display = 'none';
    
    // 显示加载状态
    isLoading = true;
    showLoading();
    
    try {
        // 准备请求数据
        const requestData = {
            message: message,
            conversation_type: conversationType
        };
        
        if (currentConversationId) {
            requestData.conversation_id = currentConversationId;
        }
        
        if (knowledgeBaseId) {
            requestData.knowledge_base_id = parseInt(knowledgeBaseId);
        }
        
        if (repositoryId) {
            requestData.repository_id = parseInt(repositoryId);
        }
        
        // 发送请求
        console.log('发送请求到:', '/ai-chat/api/chat/stream/');
        console.log('请求数据:', requestData);
        
        // 创建AI消息容器
        const aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = 'message message-assistant';
        const aiContentDiv = document.createElement('div');
        aiContentDiv.className = 'message-content';
        aiContentDiv.innerHTML = '<p>正在思考...</p>';
        aiMessageDiv.appendChild(aiContentDiv);
        messageArea.appendChild(aiMessageDiv);
        scrollToBottom();
        
        // 使用流式API
        const response = await fetch('/ai-chat/api/chat/stream/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('响应状态:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('响应错误:', errorText);
            aiContentDiv.innerHTML = `<p>抱歉，消息发送失败: ${response.status} ${errorText}</p>`;
            throw new Error('发送消息失败: ' + response.status + ' ' + errorText);
        }
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        
        aiContentDiv.innerHTML = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const chunk = decoder.decode(value);
            fullContent += chunk;
            
            // 更新显示
            aiContentDiv.innerHTML = '<p>' + formatMarkdown(fullContent) + '</p>';
            scrollToBottom();
        }
        
        console.log('完整响应:', fullContent);
        
        // 保存完整回复到数据库
        if (fullContent) {
            try {
                await fetch('/ai-chat/api/save_message/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        conversation_id: currentConversationId || result.conversation_id,
                        role: 'assistant',
                        content: fullContent
                    })
                });
            } catch (e) {
                console.error('保存消息失败:', e);
            }
        }
        
        // 更新当前对话ID
        if (!currentConversationId) {
            currentConversationId = result.conversation_id;
            
            // 更新标题
            document.getElementById('currentConversationTitle').textContent = 
                message.length > 20 ? message.substring(0, 20) + '...' : message;
            
            // 隐藏设置面板
            document.getElementById('conversationSettings').style.display = 'none';
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        console.error('错误详情:', error.message, error.stack);
        showToast('发送消息失败: ' + error.message, 'error');
        
        // 显示错误消息
        appendMessage('assistant', `抱歉，消息发送失败: ${error.message}`);
        
        // 如果是用户未登录错误，提示用户
        if (error.message.includes('UNAUTHORIZED') || error.message.includes('401')) {
            appendMessage('assistant', '请先登录后使用AI聊天功能。');
        }
    } finally {
        try {
            hideLoading();
        } catch (e) {
            console.error('隐藏加载状态失败:', e);
        }
        isLoading = false;
    }
}

/**
 * 添加消息到对话区域
 */
function appendMessage(role, content, knowledgeReferences = null) {
    const messageArea = document.getElementById('messageArea');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // 处理Markdown格式（简单实现）
    let formattedContent = content
        .replace(/\n\n/g, '</p><p>')  // 段落
        .replace(/\n/g, '<br>')      // 换行
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')  // 代码块
        .replace(/`([^`]+)`/g, '<code>$1</code>')  // 行内代码
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // 粗体
        .replace(/\*(.+?)\*/g, '<em>$1</em>');  // 斜体
    
    contentDiv.innerHTML = `<p>${formattedContent}</p>`;
    
    // 添加知识库引用
    if (knowledgeReferences && knowledgeReferences.length > 0) {
        const referenceDiv = document.createElement('div');
        referenceDiv.className = 'knowledge-reference';
        referenceDiv.innerHTML = '<strong>📚 知识库引用:</strong><br>' + 
            knowledgeReferences.map(ref => `• ${ref.title}`).join('<br>');
        contentDiv.appendChild(referenceDiv);
    }
    
    messageDiv.appendChild(contentDiv);
    messageArea.appendChild(messageDiv);
    
    // 滚动到底部
    scrollToBottom();
}

/**
 * 清空当前对话
 */
async function clearCurrentConversation() {
    if (!currentConversationId) {
        // 清空消息区域
        const messageArea = document.getElementById('messageArea');
        messageArea.innerHTML = `
            <div class="text-center text-muted mt-5" id="emptyMessage">
                <i class="bi bi-chat-dots" style="font-size: 3rem;"></i>
                <p class="mt-3">开始与AI助手对话吧！</p>
                <p class="small">支持代码评审、PRD分析、测试用例生成等多种场景</p>
            </div>
        `;
        return;
    }
    
    if (!confirm('确定要清空当前对话的所有消息吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/ai-chat/api/conversations/${currentConversationId}/clear/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (!response.ok) {
            throw new Error('清空失败');
        }
        
        // 清空消息区域
        const messageArea = document.getElementById('messageArea');
        messageArea.innerHTML = `
            <div class="text-center text-muted mt-5" id="emptyMessage">
                <i class="bi bi-chat-dots" style="font-size: 3rem;"></i>
                <p class="mt-3">开始与AI助手对话吧！</p>
                <p class="small">支持代码评审、PRD分析、测试用例生成等多种场景</p>
            </div>
        `;
        
        showToast('对话历史已清空', 'success');
        
    } catch (error) {
        console.error('清空失败:', error);
        showToast('清空失败: ' + error.message, 'error');
    }
}

/**
 * 保存对话
 */
function saveConversation() {
    if (!currentConversationId) {
        showToast('请先发送一条消息', 'warning');
        return;
    }
    
    showToast('对话已保存', 'success');
}

/**
 * 筛选对话
 */
function filterConversations() {
    const filterValue = document.getElementById('conversationTypeFilter').value;
    const conversationItems = document.querySelectorAll('.conversation-item');
    
    conversationItems.forEach(item => {
        if (!filterValue || item.dataset.type === filterValue) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
    const messageArea = document.getElementById('messageArea');
    messageArea.scrollTop = messageArea.scrollHeight;
}

/**
 * 显示加载状态
 */
function showLoading() {
    try {
        const modalElement = document.getElementById('loadingModal');
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        } else {
            console.error('loadingModal元素不存在');
        }
    } catch (error) {
        console.error('显示加载状态失败:', error);
        // 如果模态框无法显示，至少记录日志
    }
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
    if (modal) {
        modal.hide();
    }
}

/**
 * 显示提示消息
 */
function showToast(message, type = 'info') {
    // 创建toast元素
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // 添加到页面
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    toastContainer.innerHTML = toastHtml;
    document.body.appendChild(toastContainer);
    
    // 显示toast
    const toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
    
    // 自动移除
    setTimeout(() => {
        toastContainer.remove();
    }, 5000);
}

/**
 * 格式化Markdown文本
 */
function formatMarkdown(text) {
    if (!text) return '';
    
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

/**
 * 获取CSRF Token
 */
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookieValue ? cookieValue.split('=')[1] : '';
}
