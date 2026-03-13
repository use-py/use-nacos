# Chooser - 加权随机选择器

Chooser 是一个加权随机选择器，用于实现负载均衡和服务实例选择。

## 概述

Chooser 通过权重计算和累积权重算法，实现了加权随机选择功能，常用于：

- 🔀 **负载均衡** - 根据实例权重选择服务实例
- ⚖️ **A/B 测试** - 按比例分配流量
- 📊 **蓝绿部署** - 按比例切换流量

## 核心功能

1. **权重计算** - 计算每个选项的精确权重
2. **累积权重** - 构建累积权重数组
3. **随机选择** - 使用二分查找进行高效随机选择
4. **异常处理** - 处理无效权重（NaN, Infinity）

---

## Chooser 类

### 构造函数

```python
Chooser(host_with_weight: list)
```

**参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `host_with_weight` | list | 包含 (host, weight) 元组的列表 |

**示例:**

```python
from use_nacos._chooser import Chooser

# 创建选择器
chooser = Chooser([
    ("instance1", 1.0),  # 权重 1
    ("instance2", 2.0),  # 权重 2（概率是 instance1 的 2 倍）
    ("instance3", 7.0),  # 权重 7
])

# 总权重: 1 + 2 + 7 = 10
# instance1 概率: 1/10 = 10%
# instance2 概率: 2/10 = 20%
# instance3 概率: 7/10 = 70%
```

---

## 方法

### refresh

刷新权重计算，重新计算累积权重。

**签名:**

```python
def refresh(self)
```

**功能:**
- 过滤掉权重 ≤ 0 的项
- 处理无效权重（NaN, Infinity）
- 计算精确权重
- 构建累积权重数组
- 验证权重总和

**示例:**

```python
from use_nacos._chooser import Chooser

# 初始权重
hosts = [
    ("instance1", 1.0),
    ("instance2", 2.0),
    ("instance3", 3.0),
]

chooser = Chooser(hosts)
chooser.refresh()

print(f"有效项数: {len(chooser.items)}")
print(f"权重列表: {chooser.weights}")
```

**权重计算逻辑:**

```python
# 原始权重
weights = [1.0, 2.0, 3.0]
sum = 6.0

# 精确权重（归一化）
exact_weights = [
    1.0 / 6.0,  # 0.1667
    2.0 / 6.0,  # 0.3333
    3.0 / 6.0,  # 0.5000
]

# 累积权重
cumulative_weights = [
    0.1667,      # 0 ~ 0.1667
    0.1667 + 0.3333,  # 0.1667 ~ 0.5000
    0.1667 + 0.3333 + 0.5000,  # 0.5000 ~ 1.0
]
# 结果: [0.1667, 0.5000, 1.0]
```

**异常处理:**

```python
# 处理特殊权重
weights = [
    ("instance1", float("inf")),  # 无穷大 → 10000
    ("instance2", float("nan")),  # NaN → 1.0
    ("instance3", -1.0),        # 负数 → 忽略
    ("instance4", 0.0),         # 零 → 忽略
    ("instance5", 5.0),         # 正常 → 5.0
]

chooser = Chooser(weights)
chooser.refresh()

# 只保留有效项: instance5
# 特殊值会被转换或忽略
```

---

### random_with_weight

根据权重随机选择一个项。

**签名:**

```python
def random_with_weight(self) -> str
```

**返回:** 随机选择的项（host 字符串）

**工作原理:**

1. 生成 0-1 之间的随机数
2. 使用二分查找在累积权重数组中找到对应项
3. 返回该项

**示例:**

```python
from use_nacos._chooser import Chooser

hosts = [
    ("192.168.1.1", 1.0),
    ("192.168.1.2", 2.0),
    ("192.168.1.3", 7.0),
]

chooser = Chooser(hosts)
chooser.refresh()

# 多次随机选择
for _ in range(10):
    selected = chooser.random_with_weight()
    print(f"选中实例: {selected}")

# 预期输出（示例）:
# 选中实例: 192.168.1.3  # 70% 概率
# 选中实例: 192.168.1.3
# 选中实例: 192.168.1.2  # 20% 概率
# 选中实例: 192.168.1.3
# 选中实例: 192.168.1.1  # 10% 概率
# 选中实例: 192.168.1.3
# ...
```

**二分查找实现:**

