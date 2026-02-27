"""
ASR服务封装
Automatic Speech Recognition Service

注意: 这是一个简化版本，实际使用需要集成FunASR、讯飞语音或其他ASR服务
"""
import logging

logger = logging.getLogger(__name__)


class ASRService:
    """ASR服务基类"""
    
    def __init__(self):
        self.name = "Base ASR Service"
    
    def transcribe(self, audio_path, language='zh'):
        """
        转写音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言，默认中文
        
        Returns:
            List[dict]: 转写结果列表
        """
        raise NotImplementedError("Subclass must implement this method")
    
    def transcribe_with_diarization(self, audio_path, language='zh'):
        """
        转写音频并进行说话人分离
        
        Args:
            audio_path: 音频文件路径
            language: 语言，默认中文
        
        Returns:
            List[dict]: [
                {
                    'speaker': 'spk0',
                    'text': '转写内容',
                    'start_time': 0.0,
                    'end_time': 5.2,
                    'confidence': 0.95
                },
                ...
            ]
        """
        raise NotImplementedError("Subclass must implement this method")


class MockASRService(ASRService):
    """模拟ASR服务（用于测试和演示）"""
    
    def __init__(self):
        super().__init__()
        self.name = "Mock ASR Service"
    
    def transcribe(self, audio_path, language='zh'):
        """模拟转写"""
        logger.info(f"Mock transcribing audio: {audio_path}")
        return [{
            'text': '这是一个模拟的转写结果',
            'start_time': 0.0,
            'end_time': 10.0,
            'confidence': 0.9
        }]
    
    def transcribe_with_diarization(self, audio_path, language='zh'):
        """模拟转写+说话人分离"""
        logger.info(f"Mock transcribing with diarization: {audio_path}")
        
        # 返回模拟数据
        return [
            {
                'speaker': 'spk0',
                'text': '大家好，今天我们进行代码评审会议。',
                'start_time': 0.0,
                'end_time': 5.2,
                'confidence': 0.95
            },
            {
                'speaker': 'spk1',
                'text': '我先介绍一下这个PR的主要功能。',
                'start_time': 5.5,
                'end_time': 10.3,
                'confidence': 0.93
            },
            {
                'speaker': 'spk0',
                'text': '有几个地方需要改进。',
                'start_time': 10.8,
                'end_time': 15.1,
                'confidence': 0.92
            }
        ]


class FunASRService(ASRService):
    """
    FunASR服务封装
    需要安装: pip install funasr
    
    注意: 这是一个示例，实际使用需要下载和配置FunASR模型
    """
    
    def __init__(self):
        super().__init__()
        self.name = "FunASR Service"
        self.model = None
    
    def _load_model(self):
        """加载FunASR模型"""
        if self.model is not None:
            return
        
        try:
            from funasr import AutoModel
            
            # 加载模型
            self.model = AutoModel(
                model="paraformer-zh",  # 语音识别模型
                model_revision="v2.0.4",
                vad_model="fsmn-vad",   # 语音活动检测
                vad_model_revision="v2.0.4",
                punc_model="ct-punc",   # 标点预测
                punc_model_revision="v2.0.4",
                spk_model="cam++",      # 说话人分离
                spk_model_revision="v2.0.2"
            )
            
            logger.info("FunASR model loaded successfully")
            
        except ImportError:
            logger.warning("FunASR not installed, falling back to mock service")
            raise ImportError("Please install funasr: pip install funasr")
        except Exception as e:
            logger.error(f"Failed to load FunASR model: {str(e)}")
            raise
    
    def transcribe_with_diarization(self, audio_path, language='zh'):
        """使用FunASR进行转写+说话人分离"""
        try:
            self._load_model()
            
            # 调用FunASR
            result = self.model.generate(
                input=audio_path,
                batch_size_s=300,
                hotword='',  # 可添加热词
            )
            
            transcripts = []
            for item in result:
                if 'text' in item:
                    transcripts.append({
                        'speaker': item.get('spk', 'unknown'),
                        'text': item['text'],
                        'start_time': item.get('timestamp', [0, 0])[0] / 1000,
                        'end_time': item.get('timestamp', [0, 0])[1] / 1000,
                        'confidence': item.get('confidence', 0.0)
                    })
            
            logger.info(f"FunASR transcribed {len(transcripts)} segments")
            return transcripts
            
        except Exception as e:
            logger.error(f"FunASR transcription failed: {str(e)}")
            raise


def get_asr_service(service_type='mock'):
    """
    获取ASR服务实例
    
    Args:
        service_type: 服务类型 ('mock', 'funasr')
    
    Returns:
        ASRService实例
    """
    if service_type == 'funasr':
        try:
            return FunASRService()
        except:
            logger.warning("FunASR not available, falling back to mock")
            return MockASRService()
    else:
        return MockASRService()