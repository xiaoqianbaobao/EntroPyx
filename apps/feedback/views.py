from rest_framework import viewsets, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import FeedbackRule, RuleType
from .serializers import FeedbackRuleSerializer, FeedbackRuleCreateSerializer


class FeedbackRuleViewSet(viewsets.ModelViewSet):
    """反馈规则视图集"""
    queryset = FeedbackRule.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackRuleCreateSerializer
        return FeedbackRuleSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        rule_type = self.request.query_params.get('rule_type')
        is_active = self.request.query_params.get('is_active')
        
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data,
            'total': queryset.count()
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)
        return Response({
            'code': 0,
            'message': '创建成功',
            'data': FeedbackRuleSerializer(instance).data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'code': 0,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'code': 0,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)


class FeedbackStatsView(views.APIView):
    """反馈统计视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取反馈统计"""
        from apps.code_review.models import CodeReview, FeedbackStatus
        
        total = CodeReview.objects.exclude(
            feedback_status=FeedbackStatus.PENDING
        ).count()
        correct = CodeReview.objects.filter(
            feedback_status=FeedbackStatus.CORRECT
        ).count()
        false_positive = CodeReview.objects.filter(
            feedback_status=FeedbackStatus.FALSE_POSITIVE
        ).count()
        missed = CodeReview.objects.filter(
            feedback_status=FeedbackStatus.MISSED
        ).count()
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # 规则统计
        whitelist_count = FeedbackRule.objects.filter(
            rule_type=RuleType.WHITELIST, is_active=True
        ).count()
        blacklist_count = FeedbackRule.objects.filter(
            rule_type=RuleType.BLACKLIST, is_active=True
        ).count()
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'total_feedback': total,
                'correct_count': correct,
                'false_positive_count': false_positive,
                'missed_count': missed,
                'accuracy_rate': round(accuracy, 2),
                'whitelist_rules': whitelist_count,
                'blacklist_rules': blacklist_count
            }
        })


# 页面视图
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import FeedbackRule


@login_required
def feedback_rules_list(request):
    """反馈规则列表页面"""
    rules = FeedbackRule.objects.all().order_by('-created_at')
    return render(request, 'feedback_rules_list.html', {
        'rules': rules
    })