```python
@staticmethod
def _find_index(weights, value):
    """二分查找累积权重数组"""
    low = 0
    high = len(weights) - 1
    
    while low <= high:
        mid = (low + high) // 2
        
        if weights[mid] < value:
            # value 在右半部分
            low = mid + 1
        elif weights[mid] > value:
            # value 在左半部分
            high = mid - 1
        else:
            # 精确匹配
            return mid
    
    return low  # 返回插入位置
```

---

## 完整示例

### 基础负载均衡

```python
from use_nacos._chooser import Chooser

# 配置服务实例及其权重
instances = [
    ("192.168.1.100", 1.0),  # 普通实例
    ("192.168.1.101", 1.0),  # 普通实例
    ("192.168.1.102", 3.0),  # 高性能实例（3 倍权重）
    ("192.168.1.103", 5.0),  # 超高性能实例（5 倍权重）
]

# 创建选择器
chooser = Chooser(instances)
chooser.refresh()

# 模拟请求分发
print("模拟 100 个请求的分布：")
distribution = {}

for _ in range(100):
    selected = chooser.random_with_weight()
    distribution[selected] = distribution.get(selected, 0) + 1

# 打印分布
for instance, count in sorted(distribution.items()):
    percentage = count / 100 * 100
    print(f"  {instance}: {count} 次 ({percentage:.1f}%)")

# 预期输出:
# 192.168.1.100: ~10 次 (10%)
# 192.168.1.101: ~10 次 (10%)
# 192.168.1.102: ~30 次 (30%)
# 192.168.1.103: ~50 次 (50%)
```

### A/B 测试

```python
from use_nacos._chooser import Chooser

# A/B 测试配置
versions = [
    ("version-a", 90),  # 90% 流量到版本 A
    ("version-b", 10),  # 10% 流量到版本 B
]

chooser = Chooser(versions)
chooser.refresh()

# 模拟用户访问
users = list(range(1000))  # 1000 个用户
assignment = {}

for user in users:
    version = chooser.random_with_weight()
    assignment[version] = assignment.get(version, 0) + 1

print("A/B 测试结果:")
print(f"  Version A: {assignment['version-a']} 用户 ({assignment['version-a'] / 1000 * 100:.1f}%)")
print(f"  Version B: {assignment['version-b']} 用户 ({assignment['version-b'] / 1000 * 100:.1f}%)")
```

### 动态权重更新

```python
from use_nacos._chooser import Chooser

# 初始权重
instances = [
    ("instance1", 1.0),
    ("instance2", 1.0),
    ("instance3", 1.0),
]

chooser = Chooser(instances)
chooser.refresh()

# 模拟监控和权重调整
def update_weights_based_on_performance(instance, performance_score):
    """根据性能分数调整权重"""
    base_weight = 1.0
    
    # 性能越好，权重越高
    new_weight = base_weight * performance_score
    
    # 更新权重（需要重新创建 Chooser）
    new_instances = [
        ("instance1", new_weight if inst == "instance1" else 1.0),
        ("instance2", new_weight if inst == "instance2" else 1.0),
        ("instance3", new_weight if inst == "instance3" else 1.0),
    ]
    
    return Chooser(new_instances)

# 模拟：instance3 性能很好（2.0 倍）
print("\n调整 instance3 的权重为 2.0")
chooser = update_weights_based_on_performance("instance3", 2.0)
chooser.refresh()

# 新的分布
for _ in range(10):
    print(f"  选中: {chooser.random_with_weight()}")

# 预期: instance3 被选中的概率增加到 50%
```

---

## 高级用法

### 带缓存的权重计算

```python
from use_nacos._chooser import Chooser
import time

class CachedChooser(Chooser):
    """带缓存的选择器，避免重复计算"""
    
    def __init__(self, hosts, ttl=60):
        super().__init__(hosts)
        self.ttl = ttl  # 缓存过期时间（秒）
        self.last_refresh = 0
        self._refresh_if_needed()
    
    def _refresh_if_needed(self):
        """如果缓存过期则刷新"""
        now = time.time()
        if now - self.last_refresh > self.ttl:
            self.refresh()
            self.last_refresh = now
    
    def random_with_weight(self):
        """选择前检查缓存"""
        self._refresh_if_needed()
        return super().random_with_weight()

# 使用
chooser = CachedChooser([
    ("instance1", 1.0),
    ("instance2", 2.0),
], ttl=60)  # 权重缓存 60 秒

for _ in range(10):
    selected = chooser.random_with_weight()
    print(f"选中: {selected}")
```

### 权重平滑调整

