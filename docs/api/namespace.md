# Namespace API

命名空间管理 API 提供了 Nacos 命名空间的创建、查询、更新和删除功能。

## 概述

命名空间用于实现租户隔离，不同的命名空间下可以有相同的服务名和配置名。

### 核心功能

- 📝 **创建命名空间** - 注册新的命名空间
- 🔍 **查询命名空间** - 列出所有命名空间
- 🔄 **更新命名空间** - 修改命名空间配置
- 🗑️ **删除命名空间** - 删除不再使用的命名空间

## NamespaceEndpoint

命名空间管理端点，支持同步和异步两种模式。

---

## 基础操作

### create

创建新命名空间。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `custom_namespace_id` | str | ✅ | 自定义命名空间 ID |
| `namespace_name` | str | ✅ | 命名空间名称 |
| `namespace_desc` | str | ❌ | 命名空间描述 |

**参数说明:**

- **custom_namespace_id**: 自定义的命名空间 ID，如 `public`, `dev`, `test` 等
- **namespace_name**: 命名空间的显示名称
- **namespace_desc**: 命名空间的描述信息

**示例:**

```python
from use_nacos import NacosClient

client = NacosClient(server="localhost:8848")

# 创建基本命名空间
client.namespace.create(
    custom_namespace_id="public",
    namespace_name="公共命名空间"
)

# 创建带描述的命名空间
client.namespace.create(
    custom_namespace_id="dev",
    namespace_name="开发环境",
    namespace_desc="用于开发测试的命名空间"
)

# 创建测试环境命名空间
client.namespace.create(
    custom_namespace_id="test",
    namespace_name="测试环境",
    namespace_desc="用于自动化测试的命名空间"
)
```

---

### delete

删除命名空间。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `namespace_id` | str | ✅ | 命名空间 ID |

**示例:**

```python
# 删除命名空间
client.namespace.delete(
    namespace_id="test"
)

# 删除开发环境
client.namespace.delete(
    namespace_id="dev"
)
```

**⚠️ 注意:**
- 删除命名空间会同时删除该命名空间下的所有服务和配置
- 此操作不可恢复，请谨慎使用
- 不能删除系统默认的命名空间（通常是 `public` 或空字符串）

---

### list

查询所有命名空间列表。

**参数:** 无

**返回:** 命名空间列表

**示例:**

```python
# 查询所有命名空间
namespaces = client.namespace.list()
print(namespaces)

# 返回格式示例
# [
#   {
#       "namespace": "",
#       "namespaceShowName": "public",
#       "namespaceId": "",
#       "namespaceDesc": "公共命名空间"
#   },
#   {
#       "namespace": "dev",
#       "namespaceShowName": "开发环境",
#       "namespaceId": "dev",
#       "namespaceDesc": "用于开发测试"
#   },
#   ...
# ]
```

---

### update

更新命名空间信息。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `namespace` | str | ✅ | 命名空间 ID |
| `namespace_show_name` | str | ✅ | 显示名称 |
| `namespace_desc` | str | ✅ | 描述信息 |

**示例:**

```python
# 更新命名空间信息
client.namespace.update(
    namespace="dev",
    namespace_show_name="开发环境（v2）",
    namespace_desc="用于开发测试和集成测试"
)
```

---

## 完整示例

### 命名空间生命周期管理

```python
from use_nacos import NacosClient

client = NacosClient(server="localhost:8848")

# 1. 创建命名空间
print("创建命名空间...")
client.namespace.create(
    custom_namespace_id="staging",
    namespace_name="预发布环境",
    namespace_desc="用于预发布和灰度发布"
)

# 2. 查询所有命名空间
print("\n所有命名空间：")
namespaces = client.namespace.list()
for ns in namespaces:
    print(f"  - {ns['namespaceShowName']}: {ns['namespace']} ({ns['namespaceDesc']})")

# 3. 更新命名空间
print("\n更新命名空间...")
client.namespace.update(
    namespace="staging",
    namespace_show_name="预发布环境（更新）",
    namespace_desc="用于预发布和灰度发布 - v2.0"
)

# 4. 删除命名空间（谨慎使用！）
# print("\n删除命名空间...")
# client.namespace.delete(namespace_id="test")
```

