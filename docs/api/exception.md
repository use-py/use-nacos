# Exception API

异常类提供了清晰的错误处理和诊断机制。

## 概述

use-nacos 定义了专门的异常类，用于处理 Nacos API 调用过程中可能出现的各种错误。

### 异常层次

```
Exception
├── HTTPResponseError      # HTTP 响应错误
└── EmptyHealthyInstanceError  # 无健康实例错误
```

---

## HTTPResponseError

HTTP 响应错误，当 Nacos API 返回错误状态码时抛出。

### 特性

- 📊 **详细错误信息** - 包含状态码、响应头、响应体
- 🔍 **易于调试** - 完整的 HTTP 响应信息
- 📝 **自定义消息** - 支持自定义错误消息

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `code` | str | 错误代码 (默认: "client_response_error") |
| `status` | int | HTTP 状态码 |
| `headers` | httpx.Headers | 响应头 |
| `body` | str | 响应体 |

### 使用方法

```python
from use_nacos import NacosClient
from use_nacos.exception import HTTPResponseError

client = NacosClient(server="localhost:8848")

try:
    # 可能失败的操作
    service = client.service.get(
        service_name="non-existent-service"
    )
except HTTPResponseError as e:
    print(f"错误代码：{e.code}")
    print(f"状态码：{e.status}")
    print(f"响应头：{e.headers}")
    print(f"响应体：{e.body}")
```

### 常见状态码

| 状态码 | 含义 | 可能原因 |
|--------|------|---------|
| 400 | Bad Request | 参数错误、格式不正确 |
| 401 | Unauthorized | 未认证、Token 过期 |
| 403 | Forbidden | 权限不足 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | Nacos 服务器错误 |
| 502 | Bad Gateway | 网关错误 |
| 503 | Service Unavailable | 服务不可用 |

### 错误处理示例

```python
from use_nacos.exception import HTTPResponseError

def safe_get_service(client, service_name):
    """安全地获取服务信息"""
    try:
        return client.service.get(service_name=service_name)
    except HTTPResponseError as e:
        if e.status == 404:
            print(f"服务不存在：{service_name}")
            return None
        elif e.status == 401:
            print("认证失败，请检查凭证")
            raise
        elif e.status >= 500:
            print("Nacos 服务器错误，请稍后重试")
            raise
        else:
            print(f"未知错误：{e.status}")
            raise

# 使用
service = safe_get_service(client, "my-service")
if service:
    print("服务信息:", service)
```

### 自定义错误消息

```python
from use_nacos.exception import HTTPResponseError

try:
    response = client.service.create(service_name="test")
except HTTPResponseError as e:
    # 使用默认消息
    print(f"默认消息：{e}")
    
    # 或提供自定义消息
    custom_error = HTTPResponseError(
        response=e.response,
        message=f"创建服务失败：服务名称可能已存在"
    )
    print(f"自定义消息：{custom_error}")
```

---

## EmptyHealthyInstanceError

无健康实例错误，当找不到健康的实例时抛出。

### 触发场景

- 调用 `get_one_healthy()` 时没有健康实例
- 所有实例都不健康或已下线
- 服务刚注册，实例还未上报心跳

### 使用方法

```python
from use_nacos import NacosClient
from use_nacos.exception import EmptyHealthyInstanceError

client = NacosClient(server="localhost:8848")

try:
    # 获取健康实例
    instance = client.instance.get_one_healthy(
        service_name="my-service"
    )
    print(f"选中实例：{instance['ip']}:{instance['port']}")
except EmptyHealthyInstanceError as e:
    print(f"没有健康实例：{e}")
    # 处理策略：
    # 1. 使用缓存的实例
    # 2. 返回错误提示
    # 3. 降级到备用服务
```

### 处理策略

#### 1. 使用缓存实例

```python
from use_nacos.cache import memory_cache
from use_nacos.exception import EmptyHealthyInstanceError

def get_instance_with_cache(client, service_name):
    """获取实例，失败时使用缓存"""
    cache_key = f"instance:{service_name}"
    
    try:
        instance = client.instance.get_one_healthy(service_name)
        # 缓存成功的结果
        memory_cache.set(cache_key, instance)
        return instance
    except EmptyHealthyInstanceError:
        # 使用缓存的实例
        cached = memory_cache.get(cache_key)
        if cached:
            print("使用缓存的实例")
            return cached
        raise

# 使用
instance = get_instance_with_cache(client, "my-service")
```

#### 2. 降级策略

```python
from use_nacos.exception import EmptyHealthyInstanceError

def get_instance_with_fallback(client, service_name, fallback_url):
    """获取实例，失败时使用降级地址"""
    try:
        return client.instance.get_one_healthy(service_name)
    except EmptyHealthyInstanceError:
        print(f"服务 {service_name} 不可用，使用降级地址")
        return {
            "ip": fallback_url.split("://")[1].split(":")[0],
            "port": int(fallback_url.split(":")[-1]),
            "weight": 1.0,
            "enabled": True,
            "healthy": False,  # 标记为不健康
            "metadata": {"fallback": "true"}
        }

# 使用
instance = get_instance_with_fallback(
    client,
    "payment-service",
    "http://backup-payment:8080"
)
```

#### 3. 重试机制

