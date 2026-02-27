#!/usr/bin/env python3
"""
简化修复验证测试
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_database():
    """测试数据库"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'knowledge_%'")
            tables = cursor.fetchall()
        
        if len(tables) >= 3:
            print("✅ 数据库表修复成功")
            return True
        else:
            print("❌ 数据库表修复失败")
            return False
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_server():
    """测试服务器启动"""
    import subprocess
    import time
    
    try:
        # 启动服务器
        process = subprocess.Popen(
            ['python3', 'manage.py', 'runserver', '0.0.0.0:8001'],
            cwd='/home/csq/workspace/bestBugBot',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # 等待服务器启动
        time.sleep(3)
        
        # 测试访问
        import requests
        try:
            response = requests.get('http://localhost:8001/api/v1/dashboard/stats/', timeout=2)
            if response.status_code == 200:
                print("✅ 服务器启动成功，API正常")
                success = True
            else:
                print(f"❌ API返回错误状态码: {response.status_code}")
                success = False
        except:
            print("❌ 无法访问API")
            success = False
        finally:
            process.terminate()
            process.wait()
        
        return success
    except Exception as e:
        print(f"❌ 服务器测试失败: {e}")
        return False

def main():
    print("=" * 50)
    print("修复验证")
    print("=" * 50)
    
    all_passed = True
    
    print("\n1. 测试数据库修复...")
    if not test_database():
        all_passed = False
    
    print("\n2. 测试服务器启动...")
    if not test_server():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ 所有修复验证通过！")
    else:
        print("❌ 部分修复验证失败")
    
    print("=" * 50)
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())