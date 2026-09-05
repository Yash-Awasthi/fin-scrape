# AutoGen金融分析系统部署指南

## 1. 部署概述

本指南详细介绍了AutoGen金融分析系统的部署流程，包括开发环境、测试环境和生产环境的部署方法。系统支持多种部署方式，包括传统的直接部署、Docker容器部署以及Kubernetes集群部署。

## 2. 系统要求

### 2.1 硬件要求

- **开发环境**: 至少4GB RAM，2核CPU，10GB硬盘空间
- **测试环境**: 至少8GB RAM，4核CPU，20GB硬盘空间
- **生产环境**: 至少16GB RAM，8核CPU，50GB硬盘空间

### 2.2 软件要求

- **操作系统**: 
  - Windows: Windows 10/11或Windows Server 2019+ 
  - Linux: Ubuntu 20.04+, CentOS 8+, Debian 11+ 
  - macOS: macOS 10.15+ 
- **Python**: 3.8或更高版本
- **数据库**: 
  - PostgreSQL: 12或更高版本
  - Redis: 6.0或更高版本
- **容器技术** (可选): 
  - Docker: 20.10或更高版本
  - Kubernetes: 1.20或更高版本
- **Web服务器** (生产环境): 
  - Nginx: 1.20或更高版本
  - Apache: 2.4或更高版本

### 2.3 网络要求

- **开发环境**: 互联网连接（用于下载依赖和金融数据）
- **生产环境**: 
  - 稳定的互联网连接
  - 防火墙配置开放必要端口（默认8000）
  - 可选的负载均衡器

## 3. 环境准备

### 3.1 数据库准备

#### 3.1.1 PostgreSQL安装与配置

**Ubuntu/Debian**: 
```bash
# 安装PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE autogen_financial;
CREATE USER autogen_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE autogen_financial TO autogen_user;
\q
```

**CentOS/RHEL**: 
```bash
# 安装PostgreSQL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE autogen_financial;
CREATE USER autogen_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE autogen_financial TO autogen_user;
\q
```

**Windows**: 
1. 从官方网站下载PostgreSQL安装包并安装
2. 打开pgAdmin工具
3. 创建数据库`autogen_financial`和用户`autogen_user`，并授予适当权限

### 3.1.2 Redis安装与配置

**Ubuntu/Debian**: 
```bash
# 安装Redis
sudo apt update
sudo apt install redis-server

# 启动Redis服务
sudo systemctl start redis
sudo systemctl enable redis
```

**CentOS/RHEL**: 
```bash
# 安装Redis
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis
```

**Windows**: 
1. 从Redis官方网站下载Windows版本
2. 解压并运行redis-server.exe
3. 可选：配置redis.windows-service.conf并安装为Windows服务

## 4. 直接部署（开发环境）

### 4.1 安装步骤

1. **克隆项目代码**
   ```bash
   git clone https://github.com/your-username/autogen-financial-analysis.git
   cd autogen-financial-analysis
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，添加必要的配置
   ```

   `.env`文件示例：
   ```bash
   # API密钥
   ALPHA_VANTAGE_API_KEY=your_key_here
   
   # 数据库配置
   DATABASE_URL=postgresql://autogen_user:your_password@localhost:5432/autogen_financial
   REDIS_URL=redis://localhost:6379/0
   
   # 安全配置
   SECRET_KEY=your_secret_key_here
   JWT_SECRET=your_jwt_secret_here
   ```

5. **初始化数据库**
   ```bash
   python -m src.data.initialize_database
   ```

6. **启动应用**
   ```bash
   # 启动开发服务器
   python -m src.api.app --reload
   ```

### 4.2 验证部署

打开浏览器，访问 `http://localhost:8000`，如果能看到系统首页，则说明部署成功。

您也可以使用命令行工具验证API接口：
```bash
curl -X GET "http://localhost:8000/api/v1/system/status"
```

## 5. Docker容器部署

### 5.1 Docker安装

