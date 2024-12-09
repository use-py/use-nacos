# 快速开始

本指南将帮助您快速开始使用 use-nacos。

## 安装

使用 pip 安装 use-nacos：

```bash
pip install use-nacos
```

## 基本使用

### 创建客户端

```python
from use_nacos import NacosClient

client = NacosClient(
    server_addresses="http://localhost:8848",
    namespace="public",
    username="nacos",  # 可选
    password="nacos"   # 可选
)
```

### 配置管理

获取配置：

```python
# 获取配置
config = await client.get_config(
    data_id="config.yaml",
    group="DEFAULT_GROUP"
)

# 发布配置
success = await client.publish_config(
    data_id="config.yaml",
    group="DEFAULT_GROUP",
    content="key: value"
)

# 删除配置
success = await client.remove_config(
    data_id="config.yaml",
    group="DEFAULT_GROUP"
)
```

### 服务发现

注册服务：

```python
success = await client.register_instance(
    service_name="my-service",
    ip="192.168.1.10",
    port=8080,
    metadata={
        "version": "1.0.0"
    }
)

# 获取服务实例列表
instances = await client.get_instances(
    service_name="my-service"
)
```

## 配置监听

监听配置变更：

```python
async def config_changed(namespace, data_id, group, content):
    print(f"配置已更新: {content}")

# 添加配置监听器
await client.add_config_watcher(
    data_id="config.yaml",
    group="DEFAULT_GROUP",
    callback=config_changed
)
```

## 错误处理

use-nacos 使用异常来处理错误情况：

```python
from use_nacos.exceptions import NacosException

try:
    config = await client.get_config("config.yaml", "DEFAULT_GROUP")
except NacosException as e:
    print(f"获取配置失败: {e}")
```

## 下一步

- 了解更多[配置管理](../api/config)功能
- 探索[服务发现](../api/discovery)特性
- 查看[认证配置](../api/auth)说明
