# AutoGen金融分析系统API文档

## 1. 概述

AutoGen金融分析系统提供了功能丰富的RESTful API接口，方便与其他系统集成和自动化操作。本文档详细描述了系统提供的所有API端点、请求参数、响应格式和使用示例。

## 2. 基础信息

### 2.1 API版本

当前API版本：v1

### 2.2 基础URL

```
http://localhost:8000/api/v1/
```

### 2.3 认证方式

系统API使用JWT（JSON Web Token）进行身份认证：

1. 获取令牌：通过`/auth/login`端点获取JWT令牌
2. 在后续请求的Authorization头中包含令牌：`Bearer {token}`

### 2.4 响应格式

所有API响应都使用JSON格式，包含以下基本字段：

```json
{
  "status": "success" | "error",
  "data": { ... },  // 成功响应的数据
  "error": "..."   // 错误信息（仅在status为error时存在）
}
```

### 2.5 错误码

| 错误码 | 描述 | HTTP状态码 |
|-------|------|------------|
| 40001 | 请求参数错误 | 400 |
| 40101 | 未授权访问 | 401 |
| 40301 | 权限不足 | 403 |
| 40401 | 资源不存在 | 404 |
| 50001 | 服务器内部错误 | 500 |
| 50002 | 数据分析失败 | 500 |
| 50003 | 数据源连接失败 | 500 |

## 3. 认证API

### 3.1 用户登录

**请求**: POST /auth/login

**请求参数**: 

```json
{
  "username": "string",
  "password": "string"
}
```

**响应**: 

```json
{
  "status": "success",
  "data": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**示例**: 

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### 3.2 刷新令牌

**请求**: POST /auth/refresh

**请求头**: Authorization: Bearer {refresh_token}

**响应**: 

```json
{
  "status": "success",
  "data": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**示例**: 

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Authorization: Bearer {refresh_token}"
```

### 3.3 验证令牌

**请求**: GET /auth/verify

**请求头**: Authorization: Bearer {token}

**响应**: 

```json
{
  "status": "success",
  "data": {
    "valid": true,
    "username": "string",
    "expires_at": "2023-12-31T23:59:59Z"
  }
}
```

**示例**: 

```bash
curl -X GET "http://localhost:8000/api/v1/auth/verify" \
  -H "Authorization: Bearer {token}"
```

## 4. 分析API

### 4.1 创建分析任务

**请求**: POST /analysis

**请求头**: Authorization: Bearer {token}

**请求参数**: 

```json
{
  "symbols": ["string"],  // 股票代码列表
  "analysis_type": "quick" | "comprehensive" | "detailed" | "portfolio" | "risk" | "financial",  // 分析类型
  "export_formats": ["html" | "pdf" | "json" | "csv" | "excel" | "markdown" | "xml"],  // 导出格式
  "portfolio_weights": {  // 投资组合权重（可选，仅对多个股票有效）
    "AAPL": 0.5,
    "MSFT": 0.3,
    "GOOG": 0.2
  },
  "options": {  // 其他选项
    "use_cache": true
  }
}
```

**响应**: 

```json
{
  "status": "success",
  "data": {
    "request_id": "string",
    "status": "pending",
    "message": "分析任务已创建"
  }
}
```

**示例**: 

```bash
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "analysis_type": "comprehensive",
    "export_formats": ["html", "pdf"]
  }'
```

### 4.2 获取分析任务状态

**请求**: GET /analysis/{task_id}

**请求头**: Authorization: Bearer {token}

**路径参数**: 
- `task_id`: 任务ID

**响应**: 

```json
{
  "status": "success",
  "data": {
    "request": {
      "id": "string",
      "symbols": ["AAPL", "MSFT"],
      "analysis_type": "comprehensive",
      "export_formats": ["html", "pdf"],
      "created_at": "2023-12-01T12:00:00Z"
    },
    "status": "pending" | "running" | "completed" | "failed" | "cancelled",
    "progress": 60,  // 进度百分比
    "export_files": ["filename1.html", "filename2.pdf"],
    "created_at": "2023-12-01T12:00:00Z"
  }
}
```

**示例**: 

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/{task_id}" \
  -H "Authorization: Bearer {token}"
```

### 4.3 获取分析结果

**请求**: GET /analysis/{task_id}/result

**请求头**: Authorization: Bearer {token}

**路径参数**: 
- `task_id`: 任务ID

**响应**: 

```json
{
  "status": "success",
  "data": {
    "request_id": "string",
    "results": {
      "symbol": "AAPL",
      "financial_metrics": {
        "roe": 20.5,
        "roa": 10.2,
        "profit_margin": 15.8,
        "debt_ratio": 45.3
      },
      "risk_metrics": {
        "volatility": 22.5,
        "beta": 1.15,
        "var_95": 3.2
      },
      "summary": {
        "score": 85,
        "rating": "买入",
        "overview": "..."
      },
      "recommendations": [
        "盈利能力优秀，具备长期投资价值",
        "负债率适中，关注偿债能力"
      ],
      "data_quality": {
        "overall_score": 0.95
      },
      "analysis_date": "2023-12-01T12:00:00Z"
    },
    "export_files": ["AAPL_analysis_20231201_120000.html", "AAPL_analysis_20231201_120000.pdf"]
  }
}
```

**示例**: 

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/{task_id}/result" \
  -H "Authorization: Bearer {token}"