**Ubuntu/Debian**: 
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
# 注销并重新登录以应用组更改
```

**CentOS/RHEL**: 
```bash
sudo yum install docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
# 注销并重新登录以应用组更改
```

**Windows**: 
1. 从Docker官方网站下载Docker Desktop并安装
2. 启动Docker Desktop并完成初始化设置

### 5.2 使用Docker Compose部署

1. **准备环境变量文件**
   ```bash
   cp .env.example .env
   # 编辑.env文件，添加必要的配置
   ```

2. **使用Docker Compose启动服务**
   ```bash
   # 启动所有服务
   docker-compose up -d
   
   # 查看服务状态
   docker-compose ps
   
   # 查看日志
   docker-compose logs -f
   ```

3. **验证部署**
   打开浏览器，访问 `http://localhost:8000`

### 5.3 自定义Docker镜像

如果您需要自定义Docker镜像，可以按照以下步骤操作：

1. **修改Dockerfile**（如果需要）

2. **构建自定义镜像**
   ```bash
   docker build -t autogen-financial:custom .
   ```

3. **使用自定义镜像**
   修改`docker-compose.yml`文件，将镜像名称改为`autogen-financial:custom`

## 6. Kubernetes部署

### 6.1 Kubernetes环境准备

1. **安装kubectl**
   请参考[官方文档](https://kubernetes.io/docs/tasks/tools/)安装kubectl

2. **设置Kubernetes集群**
   您可以使用以下方式之一：
   - **Minikube**: 适合开发和测试环境
   - **Docker Desktop**: 内置Kubernetes支持
   - **云服务商的Kubernetes服务**: 如AWS EKS, Google GKE, Azure AKS等

### 6.2 部署步骤

1. **准备配置文件**
   确保`k8s/deployment.yaml`文件中的配置适合您的环境

2. **创建命名空间**
   ```bash
   kubectl create namespace autogen-financial
   ```

3. **创建Secret**
   ```bash
   # 创建API密钥Secret
   kubectl create secret generic api-secrets \
     --namespace=autogen-financial \
     --from-literal=openai-api-key=your_openai_api_key \
     --from-literal=alpha-vantage-key=your_alpha_vantage_api_key
     
   # 创建PostgreSQL密码Secret
   kubectl create secret generic postgres-secrets \
     --namespace=autogen-financial \
     --from-literal=password=your_postgres_password
   ```

4. **部署应用**
   ```bash
   kubectl apply -f k8s/deployment.yaml -n autogen-financial
   ```

5. **验证部署**
   ```bash
   # 查看Pod状态
   kubectl get pods -n autogen-financial
   
   # 查看服务
   kubectl get svc -n autogen-financial
   
   # 查看日志
   kubectl logs -f <pod-name> -n autogen-financial
   ```

6. **访问应用**
   如果使用LoadBalancer类型的服务，您可以通过外部IP访问应用；如果使用NodePort或ClusterIP，可以通过端口转发访问：
   ```bash
   kubectl port-forward svc/autogen-service 8000:80 -n autogen-financial
   ```
   然后访问 `http://localhost:8000`

### 6.3 扩缩容

```bash
# 扩展副本数量
kubectl scale deployment autogen-financial --replicas=5 -n autogen-financial

# 缩小副本数量
kubectl scale deployment autogen-financial --replicas=2 -n autogen-financial
```

## 7. 生产环境部署最佳实践

### 7.1 安全配置

1. **使用HTTPS**
   - 配置SSL证书
   - 重定向HTTP请求到HTTPS
   - 配置HSTS (HTTP Strict Transport Security)

2. **数据库安全**
   - 使用强密码
   - 限制数据库访问IP
   - 定期备份数据库
   - 启用加密连接

3. **API安全**
   - 实施JWT认证
   - 配置适当的权限控制
   - 设置API速率限制
   - 验证所有用户输入

4. **环境变量安全**
   - 不要在代码中硬编码敏感信息
   - 使用Secret管理敏感数据
   - 限制对环境变量的访问

### 7.2 性能优化

1. **配置缓存**
   - 优化Redis缓存配置
   - 设置合理的缓存过期时间
   - 监控缓存命中率

2. **数据库优化**
   - 为常用查询添加索引
   - 优化数据库连接池
   - 定期清理和优化数据库

3. **负载均衡**
   - 配置Nginx或其他负载均衡器
   - 实现健康检查和自动故障转移
   - 根据负载调整服务器数量

### 7.3 监控与告警

1. **配置Prometheus监控**
   - 部署Prometheus服务器
   - 配置监控指标和告警规则
   - 设置数据保留策略

2. **配置Grafana仪表板**
   - 连接Prometheus数据源
   - 创建系统监控仪表板
   - 设置可视化图表和告警通知

3. **日志管理**
   - 配置结构化日志
   - 设置适当的日志级别
   - 实现日志轮转和归档
   - 可选：使用ELK Stack等日志管理系统

### 7.4 备份与恢复

1. **数据库备份**
   - 实施定期数据库备份策略
   - 验证备份的完整性
   - 测试恢复流程

2. **配置备份**
   - 备份配置文件和环境变量
   - 版本控制重要配置

3. **代码备份**
   - 使用Git等版本控制系统
   - 定期推送到远程仓库

## 8. 常见部署问题解决

### 8.1 数据库连接问题

**症状**: 应用无法连接到PostgreSQL或Redis数据库

**解决方案**: 
- 检查数据库服务是否正在运行
- 验证连接参数是否正确（主机、端口、用户名、密码）
- 检查防火墙设置是否允许连接
- 验证数据库用户权限

### 8.2 API密钥问题

**症状**: 无法获取金融数据或API调用失败

**解决方案**: 
- 验证API密钥是否正确
- 检查API密钥是否过期
- 检查API调用限制是否被触发
- 查看系统日志以获取详细错误信息

### 8.3 性能问题

**症状**: 系统响应缓慢或分析任务执行时间过长

**解决方案**: 
- 增加系统资源（CPU、内存）
- 优化数据库查询
- 调整缓存配置
- 增加应用实例数量（使用负载均衡）
- 监控系统性能指标，找出瓶颈

### 8.4 容器相关问题

**症状**: Docker容器无法启动或频繁重启

**解决方案**: 
- 查看容器日志以获取详细错误信息
- 检查资源限制是否合理
- 验证挂载的卷和权限
- 检查环境变量配置

### 8.5 Kubernetes相关问题

**症状**: Pod无法启动或服务不可用

**解决方案**: 
- 使用`kubectl describe pod`查看Pod事件和状态
- 查看容器日志
- 验证资源请求和限制
- 检查服务和Ingress配置
- 验证网络策略和防火墙规则

## 9. 系统更新

### 9.1 直接部署更新

```bash
# 拉取最新代码
git pull origin main

# 安装新依赖
pip install -r requirements.txt --upgrade

# 重启应用
python -m src.api.app
```

### 9.2 Docker部署更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 9.3 Kubernetes部署更新

```bash
# 拉取最新代码
git pull origin main

# 构建并推送新镜像
docker build -t autogen-financial:latest .
docker push your-registry/autogen-financial:latest

# 更新部署
kubectl apply -f k8s/deployment.yaml -n autogen-financial

# 或者直接更新镜像
kubectl set image deployment/autogen-financial autogen-api=your-registry/autogen-financial:latest -n autogen-financial
```

## 10. 扩展系统

### 10.1 添加新的数据源

1. 在`src/data/data_sources.py`中实现新的数据源类
2. 更新`config.yaml`文件中的数据源配置
3. 在`src/data/data_collector.py`中注册新的数据源
4. 重新部署系统

### 10.2 添加新的分析功能

1. 在适当的分析模块中实现新功能
2. 更新API接口以支持新功能
3. 更新前端界面（如果需要）
4. 编写测试用例
5. 重新部署系统

### 10.3 水平扩展

- **直接部署**: 部署多个实例并使用负载均衡器
- **Docker部署**: 增加容器数量并配置负载均衡
- **Kubernetes部署**: 增加副本数量或使用Horizontal Pod Autoscaler

## 11. 附录：配置文件参考

### 11.1 Docker Compose配置示例

```yaml
version: '3'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://autogen_user:password@postgres:5432/autogen_financial
      - REDIS_URL=redis://redis:6379/0
      - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./output:/app/output
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=autogen_financial
      - POSTGRES_USER=autogen_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 11.2 Nginx配置示例

```nginx
upstream autogen_api {
    server localhost:8000;
    # 如果有多个后端服务器，可以在这里添加
    # server localhost:8001;
    # server localhost:8002;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    location / {
        proxy_pass http://autogen_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket支持
    location /ws {
        proxy_pass http://autogen_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # 静态文件服务
    location /reports {
        alias /path/to/your/reports;
        autoindex on;
    }
}
```

---

**注意**: 本系统仅供学习和研究使用，不构成投资建议。投资有风险，请谨慎决策。