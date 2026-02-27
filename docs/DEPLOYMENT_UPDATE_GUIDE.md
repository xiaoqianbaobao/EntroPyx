# 远程内网机器部署更新指南

本文档说明如何在本地更新代码后，重新打包并部署到远程内网机器。

## 前置条件

- 本地环境：已安装 Docker、Python 3.x
- 远程内网机器：已成功部署过第一次，无需安装 Docker

## 部署更新流程

### 步骤 1: 本地更新代码

在本地进行代码修改后，确保以下文件已更新：

1. **requirements.txt** - 如果添加了新的 Python 依赖
2. **项目代码** - apps/、config/、templates/ 等目录下的代码修改
3. **Dockerfile** - 如果需要修改容器配置

### 步骤 2: 更新 Python 依赖包（如有新增）

如果修改了 `requirements.txt`，需要下载新的依赖包：

```bash
cd /home/csq/workspace/entropyx-ai

# 使用虚拟环境中的 pip 下载依赖包
venv/bin/pip download --dest python_packages --only-binary :all: -r requirements.txt

# 如果某个包没有二进制版本，可以尝试：
venv/bin/pip download --dest python_packages -r requirements.txt
```

**注意**：确保下载的包与 Dockerfile 中指定的 Python 版本（3.11）兼容。

### 步骤 3: 重新构建 Docker 镜像

```bash
cd /home/csq/workspace/entropyx-ai

# 构建 Docker 镜像
docker build -t entropyx-ai:latest .
```

### 步骤 4: 重新打包离线部署包

```bash
cd /home/csq/workspace/entropyx-ai

# 执行打包脚本
./build-complete-offline-package.sh
```

打包脚本会：
1. 复制最新的项目文件到 `offline-docker-package/project_files/`
2. 复制最新的 Python 依赖包到 `offline-docker-package/python_packages/`
3. 导出 Docker 镜像到 `offline-docker-package/entropyx-ai-image.tar`

### 步骤 5: 传输到远程内网机器

```bash
# 使用 scp 传输（替换为实际的远程地址）
scp -r offline-docker-package user@remote-server:/tmp/

# 或者先打包成 tar.gz 再传输
tar -czf offline-docker-package.tar.gz offline-docker-package/
scp offline-docker-package.tar.gz user@remote-server:/tmp/
```

### 步骤 6: 远程机器部署

登录到远程内网机器，执行以下操作：

```bash
# 如果传输的是 tar.gz，先解压
cd /tmp
tar -xzf offline-docker-package.tar.gz
cd offline-docker-package

# 停止并删除旧容器
cd /opt/entropyx-ai
docker-compose down

# 备份旧数据（可选但推荐）
mkdir -p /opt/entropyx-ai-backup
cp -r /opt/entropyx-ai/data /opt/entropyx-ai-backup/
cp -r /opt/entropyx-ai/media /opt/entropyx-ai-backup/

# 复制新文件
cp -r /tmp/offline-docker-package/project_files/* /opt/entropyx-ai/
cp /tmp/offline-docker-package/docker-compose-offline.yml /opt/entropyx-ai/docker-compose.yml

# 加载新的 Docker 镜像
docker load -i /tmp/offline-docker-package/entropyx-ai-image.tar

# 重新启动容器
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 步骤 7: 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查服务是否正常
curl http://localhost:8000

# 查看详细日志
docker-compose logs web
```

## 常见问题

### 问题 1: 缺少 Python 依赖包

**现象**：容器启动时报错 `ModuleNotFoundError`

**解决**：
1. 检查 `requirements.txt` 是否包含所有依赖
2. 重新执行步骤 2，下载缺失的包
3. 确保 `python_packages/` 目录中有对应的 `.whl` 文件

### 问题 2: Docker 镜像加载失败

**现象**：`docker load` 报错

**解决**：
1. 确保传输的 tar 文件完整（检查文件大小）
2. 重新执行步骤 3 和 4，重新构建和打包

### 问题 3: 数据库迁移失败

**现象**：`migrate` 命令报错

**解决**：
```bash
# 手动执行迁移
docker-compose exec web python manage.py migrate

# 如果失败，尝试回滚
docker-compose exec web python manage.py migrate fake
```

### 问题 4: 静态文件未更新

**现象**：前端页面样式或脚本未更新

**解决**：
```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --noinput

# 重启容器
docker-compose restart web
```

## 优化建议

### 1. 减小包大小

如果目标机器已有 Docker，可以删除以下内容以减小包体积：

```bash
cd offline-docker-package

# 删除 Docker 二进制文件（如果目标机器已有 Docker）
rm -rf docker_bin/

# 删除重复的镜像（只保留一个）
rm -f entropyx-ai-complete-image.tar
```

优化后包大小可减少约 500MB。

### 2. 增量更新（高级）

如果只是修改了少量代码，可以只传输修改的文件：

```bash
# 只传输修改的文件
scp apps/your_app/*.py user@remote-server:/opt/entropyx-ai/apps/your_app/

# 重启容器以应用更改
ssh user@remote-server "cd /opt/entropyx-ai && docker-compose restart web"
```

**注意**：增量更新不适用于：
- 修改了依赖包
- 修改了 Dockerfile
- 修改了静态文件
- 数据库结构变更

### 3. 版本管理

建议为每次发布打上版本标签：

```bash
# 构建时添加版本标签
docker build -t entropyx-ai:v1.0.1 .
docker tag entropyx-ai:v1.0.1 entropyx-ai:latest

# 导出镜像时包含版本信息
docker save entropyx-ai:v1.0.1 > offline-docker-package/entropyx-ai-v1.0.1.tar
```

## 快速检查清单

在传输到远程机器前，确认以下事项：

- [ ] 所有代码修改已提交或保存
- [ ] `requirements.txt` 已更新（如需要）
- [ ] 新的依赖包已下载到 `python_packages/`
- [ ] Docker 镜像构建成功
- [ ] 打包脚本执行成功
- [ ] 打包后的文件大小合理（约 300-400MB）

## 回滚方案

如果新版本部署失败，可以快速回滚到旧版本：

```bash
# 停止新容器
cd /opt/entropyx-ai
docker-compose down

# 恢复备份数据
cp -r /opt/entropyx-ai-backup/data/* /opt/entropyx-ai/data/
cp -r /opt/entropyx-ai-backup/media/* /opt/entropyx-ai/media/

# 重新启动旧版本（如果之前保留了旧镜像）
docker load -i /path/to/old-image.tar
docker-compose up -d
```

## 联系与支持

如遇到问题，请检查：
1. Docker 容器日志：`docker-compose logs`
2. Django 应用日志：`/opt/entropyx-ai/logs/`
3. 系统日志：`journalctl -u docker`