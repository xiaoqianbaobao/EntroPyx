/**
 * MeetingRecorder - 会议录音器
 * 提供实时录音、WebSocket连接、转写等功能
 */
class MeetingRecorder {
    constructor(options = {}) {
        this.apiBaseUrl = options.apiBaseUrl || '/meeting-assistant/api/';
        this.repositoryId = options.repositoryId || null;
        this.onStart = options.onStart || function() {};
        this.onStop = options.onStop || function() {};
        this.onError = options.onError || function() {};
        
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.socket = null;
        this.isRecording = false;
    }

    /**
     * 初始化录音器
     */
    async init() {
        try {
            // 检查浏览器支持
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('您的浏览器不支持录音功能');
            }

            // 请求麦克风权限
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // 停止测试流，只是为了获取权限
            stream.getTracks().forEach(track => track.stop());
            
            return true;
        } catch (error) {
            this.onError('初始化失败: ' + error.message);
            console.error('录音器初始化失败:', error);
            return false;
        }
    }

    /**
     * 开始录音
     */
    async startRecording() {
        if (this.isRecording) {
            console.warn('录音已在进行中');
            return;
        }

        try {
            // 获取音频流
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // 创建MediaRecorder
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: this.getSupportedMimeType()
            });

            this.audioChunks = [];

            // 收集音频数据
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            // 录音停止事件
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { 
                    type: this.mediaRecorder.mimeType 
                });
                
                // 停止音频流
                stream.getTracks().forEach(track => track.stop());
                
                this.isRecording = false;
                this.onStop(audioBlob);
            };

            // 开始录音
            this.mediaRecorder.start(1000); // 每秒收集一次数据
            this.isRecording = true;
            
            this.onStart();
            
            console.log('录音开始');
        } catch (error) {
            this.onError('启动录音失败: ' + error.message);
            console.error('启动录音失败:', error);
            throw error;
        }
    }

    /**
     * 停止录音
     */
    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            console.warn('没有正在进行的录音');
            return;
        }

        try {
            this.mediaRecorder.stop();
            console.log('录音停止');
        } catch (error) {
            this.onError('停止录音失败: ' + error.message);
            console.error('停止录音失败:', error);
            throw error;
        }
    }

    /**
     * 获取支持的音频格式
     */
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
            'audio/mp4',
            'audio/wav'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return 'audio/webm'; // 默认格式
    }

    /**
     * 上传录音文件
     */
    async uploadRecording(audioBlob, title, meetingDate = null, participants = '') {
        if (!audioBlob) {
            throw new Error('没有录音文件');
        }

        if (!this.repositoryId) {
            throw new Error('未选择仓库');
        }

        const formData = new FormData();
        formData.append('repository_id', this.repositoryId);
        formData.append('audio_file', audioBlob, `recording_${Date.now()}.webm`);
        formData.append('meeting_title', title);
        
        if (meetingDate) {
            formData.append('meeting_date', meetingDate);
        }
        
        if (participants) {
            formData.append('participants', participants);
        }

        try {
            const csrfToken = this.getCsrfToken();
            
            const response = await fetch(this.apiBaseUrl + 'recordings/upload/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                credentials: 'same-origin',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || errorData.detail || '上传失败');
            }

            return await response.json();
            
        } catch (error) {
            console.error('上传录音失败:', error);
            throw error;
        }
    }

    /**
     * 获取CSRF Token
     */
    getCsrfToken() {
        // 从cookie中获取
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        
        // 从meta标签获取
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // 从隐藏input获取
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) {
            return input.value;
        }
        
        return '';
    }

    /**
     * 连接WebSocket进行实时转写
     */
    connectWebSocket(recordingId) {
        const wsUrl = `ws://${window.location.host}/ws/meeting-assistant/${recordingId}/`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('WebSocket连接已建立');
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'transcript') {
                // 处理转写结果
                if (this.onTranscript) {
                    this.onTranscript(data);
                }
            } else if (data.type === 'error') {
                console.error('WebSocket错误:', data.message);
                if (this.onError) {
                    this.onError(data.message);
                }
            }
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket错误:', error);
        };
        
        this.socket.onclose = () => {
            console.log('WebSocket连接已关闭');
        };
    }

    /**
     * 发送音频数据到WebSocket
     */
    sendAudioData(audioBlob) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const reader = new FileReader();
            reader.onload = () => {
                this.socket.send(JSON.stringify({
                    type: 'audio',
                    data: reader.result
                }));
            };
            reader.readAsDataURL(audioBlob);
        }
    }

    /**
     * 断开WebSocket连接
     */
    disconnectWebSocket() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    /**
     * 销毁录音器
     */
    destroy() {
        if (this.isRecording) {
            this.stopRecording();
        }
        
        this.disconnectWebSocket();
        
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
    }
}

// 导出供全局使用
if (typeof window !== 'undefined') {
    window.MeetingRecorder = MeetingRecorder;
}