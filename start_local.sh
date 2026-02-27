#!/bin/bash
# 本地开发环境启动脚本

# 设置环境变量
export USE_SQLITE=True
export DJANGO_SETTINGS_MODULE=config.settings

# 项目目录
PROJECT_DIR="/home/csq/workspace/entropyx-ai"
cd "$PROJECT_DIR"

# 虚拟环境
VENV="$PROJECT_DIR/venv"
PYTHON="$VENV/bin/python"

echo "========================================="
echo "EntropyX-AI 本地开发环境"
echo "========================================="
echo ""

# 检查Django进程是否已经运行
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "✓ Django 服务器已在运行"
    echo "  访问地址: http://localhost:8000"
    echo "  管理后台: http://localhost:8000/admin/"
    echo "  管理员账号: admin / admin123"
    echo ""
    echo "查看日志: tail -f $PROJECT_DIR/logs/django.log"
    echo "停止服务: ./stop_local.sh"
    exit 0
fi

# 创建必要的目录
mkdir -p "$PROJECT_DIR/media" "$PROJECT_DIR/repos" "$PROJECT_DIR/data" "$PROJECT_DIR/logs"

# 数据库迁移
echo "步骤 1/4: 检查数据库迁移..."
$PYTHON manage.py migrate --noinput

# 收集静态文件
echo "步骤 2/4: 收集静态文件..."
$PYTHON manage.py collectstatic --noinput

# 启动Django服务器
echo "步骤 3/4: 启动Django开发服务器..."
nohup $PYTHON manage.py runserver 0.0.0.0:8000 > "$PROJECT_DIR/logs/django.log" 2>&1 &
sleep 3

# 验证服务是否启动
echo "步骤 4/4: 验证服务状态..."
if pgrep -f "manage.py runserver" > /dev/null; then
    echo ""
    echo "========================================="
    echo "✓ 服务启动成功!"
    echo "========================================="
    echo ""
    echo "访问地址:"
    echo "  主页:     http://localhost:8000"
    echo "  管理后台: http://localhost:8000/admin/"
    echo ""
    echo "管理员账号:"
    echo "  用户名: admin"
    echo "  密码:   admin123"
    echo ""
    echo "常用命令:"
    echo "  查看日志: tail -f $PROJECT_DIR/logs/django.log"
    echo "  停止服务: ./stop_local.sh"
    echo "  重启服务: ./stop_local.sh && ./start_local.sh"
    echo ""
else
    echo ""
    echo "✗ 服务启动失败，请查看日志:"
    echo "  tail -f $PROJECT_DIR/logs/django.log"
    exit 1
fi