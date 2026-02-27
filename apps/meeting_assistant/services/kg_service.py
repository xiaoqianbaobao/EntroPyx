"""
知识图谱服务
Knowledge Graph Service
"""
import logging
from typing import List, Dict, Optional
from django.db import transaction
from django.contrib.auth.models import User

from ..models import (
    KnowledgeEntity,
    KnowledgeRelation,
    MeetingSummary,
    MeetingTranscript,
    MeetingRecording,
    EntityType,
    RelationType
)

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务"""
    
    def __init__(self):
        self.name = "Knowledge Graph Service"
    
    def build_meeting_graph(self, summary: MeetingSummary):
        """
        构建会议知识图谱
        
        Args:
            summary: 会议纪要对象
        """
        try:
            with transaction.atomic():
                # 提取和创建实体
                entities = self._extract_entities(summary)
                
                # 创建关系
                self._create_relations(summary, entities)
                
                logger.info(f"Knowledge graph built for meeting {summary.id}")
                
        except Exception as e:
            logger.error(f"Failed to build knowledge graph: {str(e)}")
            raise
    
    def _extract_entities(self, summary: MeetingSummary) -> Dict[str, KnowledgeEntity]:
        """
        从会议纪要中提取实体
        
        Args:
            summary: 会议纪要对象
        
        Returns:
            Dict: 实体字典 {entity_key: entity_obj}
        """
        entities = {}
        
        # 1. 会议实体
        meeting_key = f"meeting_{summary.recording.id}"
        meeting_entity, _ = KnowledgeEntity.objects.get_or_create(
            entity_type=EntityType.PROJECT,
            entity_name=summary.recording.meeting_title,
            defaults={
                'meeting': summary.recording,
                'repository': summary.recording.repository,
                'metadata': {
                    'date': str(summary.recording.meeting_date),
                    'duration': summary.recording.duration
                }
            }
        )
        entities[meeting_key] = meeting_entity
        
        # 2. 仓库实体
        repo_key = f"repo_{summary.recording.repository.id}"
        repo_entity, _ = KnowledgeEntity.objects.get_or_create(
            entity_type=EntityType.PROJECT,
            entity_name=summary.recording.repository.name,
            defaults={
                'repository': summary.recording.repository,
                'metadata': {
                    'git_url': summary.recording.repository.git_url
                }
            }
        )
        entities[repo_key] = repo_entity
        
        # 3. 参会人员实体
        participants = summary.recording.participants.split(',')
        for participant in participants:
            participant = participant.strip()
            if participant:
                person_key = f"person_{participant}"
                person_entity, _ = KnowledgeEntity.objects.get_or_create(
                    entity_type=EntityType.PERSON,
                    entity_name=participant,
                    defaults={'metadata': {'source': 'participants'}}
                )
                entities[person_key] = person_entity
        
        # 4. 从转写中提取说话人
        for transcript in summary.recording.transcripts.all():
            speaker_key = f"speaker_{transcript.speaker}"
            if speaker_key not in entities:
                speaker_entity, _ = KnowledgeEntity.objects.get_or_create(
                    entity_type=EntityType.PERSON,
                    entity_name=transcript.speaker,
                    defaults={
                        'metadata': {
                            'source': 'transcript',
                            'speaker_id': transcript.speaker
                        }
                    }
                )
                entities[speaker_key] = speaker_entity
        
        # 5. 从纪要中提取关键词作为主题实体
        for keyword in summary.key_points:
            topic_key = f"topic_{keyword}"
            if topic_key not in entities:
                topic_entity, _ = KnowledgeEntity.objects.get_or_create(
                    entity_type=EntityType.TOPIC,
                    entity_name=keyword,
                    defaults={'metadata': {'source': 'key_points'}}
                )
                entities[topic_key] = topic_entity
        
        # 6. 从评审意见中提取问题实体
        for opinion in summary.opinions.filter(opinion_type=EntityType.ISSUE):
            issue_key = f"issue_{opinion.id}"
            if issue_key not in entities:
                issue_entity, _ = KnowledgeEntity.objects.get_or_create(
                    entity_type=EntityType.ISSUE,
                    entity_name=opinion.content[:50],
                    defaults={
                        'metadata': {
                            'full_content': opinion.content,
                            'priority': opinion.priority,
                            'resolved': opinion.is_resolved
                        }
                    }
                )
                entities[issue_key] = issue_entity
        
        # 7. 从决策事项中提取决策实体
        for decision in summary.decisions:
            decision_key = f"decision_{hash(decision)}"
            if decision_key not in entities:
                decision_entity, _ = KnowledgeEntity.objects.get_or_create(
                    entity_type=EntityType.DECISION,
                    entity_name=decision[:50],
                    defaults={'metadata': {'full_content': decision}}
                )
                entities[decision_key] = decision_entity
        
        return entities
    
    def _create_relations(self, summary: MeetingSummary, entities: Dict[str, KnowledgeEntity]):
        """
        创建实体之间的关系
        
        Args:
            summary: 会议纪要对象
            entities: 实体字典
        """
        meeting_key = f"meeting_{summary.recording.id}"
        repo_key = f"repo_{summary.recording.repository.id}"
        
        # 1. 会议属于仓库
        KnowledgeRelation.objects.get_or_create(
            source=entities[repo_key],
            target=entities[meeting_key],
            relation_type=RelationType.RELATED_TO,
            defaults={'summary': summary}
        )
        
        # 2. 人员参会关系
        for entity_key, entity in entities.items():
            if entity.entity_type == EntityType.PERSON:
                KnowledgeRelation.objects.get_or_create(
                    source=entity,
                    target=entities[meeting_key],
                    relation_type=RelationType.ATTENDED,
                    defaults={'summary': summary}
                )
        
        # 3. 主题讨论关系
        for entity_key, entity in entities.items():
            if entity.entity_type == EntityType.TOPIC:
                KnowledgeRelation.objects.get_or_create(
                    source=entities[meeting_key],
                    target=entity,
                    relation_type=RelationType.DISCUSSED,
                    defaults={'summary': summary}
                )
        
        # 4. 问题提出关系
        for opinion in summary.opinions.filter(opinion_type=EntityType.ISSUE):
            issue_key = f"issue_{opinion.id}"
            if issue_key in entities:
                # 如果有说话人，创建说话人到问题的关系
                if opinion.speaker:
                    speaker_key = f"person_{opinion.speaker.get_full_name() or opinion.speaker.username}"
                    if speaker_key in entities:
                        KnowledgeRelation.objects.get_or_create(
                            source=entities[speaker_key],
                            target=entities[issue_key],
                            relation_type=RelationType.RAISED,
                            defaults={'summary': summary, 'opinion_id': opinion.id}
                        )
                
                # 会议讨论了问题
                KnowledgeRelation.objects.get_or_create(
                    source=entities[meeting_key],
                    target=entities[issue_key],
                    relation_type=RelationType.DISCUSSED,
                    defaults={'summary': summary}
                )
        
        # 5. 决策关系
        for decision in summary.decisions:
            decision_key = f"decision_{hash(decision)}"
            if decision_key in entities:
                KnowledgeRelation.objects.get_or_create(
                    source=entities[meeting_key],
                    target=entities[decision_key],
                    relation_type=RelationType.DECIDED,
                    defaults={'summary': summary}
                )
    
    def search_entities(self, keyword: str, entity_type: str = None) -> List[KnowledgeEntity]:
        """
        搜索实体
        
        Args:
            keyword: 搜索关键词
            entity_type: 实体类型（可选）
        
        Returns:
            List[KnowledgeEntity]: 匹配的实体列表
        """
        queryset = KnowledgeEntity.objects.filter(entity_name__icontains=keyword)
        
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        return queryset.select_related('user', 'repository', 'meeting')[:20]
    
    def get_entity_relations(self, entity_id: int, direction: str = 'both') -> List[KnowledgeRelation]:
        """
        获取实体的关系
        
        Args:
            entity_id: 实体ID
            direction: 关系方向 ('outgoing', 'incoming', 'both')
        
        Returns:
            List[KnowledgeRelation]: 关系列表
        """
        entity = KnowledgeEntity.objects.get(id=entity_id)
        
        if direction == 'outgoing':
            return entity.outgoing_relations.select_related('target').all()
        elif direction == 'incoming':
            return entity.incoming_relations.select_related('source').all()
        else:
            # 返回所有关系
            outgoing = list(entity.outgoing_relations.select_related('target').all())
            incoming = list(entity.incoming_relations.select_related('source').all())
            return outgoing + incoming
    
    def get_related_meetings(self, entity_id: int) -> List[MeetingRecording]:
        """
        获取与实体相关的会议
        
        Args:
            entity_id: 实体ID
        
        Returns:
            List[MeetingRecording]: 相关会议列表
        """
        entity = KnowledgeEntity.objects.get(id=entity_id)
        
        # 获取所有相关的会议ID
        meeting_ids = set()
        
        # 通过会议实体关系
        if entity.entity_type == EntityType.PROJECT:
            meeting_ids.add(entity.meeting_id)
        
        # 通过关系查找
        for relation in entity.outgoing_relations.all():
            if relation.target.entity_type == EntityType.PROJECT:
                meeting_ids.add(relation.target.meeting_id)
        
        for relation in entity.incoming_relations.all():
            if relation.source.entity_type == EntityType.PROJECT:
                meeting_ids.add(relation.source.meeting_id)
        
        # 获取会议对象
        return MeetingRecording.objects.filter(id__in=meeting_ids).select_related('repository')
    
    def get_entity_graph(self, entity_id: int, depth: int = 2) -> Dict:
        """
        获取实体的子图
        
        Args:
            entity_id: 实体ID
            depth: 深度
        
        Returns:
            Dict: 图数据 {nodes: [], edges: []}
        """
        entity = KnowledgeEntity.objects.get(id=entity_id)
        
        nodes = []
        edges = []
        
        # 添加中心节点
        nodes.append({
            'id': entity.id,
            'name': entity.entity_name,
            'type': entity.entity_type,
            'isCenter': True
        })
        
        # 递归获取邻居节点
        visited = {entity.id}
        self._collect_neighbors(entity, depth, visited, nodes, edges)
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def _collect_neighbors(self, entity, depth, visited, nodes, edges):
        """递归收集邻居节点"""
        if depth == 0:
            return
        
        # 获取出边
        for relation in entity.outgoing_relations.select_related('target').all():
            target = relation.target
            
            if target.id not in visited:
                visited.add(target.id)
                nodes.append({
                    'id': target.id,
                    'name': target.entity_name,
                    'type': target.entity_type
                })
                
                edges.append({
                    'source': entity.id,
                    'target': target.id,
                    'type': relation.relation_type,
                    'label': relation.get_relation_type_display()
                })
                
                # 递归
                self._collect_neighbors(target, depth - 1, visited, nodes, edges)
        
        # 获取入边
        for relation in entity.incoming_relations.select_related('source').all():
            source = relation.source
            
            if source.id not in visited:
                visited.add(source.id)
                nodes.append({
                    'id': source.id,
                    'name': source.entity_name,
                    'type': source.entity_type
                })
                
                edges.append({
                    'source': source.id,
                    'target': entity.id,
                    'type': relation.relation_type,
                    'label': relation.get_relation_type_display()
                })
                
                # 递归
                self._collect_neighbors(source, depth - 1, visited, nodes, edges)


def get_kg_service():
    """获取知识图谱服务实例"""
    return KnowledgeGraphService()