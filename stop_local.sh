#!/bin/bash
# 本地开发环境停止脚本

PROJECT_DIR="/home/csq/workspace/entropyx-ai"

echo "正在停止 Django 服务器..."

# 查找并停止 Django 进程
PIDS=$(pgrep -f "manage.py runserver")

if [ -z "$PIDS" ]; then
    echo "✓ Django 服务器未运行"
    exit 0
fi

# 停止进程
for PID in $PIDS; do
    kill $PID 2>/dev/null
    echo "  已停止进程: $PID"
done

# 等待进程完全停止
sleep 2

# 验证是否已停止
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "✗ 部分进程仍在运行，强制停止..."
    pkill -9 -f "manage.py runserver"
    sleep 1
fi

if pgrep -f "manage.py runserver" > /dev/null; then
    echo "✗ 停止失败"
    exit 1
else
    echo "✓ Django 服务器已停止"
    echo ""
    echo "重新启动: ./start_local.sh"
fi