"""
WebSocket消费者
Meeting Assistant WebSocket Consumers
"""
import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class RealtimeTranscribeConsumer(AsyncWebsocketConsumer):
    """实时转写WebSocket消费者"""
    
    async def connect(self):
        """建立WebSocket连接"""
        await self.accept()
        self.is_processing = False
        self.transcript_buffer = []
        
        logger.info("WebSocket client connected")
        
        # 发送连接成功消息
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': 'WebSocket连接成功'
        }))
    
    async def disconnect(self, close_code):
        """断开WebSocket连接"""
        logger.info(f"WebSocket client disconnected with code: {close_code}")
        self.is_processing = False
    
    async def receive(self, text_data=None, bytes_data=None):
        """接收消息"""
        if text_data:
            # 处理文本消息
            data = json.loads(text_data)
            await self.handle_text_message(data)
        elif bytes_data:
            # 处理音频数据
            await self.handle_audio_data(bytes_data)
    
    async def handle_text_message(self, data):
        """处理文本消息"""
        message_type = data.get('type')
        
        if message_type == 'start_recording':
            # 开始录音
            self.is_processing = True
            self.transcript_buffer = []
            
            await self.send(text_data=json.dumps({
                'type': 'recording_started',
                'message': '开始录音和转写'
            }))
            
        elif message_type == 'stop_recording':
            # 停止录音
            self.is_processing = False
            
            # 发送完整的转写结果
            await self.send(text_data=json.dumps({
                'type': 'recording_stopped',
                'message': '录音停止',
                'full_transcript': self.transcript_buffer
            }))
            
        elif message_type == 'ping':
            # 心跳检测
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'message': 'pong'
            }))
    
    async def handle_audio_data(self, bytes_data):
        """处理音频数据"""
        if not self.is_processing:
            return
        
        try:
            # 模拟实时转写
            # 在实际应用中，这里应该调用ASR服务进行实时转写
            transcript = await self.simulate_realtime_transcription()
            
            if transcript:
                # 发送转写结果
                await self.send(text_data=json.dumps({
                    'type': 'transcript',
                    'speaker': transcript['speaker'],
                    'text': transcript['text'],
                    'timestamp': transcript['timestamp']
                }))
                
                # 添加到缓冲区
                self.transcript_buffer.append(transcript)
                
        except Exception as e:
            logger.error(f"Error processing audio data: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'处理音频失败: {str(e)}'
            }))
    
    async def simulate_realtime_transcription(self):
        """
        模拟实时转写
        注意: 这是一个演示版本，实际使用应该集成真实的ASR服务
        """
        # 模拟一些转写结果
        # 在实际应用中，应该调用FunASR或其他ASR服务的实时转写API
        import random
        
        # 随机返回一些示例文本
        sample_texts = [
            "大家好，今天我们进行代码评审会议。",
            "我先介绍一下这个PR的主要功能。",
            "我看过代码，有几个地方需要改进。",
            "建议添加更多的单元测试。",
            "好的，我会根据大家的意见进行修改。",
            "会议到此结束，谢谢大家。"
        ]
        
        # 只有10%的概率返回转写结果，模拟真实的实时转写频率
        if random.random() < 0.1:
            speaker = random.choice(['spk0', 'spk1', 'spk2'])
            text = random.choice(sample_texts)
            
            return {
                'speaker': speaker,
                'text': text,
                'timestamp': asyncio.get_event_loop().time()
            }
        
        return None