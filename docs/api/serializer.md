# Serializer API

序列化器提供了多种数据格式的解析和转换功能，支持自动识别格式。

## 概述

use-nacos 的序列化器支持解析常见的配置文件格式，包括：

- 📝 **Text** - 纯文本
- 📊 **JSON** - JSON 格式
- 📋 **YAML** - YAML 格式
- ⚙️ **TOML** - TOML 格式
- 🔮 **Auto** - 自动识别格式

## 核心类

### Serializer

抽象基类，定义了序列化器的接口。

#### `__call__(data, **kwargs)`

解析数据。

**参数:**
- `data` (str): 要解析的数据字符串
- `**kwargs`: 额外参数

**返回:** 解析后的数据（通常是 dict 或 str）

**抛出:** `SerializerException` - 解析失败时

---

## 具体实现

### TextSerializer

纯文本序列化器，不做任何解析，直接返回原文。

**特点:**
- ✅ 零开销
- ✅ 适用于纯文本配置
- ✅ 兼容所有格式

**示例:**

```python
from use_nacos.serializer import TextSerializer

serializer = TextSerializer()

# 纯文本
text = serializer("a = 1")
print(text)  # "a = 1"

# 多行文本
text = serializer("a = 1\n[foo]\nb = 2")
print(text)  # "a = 1\n[foo]\nb = 2"
```

**使用场景:**
- 纯文本配置
- 自定义格式
- 需要原样输出的场景

---

### JsonSerializer

JSON 序列化器，解析 JSON 字符串为 Python 字典。

**特点:**
- ✅ 标准 JSON 格式
- ✅ 支持嵌套结构
- ✅ 严格解析

**示例:**

```python
from use_nacos.serializer import JsonSerializer

serializer = JsonSerializer()

# 简单 JSON
data = serializer('{"a": 1}')
print(data)  # {"a": 1}

# 嵌套 JSON
data = serializer('{"a": 1, "foo": {"b": 2}}')
print(data)  # {"a": 1, "foo": {"b": 2}}

# 数组
data = serializer('["item1", "item2"]')
print(data)  # ["item1", "item2"]
```

**使用场景:**
- Nacos 配置中心
- 标准 API 响应
- 复杂数据结构

**错误处理:**

```python
from use_nacos.serializer import SerializerException

try:
    data = serializer('invalid json')
except SerializerException as e:
    print(f"Parse error: {e}")
```

---

### YamlSerializer

YAML 序列化器，解析 YAML 字符串为 Python 字典。

**特点:**
- ✅ 人类可读
- ✅ 支持注释
- ✅ 简洁的语法

**示例:**

```python
from use_nacos.serializer import YamlSerializer

serializer = YamlSerializer()

# 简单 YAML
data = serializer('a: 1')
print(data)  # {"a": 1}

# 嵌套 YAML
data = serializer('a: 1\nfoo:\n  b: 2')
print(data)  # {"a": 1, "foo": {"b": 2}}

# 列表
data = serializer('items:\n  - item1\n  - item2')
print(data)  # {"items": ["item1", "item2"]}
```

**使用场景:**
- 配置文件
- 复杂结构数据
- 需要注释的配置

**YAML 特性:**

```python
# 注释
data = serializer('# This is a comment\na: 1')

# 多行字符串
data = serializer('description: |\n  This is a\n  multi-line string')

# 类型自动转换
data = serializer('count: 10\nenabled: true\nname: "test"')
print(type(data['count']))   # <class 'int'>
print(type(data['enabled'])) # <class 'bool'>
print(type(data['name']))   # <class 'str'>
```

---

### TomlSerializer

TOML 序列化器，解析 TOML 字符串为 Python 字典。

**特点:**
- ✅ 简洁明确
- ✅ 类型明确
- ✅ 适合配置文件

**示例:**

```python
from use_nacos.serializer import TomlSerializer

serializer = TomlSerializer()

# 简单 TOML
data = serializer('a = 1')
print(data)  # {"a": 1}

# 嵌套 TOML
data = serializer('a = 1\n[foo]\nb = 2')
print(data)  # {"a": 1, "foo": {"b": 2}}

# 表格
data = serializer('[servers.alpha]\nhost = "10.0.0.1"\n[servers.beta]\nhost = "10.0.0.2"')
print(data)
# {"servers": {"alpha": {"host": "10.0.0.1"}, "beta": {"host": "10.0.0.2"}}}
```

**使用场景:**
- Rust 项目配置
- 需要类型明确的配置
- 系统配置文件

**TOML 特性:**

```python
# 日期时间
data = serializer('start = 2026-03-13T08:00:00Z')

# 数组
data = serializer('items = ["a", "b", "c"]')

# 布尔值和数字
data = serializer('enabled = true\nport = 8080\ntimeout = 30.5')
```

---

### AutoSerializer

自动序列化器，自动识别并解析数据格式。

**特点:**
- ✅ 智能识别
- ✅ 按优先级尝试
- ✅ 友好的错误提示

**优先级顺序:**

1. JSON
2. TOML
3. YAML
4. Text (fallback)

**示例:**