```

### 4.4 取消分析任务

**请求**: DELETE /analysis/{task_id}

**请求头**: Authorization: Bearer {token}

**路径参数**: 
- `task_id`: 任务ID

**响应**: 

```json
{
  "status": "success",
  "data": {
    "message": "任务已取消"
  }
}
```

**示例**: 

```bash
curl -X DELETE "http://localhost:8000/api/v1/analysis/{task_id}" \
  -H "Authorization: Bearer {token}"
```

### 4.5 获取分析任务列表

**请求**: GET /analysis

**请求头**: Authorization: Bearer {token}

**查询参数**: 
- `status`: 任务状态（可选）
- `limit`: 返回的最大数量（默认：50）
- `offset`: 偏移量（默认：0）

**响应**: 

```json
{
  "status": "success",
  "data": [
    {
      "request": {
        "id": "string",
        "symbols": ["AAPL"],
        "analysis_type": "comprehensive",
        "created_at": "2023-12-01T12:00:00Z"
      },
      "status": "completed",
      "progress": 100,
      "export_files": ["AAPL_analysis_20231201_120000.html"],
      "created_at": "2023-12-01T12:00:00Z"
    }
  ]
}
```

**示例**: 

```bash
curl -X GET "http://localhost:8000/api/v1/analysis?status=completed&limit=10" \
  -H "Authorization: Bearer {token}"
```

## 5. 系统管理API

### 5.1 获取系统状态

**请求**: GET /system/status

**请求头**: Authorization: Bearer {token}

**响应**: 

```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "uptime": 86400,
    "active_tasks": 5,
    "completed_tasks": 100,
    "failed_tasks": 2,
    "system_resources": {
      "cpu_usage": 15.5,
      "memory_usage": 780,
      "memory_total": 16384
    },
    "api_version": "1.0.0"
  }
}
```

**示例**: 

```bash
curl -X GET "http://localhost:8000/api/v1/system/status" \
  -H "Authorization: Bearer {token}"
```

### 5.2 获取系统指标

**请求**: GET /system/metrics

**请求头**: Authorization: Bearer {token}

**响应**: 

```json
{
  "status": "success",
  "data": {
    "cpu_usage": 15.5,
    "memory_usage": 780,
    "disk_usage": 12000,
    "network_in": 1000,
    "network_out": 2000
  }
}
```

**示例**: 

```bash
curl -X GET "http://localhost:8000/api/v1/system/metrics" \
  -H "Authorization: Bearer {token}"
```

## 6. WebSocket API

系统还提供了WebSocket API，用于获取实时更新和推送通知。

### 6.1 连接WebSocket

**URL**: `ws://localhost:8000/ws`

**认证**: 连接时需要提供JWT令牌作为查询参数：`ws://localhost:8000/ws?token={token}`

### 6.2 订阅任务更新

连接建立后，客户端可以订阅任务状态更新：

```json
{
  "type": "subscribe",
  "task_id": "string"
}
```

### 6.3 接收任务更新

客户端会收到分析任务的实时更新：

```json
{
  "type": "task_update",
  "task_id": "string",
  "data": {
    "status": "running",
    "progress": 60,
    "step": "数据收集"
  },
  "timestamp": "2023-12-01T12:05:00Z"
}
```

### 6.4 JavaScript示例

```javascript
const token = "your_jwt_token";
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = function(event) {
  console.log('WebSocket连接已建立');
  // 订阅任务更新
  ws.send(JSON.stringify({
    "type": "subscribe",
    "task_id": "your_task_id"
  }));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  if (data.type === 'task_update') {
    console.log('任务更新:', data.data);
    // 处理任务更新
  }
};

ws.onerror = function(error) {
  console.error('WebSocket错误:', error);
};

ws.onclose = function(event) {
  console.log('WebSocket连接已关闭');
};
```

## 7. API使用最佳实践

### 7.1 认证与安全

- 始终使用HTTPS协议（生产环境）
- 妥善保管JWT令牌，不要在客户端代码中硬编码
- 设置合理的令牌过期时间
- 定期刷新令牌
- 实施适当的访问控制和权限检查

### 7.2 性能优化

- 使用批量操作减少API调用次数
- 利用缓存减少重复请求
- 合理设置请求超时时间
- 实现重试机制处理临时错误
- 监控API响应时间并进行优化

### 7.3 错误处理

- 检查并处理所有API错误响应
- 实现适当的重试逻辑
- 记录详细的错误日志
- 向用户提供友好的错误信息
- 区分临时错误和永久错误

### 7.4 分页与过滤

- 对大型数据集使用分页
- 使用过滤参数减少数据传输量
- 按需求选择适当的数据字段
- 实现增量同步机制减少数据传输

## 8. 常见问题

**Q: 如何处理API速率限制？**
A: 系统实现了速率限制机制，建议在应用中实现重试逻辑，并尊重API的速率限制。

**Q: 如何获取大量历史数据？**
A: 对于大量历史数据，建议使用较小的时间范围分批获取，或使用系统提供的数据导出功能。

**Q: API返回的金融数据与实际市场数据有差异怎么办？**
A: 数据可能存在延迟，请检查数据的更新时间。如果发现持续的差异，请联系技术支持。

**Q: 如何调试API请求？**
A: 可以使用Postman、curl等工具测试API请求，检查请求参数和响应结果。

**Q: API版本更新会影响现有应用吗？**
A: 我们会尽力保持API的向后兼容性，但建议在新版本发布后及时测试和更新您的应用。

## 9. API变更日志

### v1.0.0 (2023-12-01)
- 初始版本发布
- 实现认证API
- 实现分析API
- 实现系统管理API
- 实现WebSocket API

---

**注意**: 本API仅供学习和研究使用，不构成投资建议。投资有风险，请谨慎决策。