### 环境隔离示例

```python
from use_nacos import NacosClient

client = NacosClient(server="localhost:8848")

# 为不同环境创建命名空间
environments = [
    {
        "id": "dev",
        "name": "开发环境",
        "desc": "用于日常开发测试"
    },
    {
        "id": "test",
        "name": "测试环境",
        "desc": "用于自动化测试"
    },
    {
        "id": "staging",
        "name": "预发布环境",
        "desc": "用于预发布和灰度发布"
    },
    {
        "id": "prod",
        "name": "生产环境",
        "desc": "用于正式生产"
    }
]

# 批量创建命名空间
for env in environments:
    try:
        client.namespace.create(
            custom_namespace_id=env["id"],
            namespace_name=env["name"],
            namespace_desc=env["desc"]
        )
        print(f"✅ 创建命名空间: {env['name']}")
    except Exception as e:
        print(f"❌ 创建失败 {env['name']}: {e}")
        # 可能已存在，忽略错误

# 验证所有命名空间
print("\n验证命名空间：")
namespaces = client.namespace.list()
ns_ids = [ns['namespace'] for ns in namespaces]

for env in environments:
    if env["id"] in ns_ids:
        print(f"✅ {env['name']}: 已存在")
    else:
        print(f"⚠️  {env['name']}: 不存在")
```

### 命名空间与服务隔离

```python
from use_nacos import NacosClient

client = NacosClient(server="localhost:8848")

# 确保命名空间存在
try:
    client.namespace.create(
        custom_namespace_id="dev",
        namespace_name="开发环境"
    )
except:
    pass  # 可能已存在

# 在开发环境创建服务
client.service.create(
    service_name="user-service",
    namespace_id="dev",
    protect_threshold=0.5
)

# 在生产环境创建服务
client.service.create(
    service_name="user-service",
    namespace_id="prod",  # 假设 prod 命名空间已存在
    protect_threshold=0.8
)

# 查询不同环境的服务
dev_services = client.service.list(namespace_id="dev")
prod_services = client.service.list(namespace_id="prod")

print(f"开发环境服务数: {dev_services['count']}")
print(f"生产环境服务数: {prod_services['count']}")
```

---

## 异步支持

所有方法都支持异步调用：

```python
from use_nacos import NacosAsyncClient

client = NacosAsyncClient(server="localhost:8848")

# 异步创建命名空间
await client.namespace.create(
    custom_namespace_id="async-dev",
    namespace_name="异步开发环境"
)

# 异步查询命名空间
namespaces = await client.namespace.list()
print(f"找到 {len(namespaces)} 个命名空间")

# 异步更新命名空间
await client.namespace.update(
    namespace="async-dev",
    namespace_show_name="异步开发环境（更新）",
    namespace_desc="用于异步开发测试"
)
```

---

## 最佳实践

### 1. 命名空间命名规范

```python
# ✅ 推荐的命名
environments = ["dev", "test", "staging", "prod"]
teams = ["backend", "frontend", "data"]

# 组合使用
namespace = f"{env}-{team}"  # "dev-backend"

# ❌ 不推荐的命名
# "namespace1", "test123", "random_name"
```

### 2. 命名空间隔离策略

```python
# 环境隔离
env_namespaces = ["dev", "test", "staging", "prod"]

# 团队隔离
team_namespaces = ["team-a", "team-b", "team-c"]

# 业务线隔离
business_namespaces = ["order", "payment", "user"]

# 选择适合的隔离策略
```

### 3. 命名空间清理

