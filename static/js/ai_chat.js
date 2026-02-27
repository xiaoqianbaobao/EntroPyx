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
        // 强制刷新页面以更新列表（简单粗暴但有效）
        // window.location.reload(); 
        
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
        // showLoading(); // 移除弹窗
        
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
        const titleElement = document.getElementById('currentConversationTitle');
        if (titleElement) titleElement.textContent = conversation.title;
        
        const metaElement = document.getElementById('conversationMeta');
        if (metaElement) metaElement.textContent = `类型: ${conversation.conversation_type} | 更新: ${new Date(conversation.updated_at).toLocaleString()}`;
        
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
        // 确保 messages 是数组
        let messageList = [];
        if (Array.isArray(messages)) {
            messageList = messages;
        } else if (messages.results && Array.isArray(messages.results)) {
            // 处理分页格式 {count: 2, next: null, previous: null, results: [...]}
            messageList = messages.results;
        } else if (messages.data && Array.isArray(messages.data)) {
            // 处理标准API格式 {code: 0, data: [...]}
            messageList = messages.data;
        } else {
            console.error('Messages data is not an array:', messages);
        }
        
        // 按时间正序排列（如果是分页数据，通常是倒序返回的，需要反转）
        // 这里假设后端返回的是正序，或者前端统一处理
        renderMessages(messageList);
        
        // 隐藏空消息提示
        const emptyMessage = document.getElementById('emptyMessage');
        if (emptyMessage) emptyMessage.style.display = 'none';
        
        // 隐藏设置面板
        const settings = document.getElementById('conversationSettings');
        if (settings) settings.style.display = 'none';
        
        // 设置激活状态
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // 尝试找到并激活对应的列表项
        // 注意：onclick 属性匹配可能不稳定，建议使用 data-id 属性
        const activeItem = document.querySelector(`.conversation-item[onclick*="${conversationId}"]`);
        if (activeItem) activeItem.classList.add('active');
        
    } catch (error) {
        console.error('加载对话失败:', error);
        showToast('加载对话失败', 'error');
    } finally {
        // hideLoading(); // 移除弹窗
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
    
    if (isLoading) {
        console.log('Sending blocked: isLoading is true');
        return;
    }
    
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
    console.log('Appending user message:', message);
    appendMessage('user', message);
    
    // 隐藏空消息提示
    const emptyMessage = document.getElementById('emptyMessage');
    if (emptyMessage) emptyMessage.style.display = 'none';
    
    // 显示加载状态
    isLoading = true;
    console.log('Set isLoading = true');
    // showLoading(); // 移除弹窗
    
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
            // 确保发生错误时重置isLoading，允许发送下一条消息
            isLoading = false;
            throw new Error('发送消息失败: ' + response.status + ' ' + errorText);
        }
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        let conversationId = null;
        
        aiContentDiv.innerHTML = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                // 流结束时，显式重置isLoading
                console.log('Stream done (in loop), set isLoading = false');
                isLoading = false;
                break;
            }
            
            const chunk = decoder.decode(value);
            
            // 检查是否包含conversation_id元数据
            const conversationIdMatch = chunk.match(/\[CONVERSATION_ID:(\d+)\]/);
            
            // 检查是否包含结束标记
            if (chunk.includes('[STREAM_DONE]')) {
                console.log('Received [STREAM_DONE] signal');
                isLoading = false;
                
                // 移除结束标记和ID标记
                let cleanChunk = chunk.replace('[STREAM_DONE]', '');
                if (conversationIdMatch) {
                    conversationId = parseInt(conversationIdMatch[1]);
                    cleanChunk = cleanChunk.replace(/\[CONVERSATION_ID:\d+\]/, '');
                }
                
                // 处理步骤更新事件
                if (cleanChunk.includes('[STEP_UPDATE]:')) {
                    const stepMatch = cleanChunk.match(/\[STEP_UPDATE\]: ({.*?})(?=\[|$)/);
                    if (stepMatch) {
                        try {
                            const stepData = JSON.parse(stepMatch[1]);
                            // 这里可以调用函数更新步骤UI，目前简单追加到文本中
                            cleanChunk = cleanChunk.replace(stepMatch[0], `\n> **[步骤 ${stepData.id}] ${stepData.title}**: ${stepData.status}\n`);
                        } catch (e) {
                            console.error('Failed to parse step update', e);
                        }
                    }
                }
                
                // 处理思考过程
                if (cleanChunk.includes('[THOUGHT]:')) {
                     cleanChunk = cleanChunk.replace(/\[THOUGHT\]: (.*?)(?=\[|$|\n)/g, '\n> *🤔 思考: $1*\n');
                }
                
                fullContent += cleanChunk;
                aiContentDiv.innerHTML = '<p>' + formatMarkdown(fullContent) + '</p>';
                scrollToBottom();
                break;
            }
            
            if (conversationIdMatch) {
                conversationId = parseInt(conversationIdMatch[1]);
                // 移除元数据行
                let cleanChunk = chunk.replace(/\[CONVERSATION_ID:\d+\]/, '');
                
                // 实时处理流中的特殊标记
                 if (cleanChunk.includes('[STEP_UPDATE]:')) {
                    const parts = cleanChunk.split('[STEP_UPDATE]:');
                    cleanChunk = parts[0]; // 保留前半部分
                    // 简单的处理：将步骤信息转换为 Markdown 引用
                    for(let i=1; i<parts.length; i++) {
                        try {
                            // 尝试提取 JSON
                            const jsonStr = parts[i].trim();
                            // 这是一个简化的处理，实际流中 JSON 可能会被截断，需要更复杂的 buffer 处理
                            // 这里假设 chunk 包含了完整的 json
                            if (jsonStr.startsWith('{') && jsonStr.includes('}')) {
                                const jsonEnd = jsonStr.indexOf('}') + 1;
                                const jsonContent = jsonStr.substring(0, jsonEnd);
                                const stepData = JSON.parse(jsonContent);
                                const statusIcon = stepData.status === 'success' ? '✅' : stepData.status === 'error' ? '❌' : '⏳';
                                cleanChunk += `\n> ${statusIcon} **步骤 ${stepData.id}: ${stepData.title}**\n`;
                                cleanChunk += jsonStr.substring(jsonEnd);
                            } else {
                                cleanChunk += parts[i];
                            }
                        } catch(e) {
                            cleanChunk += parts[i];
                        }
                    }
                }

                if (cleanChunk.includes('[THOUGHT]:')) {
                     cleanChunk = cleanChunk.replace(/\[THOUGHT\]: (.*?)(?=\[|$|\n)/g, '\n> *🤔 思考: $1*\n');
                }

                fullContent += cleanChunk;
            } else {
                let cleanChunk = chunk;
                // 实时处理流中的特殊标记 (重复逻辑，待优化为函数)
                 if (cleanChunk.includes('[STEP_UPDATE]:')) {
                    // 简化处理，直接替换
                    cleanChunk = cleanChunk.replace(/\[STEP_UPDATE\]: ({.*?})/g, (match, p1) => {
                        try {
                            const stepData = JSON.parse(p1);
                            const statusIcon = stepData.status === 'success' ? '✅' : stepData.status === 'error' ? '❌' : '⏳';
                            return `\n> ${statusIcon} **步骤 ${stepData.id}: ${stepData.title}**\n`;
                        } catch (e) { return match; }
                    });
                }
                
                if (cleanChunk.includes('[THOUGHT]:')) {
                     cleanChunk = cleanChunk.replace(/\[THOUGHT\]: (.*?)(?=\[|$|\n)/g, '\n> *🤔 思考: $1*\n');
                }
                
                fullContent += cleanChunk;
            }
            
            // 更新显示
            aiContentDiv.innerHTML = '<p>' + formatMarkdown(fullContent) + '</p>';
            scrollToBottom();
        }
        
        console.log('完整响应:', fullContent);
        console.log('对话ID:', conversationId);
        
        // 更新当前对话ID
        if (!currentConversationId && conversationId) {
            currentConversationId = conversationId;
            
            // 更新标题
            document.getElementById('currentConversationTitle').textContent = 
                message.length > 20 ? message.substring(0, 20) + '...' : message;
            
            // 隐藏设置面板
            document.getElementById('conversationSettings').style.display = 'none';
        }

        // 成功完成后，重置isLoading状态，允许发送下一条消息
        console.log('Stream finished, set isLoading = false');
        isLoading = false;
        
    } catch (error) {
        console.error('发送消息失败:', error);
        console.error('错误详情:', error.message, error.stack);
        showToast('发送消息失败: ' + error.message, 'error');
        
        // 显示错误消息
        // 如果aiContentDiv已经存在，更新它而不是追加新消息
        const lastMessage = document.getElementById('messageArea').lastElementChild;
        if (lastMessage && lastMessage.classList.contains('message-assistant') && lastMessage.querySelector('.message-content').textContent.trim() === '正在思考...') {
             lastMessage.querySelector('.message-content').innerHTML = `<p>抱歉，消息发送失败: ${error.message}</p>`;
        } else {
             appendMessage('assistant', `抱歉，消息发送失败: ${error.message}`);
        }
        
        // 如果是用户未登录错误，提示用户
        if (error.message.includes('UNAUTHORIZED') || error.message.includes('401')) {
            appendMessage('assistant', '请先登录后使用AI聊天功能。');
        }
    } finally {
        // 确保无论成功还是失败，都重置isLoading状态
        console.log('Finally block: set isLoading = false');
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
    
    if (!confirm('确定要删除当前对话吗？')) {
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
            throw new Error('删除失败');
        }
        
        // 从侧边栏移除该对话项
        const sidebarItem = document.querySelector(`.conversation-item[onclick*="${currentConversationId}"]`);
        if (sidebarItem) {
            sidebarItem.remove();
        }
        
        // 重置为新建对话状态
        newConversation();
        
        showToast('对话已删除', 'success');
        
    } catch (error) {
        console.error('删除失败:', error);
        showToast('删除失败: ' + error.message, 'error');
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