```python
from use_nacos._chooser import Chooser

class SmoothWeightedChooser:
    """权重平滑调整的选择器"""
    
    def __init__(self, hosts, smoothing_factor=0.1):
        self.hosts = hosts
        self.target_weights = {h: w for h, w in hosts}
        self.current_weights = {h: w for h, w in hosts}
        self.smoothing_factor = smoothing_factor
        self.refresh()
    
    def refresh(self):
        """使用当前权重创建 Chooser"""
        hosts_with_weight = [
            (h, self.current_weights[h])
            for h in self.hosts
        ]
        self.chooser = Chooser(hosts_with_weight)
        self.chooser.refresh()
    
    def update_weight(self, host, new_weight):
        """平滑更新权重"""
        old_weight = self.current_weights[host]
        
        # 平滑调整：new = old + α * (target - old)
        smoothed_weight = (
            old_weight + 
            self.smoothing_factor * (new_weight - old_weight)
        )
        
        self.current_weights[host] = smoothed_weight
        self.refresh()
    
    def random_with_weight(self):
        """选择实例"""
        return self.chooser.random_with_weight()

# 使用
chooser = SmoothWeightedChooser([
    ("instance1", 1.0),
    ("instance2", 1.0),
    ("instance3", 1.0),
], smoothing_factor=0.1)

# 平滑调整权重
print("平滑调整 instance3 的权重...")
for i in range(10):
    chooser.update_weight("instance3", 5.0)
    current = chooser.current_weights["instance3"]
    print(f"  步骤 {i + 1}: 权重 = {current:.2f}")

# 最终权重会逐步从 1.0 增加到 5.0
```

---

## 性能考虑

### 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| `refresh()` | O(n) | n 是有效项数 |
| `random_with_weight()` | O(log n) | 二分查找 |

### 空间复杂度

| 数据结构 | 复杂度 | 说明 |
|---------|--------|------|
| `items` | O(n) | 存储有效项 |
| `weights` | O(n) | 存储累积权重 |

### 性能优化建议

1. **缓存权重计算** - 如果权重不变，可以只计算一次
2. **避免频繁 refresh** - 只在权重变化时调用
3. **使用浮点数** - 权重使用 float 类型提高精度

---

## 最佳实践

### 1. 权重设置

```python
# ✅ 好的权重设置
instances = [
    ("instance1", 1.0),  # 基准
    ("instance2", 2.0),  # 2 倍权重
    ("instance3", 3.0),  # 3 倍权重
]

# ❌ 不好的权重设置
instances = [
    ("instance1", 0.0001),  # 权重太小
    ("instance2", 999999),  # 权重太大
    ("instance3", -1),      # 负权重
]
```

### 2. 权重范围

```python
# 推荐的权重范围: 0.1 - 10.0
MIN_WEIGHT = 0.1
MAX_WEIGHT = 10.0

# 限制权重范围
def clamp_weight(weight):
    return max(MIN_WEIGHT, min(MAX_WEIGHT, weight))

# 使用
weight = clamp_weight(user_input_weight)
```

### 3. 处理空列表

```python
from use_nacos._chooser import Chooser

# 所有权重都 ≤ 0 的情况
chooser = Chooser([
    ("instance1", -1),
    ("instance2", 0),
])

chooser.refresh()
# items 和 weights 都为空

try:
    selected = chooser.random_with_weight()
except Exception as e:
    print(f"没有有效实例: {e}")
```

### 4. 监控选择分布

```python
from use_nacos._chooser import Chooser
from collections import Counter

class MonitoredChooser(Chooser):
    """带监控的选择器"""
    
    def __init__(self, hosts):
        super().__init__(hosts)
        self.selections = Counter()
        self.refresh()
    
    def random_with_weight(self):
        selected = super().random_with_weight()
        self.selections[selected] += 1
        return selected
    
    def get_distribution(self):
        """获取选择分布"""
        total = sum(self.selections.values())
        return {
            item: count / total
            for item, count in self.selections.items()
        }

# 使用
chooser = MonitoredChooser([
    ("instance1", 1),
    ("instance2", 2),
    ("instance3", 7),
])

# 模拟 1000 次选择
for _ in range(1000):
    chooser.random_with_weight()

# 查看分布
dist = chooser.get_distribution()
print("选择分布:")
for item, ratio in dist.items():
    print(f"  {item}: {ratio * 100:.1f}%")
```

---

## 相关文档

- [实例管理 API](./instance.md)
- [服务发现 API](./discovery.md)
- [缓存 API](./cache.md)