```python
def cleanup_test_namespaces(client, dry_run=True):
    """清理测试环境命名空间"""
    namespaces = client.namespace.list()
    
    for ns in namespaces:
        ns_id = ns['namespace']
        
        # 只清理测试环境的命名空间
        if 'test' in ns_id.lower():
            if dry_run:
                print(f"[DRY RUN] 删除: {ns['namespaceShowName']}")
            else:
                try:
                    client.namespace.delete(namespace_id=ns_id)
                    print(f"✅ 已删除: {ns['namespaceShowName']}")
                except Exception as e:
                    print(f"❌ 删除失败: {e}")

# 使用
cleanup_test_namespaces(client, dry_run=True)  # 预演
# cleanup_test_namespaces(client, dry_run=False)  # 实际执行
```

### 4. 命名空间监控

```python
import time
from use_nacos import NacosClient

client = NacosClient(server="localhost:8848")

def monitor_namespaces():
    """监控命名空间数量"""
    while True:
        namespaces = client.namespace.list()
        
        print(f"当前命名空间数: {len(namespaces)}")
        print("命名空间列表:")
        for ns in namespaces:
            print(f"  - {ns['namespaceShowName']}: {ns['namespace']}")
        
        # 5 分钟检查一次
        time.sleep(300)

# 使用（实际应该用定时任务）
# monitor_namespaces()
```

---

## 参数详解

### custom_namespace_id

自定义命名空间 ID，用于标识命名空间。

**命名规范:**
- 只能包含字母、数字、连字符
- 不能以连字符开头或结尾
- 长度限制：通常 1-128 字符

**常见值:**
- `""` 或 `public` - 公共命名空间（默认）
- `dev` - 开发环境
- `test` - 测试环境
- `staging` - 预发布环境
- `prod` - 生产环境

### namespace_show_name

命名空间的显示名称，用于 UI 展示。

**建议:**
- 使用中文或英文
- 简洁明了
- 包含环境或用途信息

### namespace_desc

命名空间的描述信息，用于说明命名空间的用途。

**建议:**
- 描述命名空间的用途
- 说明适用的场景
- 添加相关约束或注意事项

---

## 故障排查

### 问题：创建命名空间失败

**可能原因:**
1. 命名空间 ID 已存在
2. 命名空间 ID 格式不正确
3. 权限不足

**解决方法:**

```python
# 先检查命名空间是否已存在
namespaces = client.namespace.list()
ns_ids = [ns['namespace'] for ns in namespaces]

if "dev" in ns_ids:
    print("命名空间 dev 已存在")
else:
    client.namespace.create(
        custom_namespace_id="dev",
        namespace_name="开发环境"
    )
```

### 问题：删除命名空间失败

**可能原因:**
1. 命名空间不存在
2. 命名空间下还有服务或配置
3. 权限不足
4. 尝试删除系统默认命名空间

**解决方法:**

```python
# 1. 检查命名空间是否存在
namespaces = client.namespace.list()
ns_ids = [ns['namespace'] for ns in namespaces]

if "test" not in ns_ids:
    print("命名空间不存在")

# 2. 清空命名空间下的服务和配置
# 需要先删除该命名空间下的所有服务

# 3. 再删除命名空间
client.namespace.delete(namespace_id="test")
```

### 问题：查询不到命名空间

**可能原因:**
1. 命名空间已被删除
2. 命名空间 ID 不正确

**解决方法:**

```python
# 列出所有命名空间
namespaces = client.namespace.list()

# 查找特定的命名空间
target_ns = None
for ns in namespaces:
    if ns['namespace'] == "dev":
        target_ns = ns
        break

if target_ns:
    print(f"找到命名空间: {target_ns['namespaceShowName']}")
else:
    print("未找到命名空间")
```

---

## 相关文档

- [服务管理 API](./service.md)
- [实例管理 API](./instance.md)
- [配置管理 API](./config.md)
- [客户端 API](./client.md)
