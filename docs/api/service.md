# Service API

服务管理 API 提供了服务的创建、查询、更新和删除功能。

## 概述

服务是 Nacos 服务发现的顶层概念，一个服务可以包含多个实例。服务 API 提供了服务生命周期的完整管理。

### 核心功能

- 📝 **创建服务** - 在 Nacos 中注册新服务
- 🔍 **查询服务** - 查询服务列表和详情
- 🔄 **更新服务** - 修改服务的配置
- 🗑️ **删除服务** - 从 Nacos 中删除服务

## ServiceEndpoint

服务管理端点，支持同步和异步两种模式。

---

## 基础操作

### create

创建新服务。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |
| `protect_threshold` | float | ❌ | 保护阈值 (默认 0) |
| `metadata` | str | ❌ | 元数据 (JSON 字符串) |
| `selector` | str | ❌ | 选择器类型 |

**参数说明:**

- **protect_threshold**: 保护阈值，当健康实例占比低于此值时，仍返回部分不健康实例（避免雪崩）
- **metadata**: 服务的自定义元数据，如版本、描述等
- **selector**: 实例选择器类型，如 `random`、`roundRobin` 等

**示例:**

```python
from use_nacos import NacosClient

client = NacosClient(server="localhost:8848")

# 创建基本服务
client.service.create(
    service_name="my-service"
)

# 创建带配置的服务
client.service.create(
    service_name="my-service",
    namespace_id="public",
    group_name="DEFAULT_GROUP",
    protect_threshold=0.5,
    metadata='{"version": "1.0", "owner": "team-a"}'
)

# 使用选择器
client.service.create(
    service_name="my-service",
    selector="random"
)
```

---

### delete

删除服务。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |

**示例:**

```python
# 删除服务
client.service.delete(
    service_name="my-service"
)

# 删除指定命名空间的服务
client.service.delete(
    service_name="my-service",
    namespace_id="public",
    group_name="DEFAULT_GROUP"
)
```

**⚠️ 注意:**
- 删除服务会同时删除该服务下的所有实例
- 此操作不可恢复，请谨慎使用

---

### list

查询服务列表（支持分页）。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page_no` | int | ❌ | 页码 (默认 1) |
| `page_size` | int | ❌ | 每页数量 (默认 20) |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |

**返回:** 服务列表信息

```python
{
    "doms": ["service1", "service2", ...],
    "count": 100,
    "pageSize": 20,
    "pageNo": 1
}
```

**示例:**

```python
# 查询第一页服务列表
result = client.service.list()
print(result["doms"])  # 服务名称列表
print(result["count"])  # 服务总数

# 分页查询
page1 = client.service.list(page_no=1, page_size=10)
page2 = client.service.list(page_no=2, page_size=10)

# 查询指定命名空间的服务
services = client.service.list(
    namespace_id="public",
    group_name="DEFAULT_GROUP"
)
```

---

### update

更新服务信息。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |
| `protect_threshold` | float | ❌ | 保护阈值 |
| `metadata` | str | ❌ | 元数据 (JSON 字符串) |
| `selector` | str | ❌ | 选择器类型 |

**示例:**

```python
# 更新保护阈值
client.service.update(
    service_name="my-service",
    protect_threshold=0.8
)

# 更新元数据
client.service.update(
    service_name="my-service",
    metadata='{"version": "2.0", "status": "stable"}'
)

# 更新选择器
client.service.update(
    service_name="my-service",
    selector="roundRobin"
)
```

---

### get

获取单个服务的详细信息。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `namespace_id` | str | ❌ | 命名空间 ID (默认 '') |
| `group_name` | str | ❌ | 分组名称 |

**返回:** 服务详细信息

**示例:**

```python
# 获取服务详情
service = client.service.get(
    service_name="my-service"
)
print(service)

# 获取指定命名空间的服务
service = client.service.get(
    service_name="my-service",
    namespace_id="public",
    group_name="DEFAULT_GROUP"
)
```

---

## 完整示例

### 服务生命周期管理

```python
from use_nacos import NacosClient

client = NacosClient(server="localhost:8848")

# 1. 创建服务
client.service.create(
    service_name="order-service",
    namespace_id="prod",
    protect_threshold=0.5,
    metadata='{"version": "1.0", "team": "order-team"}'
)

# 2. 查询服务
services = client.service.list(namespace_id="prod")
if "order-service" in services["doms"]:
    print("Order service created successfully")

# 3. 获取服务详情
service_detail = client.service.get(
    service_name="order-service",
    namespace_id="prod"
)
print(service_detail)

# 4. 更新服务
client.service.update(
    service_name="order-service",
    namespace_id="prod",
    protect_threshold=0.8
)

# 5. 删除服务（谨慎使用！）
# client.service.delete(
#     service_name="order-service",
#     namespace_id="prod"
# )
```

### 批量操作

```python
# 批量创建服务
service_names = ["user-service", "order-service", "product-service"]

for name in service_names:
    client.service.create(
        service_name=name,
        namespace_id="public"
    )

# 批量查询
services = client.service.list(namespace_id="public")
active_services = services["doms"]

# 过滤特定服务
if "user-service" in active_services:
    print("User service is active")
