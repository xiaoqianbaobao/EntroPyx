/**
 * 会议录音器 - 简化版（不依赖WebSocket）
 * Meeting Recorder - Simplified Version (No WebSocket dependency)
 */
class MeetingRecorder {
    constructor(options = {}) {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordingTime = 0;
        this.recordingInterval = null;
        
        // 配置
        this.meetingId = options.meetingId || null;
        this.repositoryId = options.repositoryId || null;
        this.apiBaseUrl = options.apiUrl || '/meeting-assistant/api/';
        
        // 回调函数
        this.onStart = options.onStart || (() => {});
        this.onStop = options.onStop || (() => {});
        this.onError = options.onError || ((error) => console.error(error));
        this.onProgress = options.onProgress || ((progress) => {});
    }
    
    /**
     * 初始化录音器
     */
    async init() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            this.stream = stream;
            console.log('麦克风初始化成功');
            return true;
        } catch (error) {
            this.onError('无法访问麦克风: ' + error.message);
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
            // 初始化录音器
            const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4';
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: mimeType,
                audioBitsPerSecond: 128000
            });
            
            this.audioChunks = [];
            
            // 处理数据块
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            // 录音停止处理
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: mimeType });
                this.onStop(audioBlob);
            };
            
            // 开始录音
            this.mediaRecorder.start(1000); // 每秒收集一次数据
            this.isRecording = true;
            this.recordingTime = 0;
            
            // 更新计时器
            this.recordingInterval = setInterval(() => {
                this.recordingTime++;
                this.updateTimerDisplay();
            }, 1000);
            
            this.onStart();
            console.log('录音开始');
            
        } catch (error) {
            this.onError('启动录音失败: ' + error.message);
        }
    }
    
    /**
     * 停止录音
     */
    stopRecording() {
        if (!this.isRecording) {
            console.warn('没有正在进行的录音');
            return;
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        this.isRecording = false;
        
        // 停止计时器
        if (this.recordingInterval) {
            clearInterval(this.recordingInterval);
            this.recordingInterval = null;
        }
        
        console.log('录音停止');
    }
    
    /**
     * 更新计时器显示
     */
    updateTimerDisplay() {
        const hours = Math.floor(this.recordingTime / 3600);
        const minutes = Math.floor((this.recordingTime % 3600) / 60);
        const seconds = this.recordingTime % 60;
        
        const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent = timeString;
        }
        
        // 触发进度回调
        this.onProgress({
            duration: this.recordingTime,
            timeString: timeString
        });
    }
    
    /**
     * 上传录音文件
     */
    async uploadRecording(audioBlob, title = '会议录音') {
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
        
        try {
            // 获取CSRF token
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
            
            const data = await response.json();
            console.log('录音上传成功:', data);
            return data;
            
        } catch (error) {
            console.error('上传录音失败:', error);
            throw error;
        }
    }
    
    /**
     * 获取CSRF token
     */
    getCsrfToken() {
        // 从cookie中获取CSRF token
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        
        // 尝试从meta标签获取
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // 尝试从输入框获取
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return '';
    }
    
    /**
     * 释放资源
     */
    cleanup() {
        this.stopRecording();
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        this.mediaRecorder = null;
        this.audioChunks = [];
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('start-record');
    const stopBtn = document.getElementById('stop-record');
    const uploadBtn = document.getElementById('upload-record');
    const statusDiv = document.getElementById('recording-status');
    
    if (!startBtn) return;
    
    // 获取仓库ID
    const repositorySelect = document.getElementById('repository-select');
    let repositoryId = repositorySelect ? repositorySelect.value : null;
    
    if (repositorySelect) {
        repositorySelect.addEventListener('change', function() {
            repositoryId = this.value;
        });
    }
    
    // 初始化录音器
    const recorder = new MeetingRecorder({
        repositoryId: repositoryId,
        onStart: () => {
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
            if (statusDiv) {
                statusDiv.textContent = '录音中...';
                statusDiv.className = 'alert alert-info';
            }
        },
        onStop: (audioBlob) => {
            if (startBtn) startBtn.disabled = false;
            if (stopBtn) stopBtn.disabled = true;
            if (statusDiv) {
                statusDiv.textContent = '录音完成，准备上传...';
                statusDiv.className = 'alert alert-warning';
            }
            
            // 自动上传
            if (audioBlob && repositoryId) {
                recorder.uploadRecording(audioBlob, '会议录音')
                    .then(data => {
                        if (statusDiv) {
                            statusDiv.textContent = '上传成功！正在处理...';
                            statusDiv.className = 'alert alert-success';
                        }
                        
                        // 3秒后跳转到会议详情页
                        setTimeout(() => {
                            if (data.recording_id) {
                                window.location.href = `/meeting-assistant/detail/${data.recording_id}/`;
                            }
                        }, 3000);
                    })
                    .catch(error => {
                        if (statusDiv) {
                            statusDiv.textContent = '上传失败: ' + error.message;
                            statusDiv.className = 'alert alert-danger';
                        }
                    });
            }
        },
        onError: (error) => {
            console.error('录音错误:', error);
            if (statusDiv) {
                statusDiv.textContent = '错误: ' + error;
                statusDiv.className = 'alert alert-danger';
            }
        }
    });
    
    // 初始化麦克风
    recorder.init().then(success => {
        if (!success) {
            if (statusDiv) {
                statusDiv.textContent = '无法访问麦克风，请检查权限设置';
                statusDiv.className = 'alert alert-danger';
            }
        }
    });
    
    // 绑定事件
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            if (!repositoryId) {
                alert('请先选择仓库');
                return;
            }
            recorder.startRecording();
        });
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            recorder.stopRecording();
        });
    }
    
    // 手动上传按钮（如果有的话）
    if (uploadBtn) {
        uploadBtn.addEventListener('click', async () => {
            const fileInput = document.getElementById('audio-file-input');
            if (!fileInput || !fileInput.files.length) {
                alert('请选择音频文件');
                return;
            }
            
            if (!repositoryId) {
                alert('请先选择仓库');
                return;
            }
            
            try {
                const formData = new FormData();
                formData.append('repository_id', repositoryId);
                formData.append('audio_file', fileInput.files[0]);
                formData.append('title', '上传的会议录音');
                
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
                
                const response = await fetch('/meeting-assistant/api/recordings/upload/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                    },
                    credentials: 'same-origin',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    alert('上传成功！');
                    window.location.href = `/meeting-assistant/detail/${data.recording_id}/`;
                } else {
                    const errorData = await response.json();
                    alert('上传失败: ' + (errorData.error || errorData.detail || '未知错误'));
                }
            } catch (error) {
                alert('上传失败: ' + error.message);
            }
        });
    }
});