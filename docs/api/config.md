# 配置管理 API

配置管理 API 提供了对 Nacos 配置的基本操作，包括获取、发布、删除配置以及监听配置变更。

## 获取配置

```python
def get(
    self,
    data_id: str,
    group: str = "DEFAULT_GROUP",
    tenant: str = "",
    *,
    serializer: Optional[Union[Serializer, bool]] = None,
    cache: Optional[BaseCache] = None,
    default: Optional[str] = None,
) -> Union[str, dict, None]:
    """
    获取配置内容

    参数:
        data_id: 配置 ID
        group: 配置分组，默认为 DEFAULT_GROUP
        tenant: 命名空间 ID
        serializer: 序列化器，True 表示自动检测格式
        cache: 缓存实例，默认为全局内存缓存
        default: 默认值，当配置不存在或网络错误且缓存未命中时返回
    
    返回:
        配置内容（字符串或序列化后的对象），失败时返回 default 或 None
    
    异常:
        HTTPResponseError: 配置不存在且未提供 default
    """
```

### 缓存降级行为

| 场景 | 返回值 |
|------|--------|
| 服务正常 | 从服务获取的内容 |
| 服务异常 + 缓存命中 | 缓存内容 |
| 服务异常 + 缓存未命中 | `default` 或 `None` |
| 配置不存在 (404) | `default` 或抛异常 |

### 使用示例

```python
from use_nacos import NacosClient

client = NacosClient("http://localhost:8848")

# 基本获取
config = client.config.get("app.yaml", "DEFAULT_GROUP")

# 带默认值（推荐生产环境使用）
config = client.config.get(
    "app.yaml",
    "DEFAULT_GROUP",
    default="name: myapp\nversion: 1.0.0"
)

# 自动解析 YAML/JSON
config = client.config.get("app.yaml", "DEFAULT_GROUP", serializer=True)
print(config["name"])  # 直接访问字段
```

## 发布配置

```python
async def publish_config(
    self,
    data_id: str,
    group: str,
    content: str
) -> bool:
    """
    发布配置

    参数:
        data_id: 配置 ID
        group: 配置分组
        content: 配置内容
    
    返回:
        是否发布成功
    """
```

## 删除配置

```python
async def remove_config(
    self,
    data_id: str,
    group: str = "DEFAULT_GROUP"
) -> bool:
    """
    删除配置

    参数:
        data_id: 配置 ID
        group: 配置分组，默认为 DEFAULT_GROUP
    
    返回:
        是否删除成功
    """
```

## 监听配置

```python
async def add_config_watcher(
    self,
    data_id: str,
    group: str,
    callback: Callable[[str, str, str, str], Awaitable[None]]
) -> None:
    """
    添加配置监听器

    参数:
        data_id: 配置 ID
        group: 配置分组
        callback: 配置变更回调函数
            callback 参数: (namespace, data_id, group, content)
    """
```

## 使用示例

```python
from use_nacos import NacosClient

client = NacosClient("http://localhost:8848")

# 获取配置
config = await client.get_config("app.yaml", "DEFAULT_GROUP")
print(f"配置内容: {config}")

# 发布配置
success = await client.publish_config(
    "app.yaml",
    "DEFAULT_GROUP",
    "name: myapp\nversion: 1.0.0"
)
print(f"发布配置: {'成功' if success else '失败'}")

# 监听配置变更
async def on_config_change(namespace, data_id, group, content):
    print(f"配置已更新: {content}")

await client.add_config_watcher(
    "app.yaml",
    "DEFAULT_GROUP",
    on_config_change
)
```