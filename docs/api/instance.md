# Instance API

实例管理 API 提供了服务实例的注册、发现、健康检查和负载均衡功能。

## 概述

实例是 Nacos 服务发现的基本单位，每个服务可以有多个实例。实例 API 提供了完整的实例生命周期管理。

### 核心功能

- 📝 **注册实例** - 将服务实例注册到 Nacos
- 🔍 **发现实例** - 查询服务的实例列表
- ❤️ **健康检查** - 实例健康状态管理和心跳检测
- ⚖️ **负载均衡** - 加权随机选择健康实例
- 🔄 **更新实例** - 修改实例的配置和元数据

## InstanceEndpoint

实例管理端点，支持同步和异步两种模式。

### InstanceType

实例类型定义：

```python
class InstanceType(TypedDict):
    ip: str              # 实例 IP 地址
    port: int            # 实例端口
    weight: float         # 权重 (默认 1.0)
    enabled: bool         # 是否启用 (默认 True)
    healthy: bool         # 是否健康 (默认 True)
    metadata: Optional[dict]  # 元数据
```

---

## 基础操作

### register

注册服务实例。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `ip` | str | ✅ | 实例 IP 地址 |
| `port` | int | ✅ | 实例端口 |
| `namespace_id` | str | ❌ | 命名空间 ID (默认 '') |
| `weight` | float | ❌ | 权重 (默认 1.0) |
| `enabled` | bool | ❌ | 是否启用 (默认 True) |
| `healthy` | bool | ❌ | 是否健康 (默认 True) |
| `metadata` | str | ❌ | 元数据 (JSON 字符串) |
| `cluster_name` | str | ❌ | 集群名称 |
| `group_name` | str | ❌ | 分组名称 |
| `ephemeral` | bool | ❌ | 是否临时实例 |

**示例:**

```python
from use_nacos import NacosClient

client = NacosClient(server="localhost:8848")

# 注册实例
client.instance.register(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080,
    weight=2.0,
    metadata={"version": "1.0", "env": "prod"}
)
```

---

### delete

删除服务实例。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `ip` | str | ✅ | 实例 IP 地址 |
| `port` | str | ✅ | 实例端口 |
| `group_name` | str | ❌ | 分组名称 |
| `cluster_name` | str | ❌ | 集群名称 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `ephemeral` | bool | ❌ | 是否临时实例 |

**示例:**

```python
client.instance.delete(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080
)
```

---

### list

查询服务实例列表。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |
| `clusters` | str | ❌ | 集群名称 (逗号分隔) |
| `healthy_only` | bool | ❌ | 只返回健康实例 (默认 False) |

**返回:** 包含实例列表的字典

**示例:**

```python
# 查询所有实例
instances = client.instance.list(
    service_name="my-service"
)
print(instances["hosts"])

# 只查询健康实例
healthy_instances = client.instance.list(
    service_name="my-service",
    healthy_only=True
)
```

---

### update

更新实例信息。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `ip` | str | ✅ | 实例 IP 地址 |
| `port` | int | ✅ | 实例端口 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `weight` | float | ❌ | 权重 |
| `enabled` | bool | ❌ | 是否启用 |
| `metadata` | dict | ❌ | 元数据 (字典) |
| `cluster_name` | str | ❌ | 集群名称 |
| `group_name` | str | ❌ | 分组名称 |
| `ephemeral` | bool | ❌ | 是否临时实例 |

**示例:**

```python
client.instance.update(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080,
    weight=3.0,
    enabled=True,
    metadata={"version": "2.0"}
)
```

---

### get

获取单个实例信息。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `ip` | str | ✅ | 实例 IP 地址 |
| `port` | int | ✅ | 实例端口 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |
| `cluster` | str | ❌ | 集群名称 |
| `healthy_only` | bool | ❌ | 只返回健康实例 |
| `ephemeral` | bool | ❌ | 是否临时实例 |

**示例:**

```python
instance = client.instance.get(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080
)
```

---

## 健康检查

### beat

发送心跳（保持实例存活）。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `ip` | str | ✅ | 实例 IP 地址 |
| `port` | int | ✅ | 实例端口 |
| `weight` | float | ❌ | 权重 (默认 1.0) |
| `namespace_id` | str | ❌ | 命名空间 ID (默认 '') |
| `group_name` | str | ❌ | 分组名称 |
| `ephemeral` | bool | ❌ | 是否临时实例 |

**示例:**

```python
# 发送单次心跳
client.instance.beat(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080
)
```

---

### heartbeat

