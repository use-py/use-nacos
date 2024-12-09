# use-nacos 简介

use-nacos 是一个用于 Python 的 Nacos 客户端库，提供了简单而强大的 API 来集成 Nacos 的配置管理和服务发现功能。

## 特性

- **配置管理**
  - 动态配置获取和更新
  - 配置变更监听
  - 支持多种配置格式（YAML、JSON、Properties）

- **服务发现**
  - 服务注册与注销
  - 服务健康检查
  - 服务实例查询

- **高级特性**
  - 命名空间支持
  - 认证和加密
  - 集群支持
  - 容错和重试机制

## 系统要求

- Python 3.8+
- aiohttp
- pydantic

## 安装

使用 pip 安装：

```bash
pip install use-nacos
```

## 快速预览

```python
from use_nacos import NacosClient

# 创建客户端实例
client = NacosClient(
    server_addresses="http://localhost:8848",
    namespace="public"
)

# 获取配置
config = await client.get_config("config.yaml", "DEFAULT_GROUP")

# 监听配置变更
async def config_changed(namespace, data_id, group, content):
    print(f"Config changed: {content}")

await client.add_config_watcher(
    "config.yaml",
    "DEFAULT_GROUP",
    config_changed
)
```