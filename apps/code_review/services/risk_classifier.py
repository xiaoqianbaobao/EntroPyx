from typing import List, Dict


class RiskClassifier:
    """风险分类器"""
    
    def classify(
        self,
        issues: List[Dict],
        files: List[Dict]
    ) -> float:
        """
        综合评估风险评分
        
        Args:
            issues: AI识别的问题列表
            files: 变更文件列表
            
        Returns:
            float: 风险评分 (0-1)
        """
        score = 0.0
        
        # 1. 基于AI识别的问题计算分数
        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity == 'high':
                score += 0.15
            elif severity == 'medium':
                score += 0.08
            else:
                score += 0.03
        
        # 2. 基于文件重要性调整
        critical_files = [f for f in files if f.get('is_critical')]
        if critical_files:
            score *= 1.2  # 关键文件风险权重增加20%
        
        # 3. 基于问题类型调整
        type_weights = {
            'security': 1.5,
            'reliability': 1.3,
            'performance': 1.1,
            'maintainability': 0.8
        }
        
        for issue in issues:
            issue_type = issue.get('type', 'maintainability')
            weight = type_weights.get(issue_type, 1.0)
            if issue.get('severity') == 'high':
                score *= weight
        
        # 限制在0-1范围内
        return min(1.0, max(0.0, score))