自动心跳（定时发送心跳）。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `ip` | str | ✅ | 实例 IP 地址 |
| `port` | int | ✅ | 实例端口 |
| `weight` | float | ❌ | 权重 (默认 1.0) |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |
| `ephemeral` | bool | ❌ | 是否临时实例 |
| `interval` | int | ❌ | 心跳间隔 (ms，默认 1000) |
| `skip_exception` | bool | ❌ | 跳过异常 (默认 True) |

**返回:** 停止事件，调用 `cancel()` 可停止心跳

**示例:**

```python
# 启动自动心跳
stop_event = client.instance.heartbeat(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080,
    interval=5000  # 每 5 秒发送一次
)

# 停止心跳
stop_event.cancel()
```

---

### update_health

更新实例健康状态。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `ip` | str | ✅ | 实例 IP 地址 |
| `port` | int | ✅ | 实例端口 |
| `healthy` | bool | ✅ | 健康状态 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |
| `cluster_name` | str | ❌ | 集群名称 |

**示例:**

```python
# 标记为不健康
client.instance.update_health(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080,
    healthy=False
)

# 标记为健康
client.instance.update_health(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080,
    healthy=True
)
```

---

## 负载均衡

### get_one_healthy

获取一个健康的实例（加权随机选择）。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `namespace_id` | str | ❌ | 命名空间 ID |
| `group_name` | str | ❌ | 分组名称 |
| `clusters` | str | ❌ | 集群名称 (逗号分隔) |

**返回:** 一个健康的实例 (InstanceType)

**抛出:** `EmptyHealthyInstanceError` - 当没有健康实例时

**示例:**

```python
# 获取健康实例
instance = client.instance.get_one_healthy(
    service_name="my-service"
)
print(f"Selected: {instance['ip']}:{instance['port']}")

# 指定集群
instance = client.instance.get_one_healthy(
    service_name="my-service",
    clusters="cluster1,cluster2"
)
```

---

## 直接请求

### request

向实例直接发送 HTTP 请求。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `method` | str | ✅ | HTTP 方法 (GET, POST, etc.) |
| `path` | str | ✅ | 请求路径 |
| `instance` | InstanceType | ❌ | 实例对象 |
| `service_name` | str | ❌ | 服务名称 (与 instance 二选一) |

**示例:**

```python
# 向指定实例发送请求
response = client.instance.request(
    method="GET",
    path="/api/health",
    instance={"ip": "192.168.1.100", "port": 8080}
)

# 向服务的一个健康实例发送请求
response = client.instance.request(
    method="GET",
    path="/api/users",
    service_name="my-service"
)
```

---

## 属性访问

支持通过属性名快速访问服务：

```python
# 直接调用服务
response = client.instance.my_service.get("/api/health")
# 等价于:
# client.instance.request("GET", "/api/health", service_name="my_service")
```

---

## 元数据批量操作

### batch_update_metadata

批量更新实例元数据。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `namespace_id` | str | ✅ | 命名空间 ID |
| `metadata` | dict | ✅ | 元数据 |
| `consistency_type` | str | ❌ | 一致性类型 (ephemeral/persist) |
| `instances` | list | ❌ | 实例列表 |

**示例:**

```python
client.instance.batch_update_metadata(
    service_name="my-service",
    namespace_id="public",
    metadata={"env": "prod", "team": "backend"}
)
```

---

### batch_delete_metadata

批量删除实例元数据。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `service_name` | str | ✅ | 服务名称 |
| `namespace_id` | str | ✅ | 命名空间 ID |
| `metadata` | dict | ✅ | 要删除的元数据 |
| `consistency_type` | str | ❌ | 一致性类型 (ephemeral/persist) |
| `instances` | list | ❌ | 实例列表 |

**示例:**

```python
client.instance.batch_delete_metadata(
    service_name="my-service",
    namespace_id="public",
    metadata={"old_key": ""}
)
```

---

## 异步支持

`InstanceAsyncEndpoint` 提供了所有方法的异步版本：

```python
from use_nacos import NacosAsyncClient

client = NacosAsyncClient(server="localhost:8848")

# 异步注册实例
await client.instance.register(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080
)

# 异步获取健康实例
instance = await client.instance.get_one_healthy(
    service_name="my-service"
)

# 异步心跳
stop_event = await client.instance.heartbeat(
    service_name="my-service",
    ip="192.168.1.100",
    port=8080
)
```

---

## 最佳实践

1. **定期心跳** - 使用 `heartbeat()` 方法保持实例存活
2. **优雅下线** - 下线前调用 `update_health(healthy=False)`
3. **权重配置** - 根据实例性能设置合理的权重
4. **元数据管理** - 使用元数据记录实例的环境、版本等信息
5. **异常处理** - 处理 `EmptyHealthyInstanceError` 异常

---

## 相关文档

- [服务管理 API](./service.md)
- [配置管理 API](./config.md)
- [客户端 API](./client.md)
