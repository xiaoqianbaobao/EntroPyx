from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from apps.repository.models import Repository
from apps.code_review.models import CodeReview, RiskLevel, FeedbackStatus
from apps.prd_review.models import PRDReview
from apps.test_case.models import TestCase
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os


@login_required
def dashboard(request):
    """数据看板页面"""
    # 新的Dashboard模板通过JavaScript API获取数据，这里只渲染模板
    return render(request, 'dashboard.html')


@login_required
def health_check(request):
    """健康检查"""
    return JsonResponse({'status': 'ok'})


@login_required
def repository_list(request):
    """仓库列表页面"""
    repositories = Repository.objects.all()
    return render(request, 'repository_list.html', {
        'repositories': repositories
    })


@login_required
def repository_create(request):
    """创建仓库"""
    if request.method == 'POST':
        try:
            repo = Repository.objects.create(
                name=request.POST.get('name'),
                git_url=request.POST.get('git_url'),
                auth_type=request.POST.get('auth_type', 'password'),
                username=request.POST.get('username', ''),
                password_encrypted=request.POST.get('password', ''),
                local_path=os.path.join('/home/csq/workspace/bestBugBot/repos', request.POST.get('name', '')),
                dingtalk_webhook=request.POST.get('dingtalk_webhook', ''),
                dingtalk_secret=request.POST.get('dingtalk_secret', ''),
                high_risk_threshold=float(request.POST.get('high_risk_threshold', 0.7)),
                medium_risk_threshold=float(request.POST.get('medium_risk_threshold', 0.4)),
                critical_patterns=[],
                ignore_patterns=[],
                created_by=request.user
            )
            return redirect('repository_list')
        except Exception as e:
            print(f"Repository create error: {e}")
            return render(request, 'repository_list.html', {
                'error': f'创建失败: {str(e)}',
                'repositories': Repository.objects.all()
            })
    return redirect('repository_list')


@login_required
def repository_detail(request, pk):
    """仓库详情页面"""
    repo = get_object_or_404(Repository, pk=pk)
    reviews = CodeReview.objects.filter(repository=repo).order_by('-created_at')[:20]

    # 获取评审模式配置
    from apps.code_review.models import ScheduledReviewConfig, RealtimeMonitorConfig

    # 获取定时评审配置（包含该仓库的配置）
    scheduled_configs = ScheduledReviewConfig.objects.filter(repositories=repo)

    # 获取实时监控配置
    realtime_config = RealtimeMonitorConfig.objects.filter(repository=repo).first()

    return render(request, 'repository_detail.html', {
        'repository': repo,
        'reviews': reviews,
        'scheduled_configs': scheduled_configs,
        'realtime_config': realtime_config
    })


@login_required
def repository_update(request, pk):
    """更新仓库"""
    repo = get_object_or_404(Repository, pk=pk)
    if request.method == 'POST':
        try:
            repo.name = request.POST.get('name')
            repo.git_url = request.POST.get('git_url')
            repo.auth_type = request.POST.get('auth_type', 'password')
            repo.username = request.POST.get('username', '')
            if request.POST.get('password'):
                repo.password_encrypted = request.POST.get('password')
            repo.dingtalk_webhook = request.POST.get('dingtalk_webhook', '')
            repo.dingtalk_secret = request.POST.get('dingtalk_secret', '')
            repo.high_risk_threshold = float(request.POST.get('high_risk_threshold', 0.7))
            repo.medium_risk_threshold = float(request.POST.get('medium_risk_threshold', 0.4))
            repo.review_branch = request.POST.get('review_branch', 'master')
            repo.review_all_branches = 'review_all_branches' in request.POST
            repo.is_active = 'is_active' in request.POST
            repo.save()
            return redirect('repository_detail', pk=repo.id)
        except Exception as e:
            print(f"Repository update error: {e}")
            reviews = CodeReview.objects.filter(repository=repo).order_by('-created_at')[:20]
            return render(request, 'repository_detail.html', {
                'repository': repo,
                'reviews': reviews,
                'error': f'更新失败: {str(e)}'
            })
    return redirect('repository_detail', pk=pk)


@login_required
def code_review_list(request):
    """代码评审列表页面"""
    queryset = CodeReview.objects.all()
    
    # 筛选条件
    repository_id = request.GET.get('repository_id')
    branch = request.GET.get('branch')
    risk_level = request.GET.get('risk_level')
    author = request.GET.get('author')
    
    if repository_id:
        queryset = queryset.filter(repository_id=repository_id)
    if branch:
        queryset = queryset.filter(branch=branch)
    if risk_level:
        queryset = queryset.filter(risk_level=risk_level)
    if author:
        queryset = queryset.filter(author__icontains=author)
    
    reviews = queryset.order_by('-created_at')[:100]
    repositories = Repository.objects.filter(is_active=True)
    
    return render(request, 'code_review_list.html', {
        'reviews': reviews,
        'repositories': repositories
    })


@login_required
def code_review_detail(request, pk):
    """代码评审详情页面"""
    review = get_object_or_404(CodeReview, pk=pk)
    return render(request, 'code_review_detail.html', {
        'review': review
    })


@login_required
def prd_review_list(request):
    """PRD评审列表页面"""
    prd_reviews = PRDReview.objects.order_by('-created_at')[:20]
    return render(request, 'prd_review_list.html', {
        'prd_reviews': prd_reviews
    })


