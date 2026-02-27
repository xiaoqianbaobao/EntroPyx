#!/usr/bin/env python3
"""
测试修复内容
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_database_tables():
    """测试数据库表"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'knowledge_%'")
            tables = cursor.fetchall()
            
        if tables:
            print("✅ 知识库数据库表存在:")
            for table in tables:
                print(f"   - {table[0]}")
            return True
        else:
            print("❌ 知识库数据库表不存在")
            return False
    except Exception as e:
        print(f"❌ 数据库表测试失败: {e}")
        return False

def test_dashboard_api():
    """测试dashboard API"""
    try:
        from django.test import Client
        client = Client()
        
        # 创建测试用户
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='test', password='test123')
        
        # 登录
        client.login(username='test', password='test123')
        response = client.get('/api/v1/dashboard/stats/')
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'knowledge_base' in data['data']:
                print("✅ Dashboard API正常，包含知识库数据")
                kb_data = data['data']['knowledge_base']
                print(f"   - 文档数: {kb_data.get('total_docs', 0)}")
                print(f"   - 实体数: {kb_data.get('total_entities', 0)}")
                print(f"   - 关系数: {kb_data.get('total_relationships', 0)}")
                return True
            else:
                print("❌ Dashboard API响应格式错误")
                return False
        else:
            print(f"❌ Dashboard API返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard API测试失败: {e}")
        return False

def test_knowledge_base_url():
    """测试知识库URL"""
    try:
        from django.test import Client
        client = Client()
        
        # 创建测试用户
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='test', password='test123')
        
        # 登录
        client.login(username='test', password='test123')
        response = client.get('/api/v1/knowledge/')
        
        if response.status_code in [200, 301, 302]:
            print("✅ 知识库URL可访问")
            return True
        else:
            print(f"❌ 知识库URL访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 知识库URL测试失败: {e}")
        return False

def test_dashboard_template():
    """测试dashboard模板"""
    try:
        from django.shortcuts import render
        from django.template.loader import get_template
        from django.template import RequestContext
        
        template = get_template('dashboard.html')
        context = RequestContext(None, {})
        
        # 检查模板中是否有知识库链接
        template_content = template.render(context)
        if 'knowledge_base:list' in template_content:
            print("✅ Dashboard模板包含知识库链接")
            return True
        else:
            print("❌ Dashboard模板缺少知识库链接")
            return False
    except Exception as e:
        print(f"❌ Dashboard模板测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("修复验证测试")
    print("=" * 60)
    
    all_passed = True
    
    print("\n1. 测试数据库表...")
    if not test_database_tables():
        all_passed = False
    
    print("\n2. 测试Dashboard API...")
    if not test_dashboard_api():
        all_passed = False
    
    print("\n3. 测试知识库URL...")
    if not test_knowledge_base_url():
        all_passed = False
    
    print("\n4. 测试Dashboard模板...")
    if not test_dashboard_template():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有修复验证通过！系统正常运行。")
        print("\n修复内容:")
        print("  1. ✅ 修复数据库表缺失问题")
        print("  2. ✅ 修复knowledge_stats变量未定义错误")
        print("  3. ✅ 首页知识库入口链接正常")
    else:
        print("❌ 部分修复验证失败")
    
    print("=" * 60)
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())