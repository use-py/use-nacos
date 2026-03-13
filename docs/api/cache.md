# Cache API

use-nacos 提供了灵活的缓存机制，用于缓存 Nacos 配置和服务实例信息，提高性能并减少网络请求。

## 概述

缓存系统支持多种实现方式：

- **BaseCache** - 缓存抽象基类
- **MemoryCache** - 内存缓存（默认）
- **FileCache** - 文件缓存（持久化）

## BaseCache

抽象基类，定义了缓存的基本接口。

### 方法

#### `set(key, value)`

设置缓存值。

**参数:**
- `key` (str): 缓存键
- `value` (Any): 缓存值

**示例:**
```python
from use_nacos.cache import BaseCache

cache = BaseCache()  # 需要子类实现
cache.set("service_config", {"timeout": 30})
```

---

#### `get(key)`

获取缓存值。

**参数:**
- `key` (str): 缓存键

**返回:** 缓存值，如果不存在则返回 `None`

**示例:**
```python
config = cache.get("service_config")
print(config)  # {"timeout": 30}
```

---

#### `exists(key)`

检查缓存键是否存在。

**参数:**
- `key` (str): 缓存键

**返回:** `bool`

**示例:**
```python
if cache.exists("service_config"):
    print("Config is cached")
```

---

## MemoryCache

内存缓存实现，数据存储在进程内存中。

### 特性

- ⚡ **高性能** - 无 I/O 开销
- ⚠️ **非持久化** - 进程重启后数据丢失
- 🔄 **自动管理** - 自动处理存储

### 使用方法

```python
from use_nacos.cache import MemoryCache

cache = MemoryCache()
cache.set("config", {"timeout": 30})
config = cache.get("config")
```

### 适用场景

- 配置项缓存
- 临时数据存储
- 高频访问的数据

### 注意事项

- 不适合存储大量数据
- 进程重启后数据丢失
- 多进程之间不共享

---

## FileCache

文件缓存实现，数据持久化到本地文件。

### 特性

- 💾 **持久化** - 数据保存到文件
- 🔄 **跨进程** - 多进程可以共享缓存
- 📝 **JSON 格式** - 易于查看和编辑

### 使用方法

```python
from use_nacos.cache import FileCache

# 使用默认路径 (_nacos_config_cache.json)
cache = FileCache()

# 使用自定义路径
cache = FileCache("/path/to/cache.json")

cache.set("config", {"timeout": 30})
config = cache.get("config")
```

### 参数

**`file_path`** (Optional[str]): 缓存文件路径

- 默认值: `_nacos_config_cache.json`
- 如果文件不存在，会自动创建

### 适用场景

- 需要持久化的配置缓存
- 多进程共享缓存
- 需要查看缓存内容

### 注意事项

- 文件 I/O 有一定性能开销
- 需要文件系统写入权限
- 缓存文件会随时间增长

---

## 全局缓存实例

use-nacos 提供了一个全局的内存缓存实例：

```python
from use_nacos.cache import memory_cache

# 直接使用全局实例
memory_cache.set("config", {"timeout": 30})
config = memory_cache.get("config")
```

这个实例通常在内部使用，用于缓存配置和服务实例信息。

---

## 选择合适的缓存实现

| 需求 | 推荐实现 | 原因 |
|------|---------|------|
| 最高性能 | MemoryCache | 无 I/O 开销 |
| 数据持久化 | FileCache | 保存到文件 |
| 多进程共享 | FileCache | 进程间共享文件 |
| 默认使用 | MemoryCache (全局) | 预配置，即用即开 |

---

## 自定义缓存

如果需要自定义缓存实现，可以继承 `BaseCache`：

```python
from use_nacos.cache import BaseCache
import redis

class RedisCache(BaseCache):
    def __init__(self, redis_client):
        self.client = redis_client

    def set(self, key, value):
        self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)

    def exists(self, key):
        return self.client.exists(key) > 0

# 使用
import redis
redis_client = redis.Redis(host='localhost', port=6379)
cache = RedisCache(redis_client)
```

---

## 最佳实践

1. **合理使用缓存** - 只缓存需要的数据，避免内存浪费
2. **设置过期时间** - 对于 FileCache，定期清理旧数据
3. **错误处理** - 缓存读取失败时，从服务端重新获取
4. **监控缓存命中率** - 评估缓存效果

---

## 相关文档

- [配置管理 API](./config.md)
- [服务发现 API](./discovery.md)
- [客户端 API](./client.md)