```python
import time
from use_nacos.exception import EmptyHealthyInstanceError

def get_instance_with_retry(client, service_name, max_retries=3, delay=1.0):
    """获取实例，失败时重试"""
    for attempt in range(max_retries):
        try:
            return client.instance.get_one_healthy(service_name)
        except EmptyHealthyInstanceError as e:
            if attempt == max_retries - 1:
                raise
            print(f"第 {attempt + 1} 次尝试失败，等待 {delay}s...")
            time.sleep(delay)
    
    raise EmptyHealthyInstanceError("重试后仍无健康实例")

# 使用
instance = get_instance_with_retry(client, "my-service")
```

---

## 最佳实践

### 1. 分层异常处理

```python
from use_nacos import NacosClient
from use_nacos.exception import HTTPResponseError, EmptyHealthyInstanceError

class NacosServiceError(Exception):
    """Nacos 服务错误（自定义包装异常）"""
    pass

def call_nacos_service(client, service_name):
    """调用 Nacos 服务，统一异常处理"""
    try:
        instance = client.instance.get_one_healthy(service_name)
        # 调用实例...
    except EmptyHealthyInstanceError:
        raise NacosServiceError(f"服务 {service_name} 不可用")
    except HTTPResponseError as e:
        if e.status == 404:
            raise NacosServiceError(f"服务 {service_name} 不存在")
        elif e.status >= 500:
            raise NacosServiceError(f"Nacos 服务器错误：{e.status}")
        else:
            raise NacosServiceError(f"Nacos 请求失败：{e.status}")

# 使用
try:
    call_nacos_service(client, "my-service")
except NacosServiceError as e:
    print(f"服务调用失败：{e}")
```

### 2. 日志记录

```python
import logging
from use_nacos.exception import HTTPResponseError

logger = logging.getLogger(__name__)

def log_error_and_continue(client, service_name):
    """记录错误并继续"""
    try:
        service = client.service.get(service_name=service_name)
        return service
    except HTTPResponseError as e:
        logger.error(
            "获取服务失败",
            extra={
                "service": service_name,
                "status": e.status,
                "body": e.body,
            }
        )
        return None

# 使用
service = log_error_and_continue(client, "my-service")
```

### 3. 监控告警

```python
from use_nacos.exception import HTTPResponseError, EmptyHealthyInstanceError

def monitor_nacos_health(client, service_name):
    """监控 Nacos 健康状态"""
    errors = []
    
    try:
        client.instance.get_one_healthy(service_name)
    except EmptyHealthyInstanceError:
        errors.append("no_healthy_instance")
    except HTTPResponseError as e:
        if e.status >= 500:
            errors.append("server_error")
        elif e.status == 401:
            errors.append("auth_error")
        else:
            errors.append(f"http_{e.status}")
    
    if errors:
        # 发送告警
        send_alert(f"Nacos 异常：{', '.join(errors)}")
    
    return errors

def send_alert(message):
    """发送告警（示例）"""
    print(f"🚨 ALERT: {message}")
```

### 4. 优雅降级

```python
from contextlib import contextmanager
from use_nacos.exception import HTTPResponseError, EmptyHealthyInstanceError

@contextmanager
def graceful_degradation(service_name, default_value=None):
    """优雅降级上下文管理器"""
    try:
        yield
    except (HTTPResponseError, EmptyHealthyInstanceError) as e:
        print(f"⚠️  服务 {service_name} 降级：{type(e).__name__}")
        yield default_value

# 使用
with graceful_degradation("config-service", default_value={}):
    config = client.config.get(data_id="app-config")
    print(config)  # 如果失败，使用默认值 {}
```

---

## 异常流程图

```
调用 Nacos API
    │
    ├─ 成功 → 返回结果
    │
    └─ 失败
       │
       ├─ HTTP 错误 (4xx, 5xx)
       │  └─ HTTPResponseError
       │     ├─ 400: 参数错误
       │     ├─ 401: 认证失败
       │     ├─ 403: 权限不足
       │     ├─ 404: 资源不存在
       │     └─ 5xx: 服务器错误
       │
       └─ 无健康实例
          └─ EmptyHealthyInstanceError
```

---

## 调试技巧

### 1. 打印完整错误信息

```python
from use_nacos.exception import HTTPResponseError

try:
    # 操作...
    pass
except HTTPResponseError as e:
    print("=" * 50)
    print("Nacos API 错误详情")
    print("=" * 50)
    print(f"错误代码：{e.code}")
    print(f"状态码：{e.status}")
    print(f"响应头：")
    for key, value in e.headers.items():
        print(f"  {key}: {value}")
    print(f"响应体：{e.body}")
    print("=" * 50)
```

### 2. 使用 traceback

```python
import traceback
from use_nacos.exception import HTTPResponseError

try:
    # 操作...
    pass
except HTTPResponseError as e:
    print("完整堆栈跟踪:")
    traceback.print_exc()
```

### 3. 转换为 JSON 日志

```python
import json
from use_nacos.exception import HTTPResponseError

try:
    # 操作...
    pass
except HTTPResponseError as e:
    error_data = {
        "type": "HTTPResponseError",
        "code": e.code,
        "status": e.status,
        "headers": dict(e.headers),
        "body": e.body,
    }
    print(json.dumps(error_data, indent=2))
```

---

## 相关文档

- [缓存 API](./cache.md)
- [实例管理 API](./instance.md)
- [服务管理 API](./service.md)
- [配置管理 API](./config.md)