```python
from use_nacos.serializer import AutoSerializer

serializer = AutoSerializer()

# 自动识别为 TOML
data = serializer('a = 1')
print(data)  # {"a": 1}

# 自动识别为 JSON
data = serializer('{"a": 1}')
print(data)  # {"a": 1}

# 自动识别为 YAML
data = serializer('a: 1')
print(data)  # {"a": 1}

# 无法识别，作为文本
data = serializer('just plain text')
print(data)  # "just plain text"
```

**工作原理:**

```python
# AutoSerializer 内部逻辑
def __call__(self, data) -> dict:
    for serializer in self.serializers:  # [Json, Toml, Yaml, Text]
        try:
            return serializer(data)
        except SerializerException:
            continue  # 尝试下一个
    raise SerializerException("Cannot parse data")
```

**使用场景:**
- 不知道格式的情况
- 支持多种格式
- 用户自定义配置

---

## SerializerException

序列化异常，当解析失败时抛出。

**示例:**

```python
from use_nacos.serializer import (
    JsonSerializer,
    SerializerException
)

serializer = JsonSerializer()

try:
    data = serializer('invalid json {')
except SerializerException as e:
    print(f"Error: {e}")
    # Error: Cannot parse data: 'invalid json {'
```

---

## 实际应用

### 1. Nacos 配置解析

```python
from use_nacos import NacosClient
from use_nacos.serializer import AutoSerializer

client = NacosClient(server="localhost:8848")
serializer = AutoSerializer()

# 获取配置
config_str = client.config.get(
    data_id="app-config",
    group="DEFAULT_GROUP"
)

# 自动解析
config = serializer(config_str)
print(config)
```

### 2. 多格式支持

```python
from use_nacos.serializer import AutoSerializer

serializer = AutoSerializer()

# 支持多种格式
configs = [
    '{"port": 8080}',           # JSON
    'port = 8080',              # TOML
    'port: 8080',               # YAML
    'port: 8080\nenv: prod',   # YAML with multiple keys
]

for config in configs:
    try:
        parsed = serializer(config)
        print(f"✅ Parsed: {parsed}")
    except SerializerException as e:
        print(f"❌ Failed: {e}")
```

### 3. 自定义格式处理

```python
from use_nacos.serializer import (
    Serializer,
    SerializerException
)

class PropertiesSerializer(Serializer):
    """Java Properties 格式解析器"""

    def __call__(self, data) -> dict:
        result = {}
        for line in data.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                result[key.strip()] = value.strip()
            elif ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()

        return result

# 使用
serializer = PropertiesSerializer()
config = serializer("server.port=8080\nserver.host=localhost")
print(config)
# {"server.port": "8080", "server.host": "localhost"}
```

### 4. 格式验证

```python
from use_nacos.serializer import JsonSerializer
import json

serializer = JsonSerializer()

# 验证 JSON 格式
def validate_json(data_str):
    try:
        result = serializer(data_str)
        return True, result
    except SerializerException as e:
        return False, str(e)

# 使用
config_str = '{"port": 8080}'
is_valid, result = validate_json(config_str)
if is_valid:
    print(f"✅ Valid: {result}")
else:
    print(f"❌ Invalid: {result}")
```

---

## 性能对比

| 序列化器 | 速度 | 适用场景 | 优先级 |
|---------|------|---------|--------|
| Text | ⚡⚡⚡ 最快 | 纯文本 | 4 |
| JSON | ⚡⚡ 快 | 标准 API | 1 |
| TOML | ⚡ 中等 | Rust 配置 | 2 |
| YAML | ⚡ 中等 | 配置文件 | 3 |
| Auto | ⚡ 较慢（尝试多种） | 未知格式 | - |

---

## 最佳实践

### 1. 明确格式时使用特定序列化器

```python
# ✅ 好的做法
serializer = JsonSerializer()
data = serializer('{"port": 8080}')

# ❌ 不推荐（不必要的尝试）
serializer = AutoSerializer()
data = serializer('{"port": 8080}')
```

### 2. 格式不确定时使用 AutoSerializer

```python
# ✅ 好的做法
serializer = AutoSerializer()
data = serializer(config_from_nacos)  # 未知格式

# ❌ 不推荐（可能尝试多种格式）
serializer = JsonSerializer()
data = serializer(config_from_nacos)  # 可能不是 JSON
```

### 3. 异常处理

```python
from use_nacos.serializer import SerializerException

try:
    data = serializer(config_str)
except SerializerException as e:
    print(f"配置解析失败: {e}")
    # 使用默认配置或提示用户
    data = get_default_config()
```

### 4. 缓存解析结果

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def parse_config(config_str):
    """缓存配置解析结果"""
    return serializer(config_str)

# 使用
config1 = parse_config('{"port": 8080}')
config2 = parse_config('{"port": 8080}')  # 使用缓存
```

---

## 版本兼容性

### Python 3.11+

使用内置的 `tomllib`:

```python
import tomllib

# Python 3.11+ 不需要额外依赖
```

### Python < 3.11

使用 `tomli`:

```python
import tomli

# 需要安装: pip install tomli
```

### YAML 支持

需要安装 `PyYAML`:

```bash
pip install pyyaml
```

---

## 相关文档

- [配置管理 API](./config.md)
- [客户端 API](./client.md)
- [认证 API](./auth.md)
