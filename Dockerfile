# 使用官方 Python 3.11 镜像作为基础镜像
# 尝试使用国内可访问的镜像源 (Docker Hub 官方源在国内访问不稳定)
FROM python:3.11-slim

# 替换 Debian 软件源为中科大 HTTPS 镜像，尝试规避网络阻断
RUN sed -i 's/http:\/\/deb.debian.org/https:\/\/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/http:\/\/security.debian.org/https:\/\/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV TZ Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    supervisor \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 设置 PostgreSQL 数据目录
ENV PGDATA /var/lib/postgresql/data
RUN mkdir -p "$PGDATA" && chown -R postgres:postgres "$PGDATA"

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装 Python 依赖
# 使用清华源加速 pip 安装
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install gunicorn -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置 Nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# 配置 Supervisord
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 复制入口脚本
COPY docker/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# 暴露端口
EXPOSE 80 8000 5432 6379

# 启动命令
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]