@login_required
def prd_review_list_v2(request):
    """PRD文档管理页面（新版本）"""
    queryset = PRDReview.objects.order_by('-created_at')
    
    # 分页处理
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
        if per_page < 1: per_page = 10
        if per_page > 100: per_page = 100
    except ValueError:
        per_page = 10
        
    paginator = Paginator(queryset, per_page)
    
    try:
        prd_reviews = paginator.page(page)
    except PageNotAnInteger:
        prd_reviews = paginator.page(1)
    except EmptyPage:
        prd_reviews = paginator.page(paginator.num_pages)
        
    return render(request, 'prd_review_list_v2.html', {
        'prd_reviews': prd_reviews,
        'per_page': per_page,
        'total_count': paginator.count
    })


@login_required
def prd_review_detail(request, pk):
    """PRD评审详情页面"""
    prd_review = get_object_or_404(PRDReview, pk=pk)
    return render(request, 'prd_review_detail_v2.html', {
        'prd_review': prd_review
    })


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def prd_review_edit(request, pk):
    """PRD文档编辑页面"""
    try:
        prd = PRDReview.objects.get(pk=pk)
        
        # 读取文档内容
        content = ""
        try:
            if prd.file:
                with prd.file.open('r') as f:
                    content = f.read()
        except Exception:
            # 如果是二进制文件（如PDF/Word），无法直接作为文本编辑
            # 这里可能需要提示或转换，或者只允许编辑元数据
            content = "（该文件格式暂不支持在线编辑，仅支持修改标题）"
            if prd.file.name.endswith('.md') or prd.file.name.endswith('.txt'):
                with prd.file.open('r') as f:
                    content = f.read()
                    
    except PRDReview.DoesNotExist:
        return redirect('prd_review_list')
        
    return render(request, 'prd_review/prd_edit.html', {
        'prd': prd,
        'content': content
    })

@login_required
def test_case_list(request):
    """测试用例列表页面"""
    queryset = TestCase.objects.order_by('-created_at')
    
    # 分页处理
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10) # 默认每页10条
    try:
        per_page = int(per_page)
        if per_page < 1: per_page = 10
        if per_page > 100: per_page = 100 # 限制最大每页显示数
    except ValueError:
        per_page = 10
        
    paginator = Paginator(queryset, per_page)
    
    try:
        test_cases = paginator.page(page)
    except PageNotAnInteger:
        test_cases = paginator.page(1)
    except EmptyPage:
        test_cases = paginator.page(paginator.num_pages)
        
    return render(request, 'test_case_list.html', {
        'test_cases': test_cases,
        'per_page': per_page,
        'total_count': paginator.count
    })


@login_required
def test_case_generate(request):
    """AI生成测试用例页面"""
    prd_reviews = PRDReview.objects.filter(review_status='PENDING')[:20]
    code_reviews = CodeReview.objects.order_by('-created_at')[:20]
    return render(request, 'test_case_generate.html', {
        'prd_reviews': prd_reviews,
        'code_reviews': code_reviews
    })


@login_required
def test_case_detail(request, pk):
    """测试用例详情页面"""
    test_case = get_object_or_404(TestCase, pk=pk)
    return render(request, 'test_case_detail.html', {
        'test_case': test_case
    })


@login_required
def ai_chat(request):
    """AI智能评审对话页面"""
    return render(request, 'ai_chat.html')


@login_required
def product_agent_view(request):
    """产品智能体聚合页"""
    tools = [
        {
            'name': 'AI产品提效工具',
            'desc': '上传PRD文档，一键进行完整性、一致性评审，自动生成用户故事和验收标准。',
            'icon': 'bi-file-earmark-text',
            'url': '/prd-review/prd-reviews/',
            'color': 'primary'
        },
        {
            'name': 'AI会议助手',
            'desc': '实时录音转写，智能提取会议纪要、待办事项和关键决策，支持多语种识别。',
            'icon': 'bi-mic',
            'url': '/meeting-assistant/',
            'color': 'success'
        }
    ]
    return render(request, 'agent_dashboard.html', {'agent_name': '产品智能体', 'tools': tools})


@login_required
def developer_agent_view(request):
    """开发智能体聚合页"""
    tools = [
        {
            'name': '仓库管理',
            'desc': '统一管理代码仓库，配置Git连接、分支策略和WebHook集成。',
            'icon': 'bi-git',
            'url': '/repository/',
            'color': 'info'
        },
        {
            'name': '代码评审',
            'desc': '基于DeepSeek大模型的智能代码审查，自动检测Bug、安全漏洞和代码异味。',
            'icon': 'bi-code-slash',
            'url': '/code-review/reviews/',
            'color': 'warning'
        }
    ]
    return render(request, 'agent_dashboard.html', {'agent_name': '开发智能体', 'tools': tools})


@login_required
def tester_agent_view(request):
    """测试智能体聚合页"""
    # 临时复用 test_case_list 页面，后续可根据需求改为聚合页
    # 目前先重定向到 test_case_list，或者使用 agent_dashboard 展示工具
    # 根据用户需求 "参考测试智能体中的正在开发中的工具列表"，其实 test_case_list 页面本身就是列表+工具卡片
    # 所以这里可以保留原样，或者也做一个聚合入口。
    # 为了保持一致性，如果用户点击侧边栏的一级菜单，最好进入一个导航页。
    # 但由于测试智能体的主功能就是测试用例列表，直接进入列表可能更方便。
    # 让我们遵循用户 "参考测试智能体中的正在开发中的工具列表" 的指示，
    # 也许用户希望测试智能体也像前两个一样，是一个纯粹的工具入口页？
    # "测试智能体中的正在开发中的工具列表" 是在列表页下方的。
    # 既然用户没有明确要求改动测试智能体内部结构，我们先不动它，只在侧边栏改入口。
    # 但为了统一，也可以提供一个 dashboard。
    # 既然用户没细说，暂不添加 tester_agent_view，侧边栏直接链到 test_case_list。
    pass
