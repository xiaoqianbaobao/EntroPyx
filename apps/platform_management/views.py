from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import LLMConfig
import json

# Mock Data
MOCK_AGENTS = [
    {'id': 1, 'name': '产品经理助手', 'description': '协助产品经理进行需求分析和PRD撰写', 'type': 'PRODUCT', 'status': 'ACTIVE', 'created_at': '2023-10-01'},
    {'id': 2, 'name': '代码评审专家', 'description': '自动进行代码评审，发现潜在Bug和安全漏洞', 'type': 'DEVELOPER', 'status': 'ACTIVE', 'created_at': '2023-10-02'},
    {'id': 3, 'name': '测试用例生成器', 'description': '根据PRD或代码自动生成测试用例', 'type': 'TESTER', 'status': 'INACTIVE', 'created_at': '2023-10-05'},
]

MOCK_WORKFLOWS = [
    {'id': 1, 'name': '自动化发布流程', 'description': '代码提交 -> 代码评审 -> 单元测试 -> 构建部署', 'steps': 4, 'status': 'ACTIVE'},
    {'id': 2, 'name': '需求评审流程', 'description': '需求提交 -> 智能分析 -> 生成PRD -> 人工审核', 'steps': 3, 'status': 'DRAFT'},
]

@login_required
def dashboard_view(request):
    """平台管理仪表盘"""
    # 获取 LLM 配置
    llm_config = LLMConfig.objects.filter(is_active=True).first()
    if not llm_config:
        # 如果不存在，创建一个默认的（或者不创建，让前端显示空表单）
        pass
        
    context = {
        'agent_count': len(MOCK_AGENTS),
        'workflow_count': len(MOCK_WORKFLOWS),
        'knowledge_count': 12, # 假数据
        'llm_config': llm_config
    }
    return render(request, 'platform_management/dashboard.html', context)

@login_required
@require_http_methods(["POST"])
def update_llm_config(request):
    """更新LLM配置"""
    try:
        data = json.loads(request.body)
        api_base = data.get('api_base')
        api_key = data.get('api_key')
        model_name = data.get('model_name')
        
        if not all([api_base, api_key, model_name]):
            return JsonResponse({'code': 400, 'message': '请填写所有必填字段'})
            
        # 查找现有的活跃配置，或者创建一个新的
        config = LLMConfig.objects.filter(is_active=True).first()
        if not config:
            config = LLMConfig(name='默认配置', is_active=True)
            
        config.api_base = api_base
        config.api_key = api_key
        config.model_name = model_name
        config.save()
        
        return JsonResponse({'code': 0, 'message': '配置更新成功'})
    except Exception as e:
        return JsonResponse({'code': 500, 'message': str(e)})

@login_required
def agent_list_view(request):
    """智能体列表"""
    context = {
        'agents': MOCK_AGENTS
    }
    return render(request, 'platform_management/agent_list.html', context)

@login_required
def agent_create_view(request):
    """创建智能体"""
    if request.method == 'POST':
        # Mock create logic
        return redirect('platform_management:agent_list')
    return render(request, 'platform_management/agent_form.html', {'action': 'create'})

@login_required
def agent_detail_view(request, pk):
    """智能体详情"""
    agent = next((a for a in MOCK_AGENTS if a['id'] == pk), None)
    return render(request, 'platform_management/agent_detail.html', {'agent': agent})

@login_required
def agent_update_view(request, pk):
    """更新智能体"""
    agent = next((a for a in MOCK_AGENTS if a['id'] == pk), None)
    if request.method == 'POST':
        # Mock update logic
        return redirect('platform_management:agent_list')
    return render(request, 'platform_management/agent_form.html', {'agent': agent, 'action': 'update'})

@login_required
def agent_delete_view(request, pk):
    """删除智能体"""
    # Mock delete logic
    return redirect('platform_management:agent_list')

@login_required
def workflow_list_view(request):
    """工作流列表"""
    context = {
        'workflows': MOCK_WORKFLOWS
    }
    return render(request, 'platform_management/workflow_list.html', context)

@login_required
def workflow_create_view(request):
    """创建工作流"""
    if request.method == 'POST':
        return redirect('platform_management:workflow_list')
    return render(request, 'platform_management/workflow_form.html')

@login_required
def workflow_detail_view(request, pk):
    """工作流详情（编排器Mock）"""
    workflow = next((w for w in MOCK_WORKFLOWS if w['id'] == pk), None)
    return render(request, 'platform_management/workflow_editor.html', {'workflow': workflow})

@login_required
def knowledge_base_proxy_view(request):
    """知识库管理代理（重定向到原有知识库页面）"""
    return redirect('knowledge_base:list')