```

---

## 异步支持

`ServiceEndpoint` 的所有方法都支持异步调用：

```python
from use_nacos import NacosAsyncClient

client = NacosAsyncClient(server="localhost:8848")

# 异步创建服务
await client.service.create(
    service_name="my-service"
)

# 异步查询服务列表
services = await client.service.list()
print(services["doms"])

# 异步更新服务
await client.service.update(
    service_name="my-service",
    protect_threshold=0.8
)
```

---

## 参数详解

### protect_threshold (保护阈值)

保护阈值用于防止服务雪崩效应。

**工作原理:**
- 当健康实例占比低于保护阈值时，Nacos 仍会返回部分不健康实例
- 这可以避免所有健康实例过载，同时给不健康实例恢复的机会

**推荐设置:**

| 场景 | 推荐值 | 说明 |
|------|---------|------|
| 高可用 | 0.0 | 不启用保护 |
| 一般服务 | 0.5 | 保护 50% 的实例 |
| 关键服务 | 0.8 | 保守策略 |

**示例:**

```python
# 关键服务：保守策略
client.service.create(
    service_name="payment-service",
    protect_threshold=0.8  # 当健康实例少于 80% 时启用保护
)

# 一般服务：标准策略
client.service.create(
    service_name="cache-service",
    protect_threshold=0.5  # 当健康实例少于 50% 时启用保护
)
```

---

### metadata (元数据)

元数据用于存储服务的自定义信息。

**常见用途:**
- 版本信息
- 所属团队
- 环境标识
- 服务描述
- 监控配置

**示例:**

```python
import json

# 构建元数据
metadata = {
    "version": "2.1.0",
    "team": "backend",
    "environment": "production",
    "description": "Order processing service",
    "owner": "backend-team@example.com"
}

# 创建服务时设置元数据
client.service.create(
    service_name="order-service",
    metadata=json.dumps(metadata)
)

# 更新元数据
client.service.update(
    service_name="order-service",
    metadata=json.dumps({
        **metadata,
        "version": "2.2.0"  # 更新版本
    })
)
```

---

## 最佳实践

### 1. 服务命名规范

```python
# ✅ 好的命名
"user-service"
"order-service"
"payment-api"

# ❌ 不好的命名
"service1"
"my-service"
"test"
```

### 2. 使用命名空间隔离环境

```python
# 生产环境
client.service.create(
    service_name="user-service",
    namespace_id="prod"
)

# 开发环境
client.service.create(
    service_name="user-service",
    namespace_id="dev"
)

# 测试环境
client.service.create(
    service_name="user-service",
    namespace_id="test"
)
```

### 3. 合理设置保护阈值

```python
# 关键核心服务：高保护阈值
client.service.create(
    service_name="core-service",
    protect_threshold=0.8
)

# 边缘服务：低保护阈值
client.service.create(
    service_name="logging-service",
    protect_threshold=0.2
)
```

### 4. 元数据管理

```python
# 使用标准化的元数据结构
SERVICE_METADATA_TEMPLATE = {
    "version": "1.0.0",
    "team": "",
    "environment": "production",
    "description": "",
    "documentation": ""
}

# 创建服务时填充模板
metadata = SERVICE_METADATA_TEMPLATE.copy()
metadata.update({
    "version": "2.1.0",
    "team": "backend",
    "description": "User authentication service"
})

client.service.create(
    service_name="auth-service",
    metadata=json.dumps(metadata)
)
```

### 5. 分页查询

```python
def list_all_services(client, namespace_id=None, page_size=100):
    """获取所有服务（处理分页）"""
    all_services = []
    page_no = 1

    while True:
        result = client.service.list(
            page_no=page_no,
            page_size=page_size,
            namespace_id=namespace_id
        )

        services = result.get("doms", [])
        all_services.extend(services)

        # 检查是否还有更多数据
        if len(services) < page_size:
            break

        page_no += 1

    return all_services

# 使用
all_services = list_all_services(client, namespace_id="public")
print(f"Total services: {len(all_services)}")
```

---

## 故障排查

### 问题：服务创建失败

**可能原因:**
1. 服务已存在
2. 命名空间不存在
3. 权限不足

**解决方法:**

```python
# 检查服务是否存在
services = client.service.list()
if "my-service" in services["doms"]:
    print("Service already exists")
else:
    client.service.create(service_name="my-service")
```

### 问题：查询不到服务

**可能原因:**
1. 命名空间不匹配
2. 分组名称错误
3. 服务已被删除

**解决方法:**

```python
# 检查所有命名空间
for ns in ["public", "dev", "test"]:
    services = client.service.list(namespace_id=ns)
    if "my-service" in services["doms"]:
        print(f"Service found in namespace: {ns}")
        break
```

### 问题：更新服务无效

**可能原因:**
1. 服务不存在
2. 参数格式错误
3. 元数据 JSON 格式错误

**解决方法:**

```python
import json

# 验证元数据格式
try:
    metadata = json.loads(metadata_str)
    print("Metadata is valid")
except json.JSONDecodeError as e:
    print(f"Invalid JSON metadata: {e}")
```

---

## 相关文档

- [实例管理 API](./instance.md)
- [配置管理 API](./config.md)
- [客户端 API](./client.md)
- [认证 API](./auth.md)
