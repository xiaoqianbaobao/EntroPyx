import os
import logging
import json
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    RAG引擎：负责文档的分片、向量化、存储和检索
    支持自动降级：如果缺少向量库依赖，回退到基于关键词的搜索
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGEngine, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化RAG引擎"""
        self.use_vector_db = False
        self.vector_store = None
        self.embeddings = None
        self.text_splitter = None
        
        try:
            # 尝试导入LangChain和向量库依赖
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain_community.vectorstores import Chroma
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            # 初始化分片器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", "。", "！", "!", "？", "?", " ", ""]
            )
            
            # 初始化Embedding模型 (使用轻量级本地模型)
            # 注意：首次运行会自动下载模型到本地缓存
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # 初始化向量存储 (ChromaDB)
            persist_directory = os.path.join(settings.BASE_DIR, 'data', 'chroma_db')
            os.makedirs(persist_directory, exist_ok=True)
            
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings,
                collection_name="entropyx_knowledge"
            )
            
            self.use_vector_db = True
            logger.info("RAG引擎初始化成功：使用向量数据库模式")
            
        except ImportError as e:
            logger.warning(f"RAG引擎降级：缺少依赖 {e}，将使用关键词搜索模式")
            self.use_vector_db = False
        except Exception as e:
            logger.error(f"RAG引擎初始化失败：{e}，将使用关键词搜索模式")
            self.use_vector_db = False
            
    def add_document(self, doc_id: str, title: str, content: str, metadata: Dict = None):
        """
        添加文档到知识库
        
        Args:
            doc_id: 文档唯一标识
            title: 标题
            content: 内容
            metadata: 元数据
        """
        if not content:
            return
            
        metadata = metadata or {}
        metadata.update({
            "doc_id": str(doc_id),
            "title": title
        })
        
        if self.use_vector_db:
            try:
                # 1. 分片
                chunks = self.text_splitter.split_text(content)
                
                # 2. 构建Document对象
                from langchain.docstore.document import Document
                documents = [
                    Document(page_content=chunk, metadata=metadata) 
                    for chunk in chunks
                ]
                
                # 3. 存入向量库
                self.vector_store.add_documents(documents)
                self.vector_store.persist()
                logger.info(f"文档 {title} ({len(chunks)} 分片) 已存入向量库")
                
            except Exception as e:
                logger.error(f"向量化文档失败: {e}")
        else:
            # 降级模式：不做处理，检索时直接查数据库
            pass

    def search(self, query: str, top_k: int = 3, filter_metadata: Dict = None) -> List[Dict]:
        """
        检索相关知识
        
        Args:
            query: 查询语句
            top_k: 返回结果数量
            filter_metadata: 过滤条件
            
        Returns:
            List[Dict]: 包含 content, metadata, score 的结果列表
        """
        if self.use_vector_db:
            try:
                # 向量检索
                results = self.vector_store.similarity_search_with_score(
                    query, 
                    k=top_k,
                    filter=filter_metadata
                )
                
                return [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score
                    }
                    for doc, score in results
                ]
            except Exception as e:
                logger.error(f"向量检索失败: {e}")
                return self._keyword_search(query, top_k)
        else:
            return self._keyword_search(query, top_k)
            
    def _keyword_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """基于关键词的简单检索（降级方案）"""
        try:
            from apps.knowledge_base.models import KnowledgeDocument
            import jieba
            
            # 分词
            keywords = list(jieba.cut_for_search(query))
            keywords = [k for k in keywords if len(k) > 1] # 过滤单字
            
            if not keywords:
                # 如果分词结果为空，退化为包含搜索
                keywords = [query]
            
            # 简单的数据库模糊匹配
            # 注意：这种方式效率低且不准确，仅作为无向量库时的Fallback
            from django.db.models import Q
            q_obj = Q()
            for k in keywords:
                q_obj |= Q(content__icontains=k)
            
            docs = KnowledgeDocument.objects.filter(q_obj)[:top_k*2]
            
            results = []
            for doc in docs:
                # 简单的相关性打分：关键词出现次数
                score = 0
                lower_content = doc.content.lower()
                for k in keywords:
                    score += lower_content.count(k.lower())
                
                # 提取片段
                start_idx = -1
                for k in keywords:
                    idx = lower_content.find(k.lower())
                    if idx != -1:
                        start_idx = idx
                        break
                
                if start_idx == -1: start_idx = 0
                
                # 截取片段 (前后200字)
                snippet_start = max(0, start_idx - 100)
                snippet_end = min(len(doc.content), start_idx + 300)
                snippet = doc.content[snippet_start:snippet_end]
                
                results.append({
                    "content": snippet,
                    "metadata": {"title": doc.title, "doc_id": doc.id},
                    "score": score
                })
            
            # 按分数排序
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []

    def delete_document(self, doc_id: str):
        """删除文档索引"""
        if self.use_vector_db:
            try:
                # ChromaDB 删除 API
                # 注意：Chroma 的 delete 参数可能随版本变化，需根据实际安装版本调整
                self.vector_store._collection.delete(
                    where={"doc_id": str(doc_id)}
                )
                self.vector_store.persist()
            except Exception as e:
                logger.error(f"删除向量索引失败: {e}")
