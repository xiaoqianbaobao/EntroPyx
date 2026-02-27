#!/bin/bash
set -e

# 初始化 PostgreSQL
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL..."
    mkdir -p "$PGDATA"
    chown -R postgres:postgres "$PGDATA"
    chmod 700 "$PGDATA"
    
    su - postgres -c "initdb -D $PGDATA"
    
    # 临时启动 PostgreSQL 并设置密码
    su - postgres -c "pg_ctl -D $PGDATA -w start"
    su - postgres -c "psql --command \"CREATE USER $POSTGRES_USER WITH SUPERUSER PASSWORD '$POSTGRES_PASSWORD';\""
    su - postgres -c "createdb -O $POSTGRES_USER $POSTGRES_DB"
    su - postgres -c "pg_ctl -D $PGDATA -m fast -w stop"
    
    # 修改 pg_hba.conf 允许本地连接
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
    echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"
fi

# 确保 Redis 目录权限
mkdir -p /var/lib/redis
chown -R redis:redis /var/lib/redis
mkdir -p /var/log/redis
chown -R redis:redis /var/log/redis

# 启动 Redis (后台运行，供 Django 初始化使用)
redis-server --daemonize yes

# 启动 PostgreSQL (后台运行，供 Django 初始化使用)
su - postgres -c "pg_ctl -D $PGDATA -w start"

# Django 初始化
echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

# 创建超级用户 (如果有环境变量)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput || true
fi

# 关闭临时启动的服务
su - postgres -c "pg_ctl -D $PGDATA -m fast -w stop"
redis-cli shutdown

# 启动 Supervisord
echo "Starting Supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf