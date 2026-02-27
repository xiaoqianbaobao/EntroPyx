from celery import shared_task
import logging
from .models import KnowledgeDocument, DocumentChunk, ChunkStatus
from .rag import RAGEngine

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def embed_document_task(self, document_id: int):
    """
    文档向量化任务
    
    Args:
        document_id: 文档ID
    """
    try:
        document = KnowledgeDocument.objects.get(id=document_id)
        document.embedding_status = ChunkStatus.EMBEDDING
        document.save()
        
        # 读取文档内容
        content = ""
        try:
            with document.file.open() as f:
                content = f.read().decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            # 尝试其他编码
            with document.file.open() as f:
                content = f.read().decode('gbk', errors='ignore')
        
        if not content:
            raise ValueError("文档内容为空")
            
        # 使用 RAGEngine 处理文档 (分片、向量化、存储)
        rag_engine = RAGEngine()
        
        # 添加到向量库
        rag_engine.add_document(
            doc_id=str(document.id),
            title=document.title,
            content=content,
            metadata={
                'source': document.title,
                'file_name': document.file.name,
                'created_at': str(document.created_at)
            }
        )
        
        # 更新文档状态
        document.is_embedded = True
        document.chunk_count = 1 # 简化处理，实际分片数在向量库中
        document.embedding_status = ChunkStatus.INDEXED
        document.save()
        
        logger.info(f"文档向量化完成: {document.title}")
        
    except Exception as e:
        logger.error(f"文档向量化失败: {str(e)}")
        if document:
            document.embedding_status = ChunkStatus.FAILED
            document.save()
        raise self.retry(exc=e)


def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """保留函数以兼容旧代码，但不再主要使用"""
    return []
    """
    将文本分割成块
    
    Args:
        text: 输入文本
        chunk_size: 每个块的大小
        overlap: 块之间的重叠大小
        
    Returns:
        文档块列表
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # 如果不是最后一块，尝试在句子边界处分割
        if end < len(text):
            # 查找最近的句号、问号、感叹号
            for delimiter in ['。', '！', '？', '.', '!', '?', '\n']:
                last_delimiter = text.rfind(delimiter, start, end)
                if last_delimiter > start + chunk_size // 2:
                    end = last_delimiter + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks