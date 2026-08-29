# Changelog

use-nacos 的面向用户变更记录。源码细节请参考 [GitHub Releases](https://github.com/use-py/use-nacos/releases)。

## Unreleased — 与 main 同步的文档更新（PR #5 + PR #7 闭环）

### 新增
- `NacosClient` / `NacosAsyncClient` 支持 `with` / `async with` 上下文管理器：进入返回 self，离开自动关闭底层 httpx 客户端。
- 显式关闭方法：`NacosClient.close()` / `NacosAsyncClient.close()`（异步版为 `aclose()`）。
- 文档新增 [CHANGELOG.md](./CHANGELOG.md)。

### 行为变更
- `NacosAPIAuth` 凭据注入收紧：仅当 `username` 与 `password` **同时** 存在时才会把 `username` / `password` 加入 URL query；之前会无条件注入 `username=` / `password=` 空串，可能在反向代理/访问日志中泄露空凭据。
- `config.subscribe()` 默认缓存改为全局 `memory_cache`，与 `config.get()` 共享同一实例（之前会创建一个新的 `MemoryCache`，导致两边缓存互不可见）。
- `config.subscribe()` 的 `timeout` 参数语义保持为 **毫秒**（默认 `30_000` ms）；修复了先前把 30000ms 当作 30000 秒传给 httpx 的 bug（实际等于 8.3 小时长连接）。
- httpx 0.28 兼容性：per-request `timeout` 现在通过 `client.build_request(...)` 传递，`send()` 不再接受 `timeout` 参数。
- `BeatType.weight` 类型由 `int` 改为 `float`，支持小数权重（如 `weight=1.5`），与 Nacos 服务端约定一致。
- `_chooser.Chooser.refresh()` 使用 `math.isnan` / `math.isinf` 判定 NaN/inf（修复 `float("nan") == weight` 永远为 `False` 导致 NaN 项被错误剔除的 bug）；inf 归一化为 `10000.0`，NaN 归一化为 `1.0`。
- 移除 `ConfigOperationMixin.__getattr__`（原实现返回 `partial(self.request, service_name=attr)`，访问任何属性都会抛 `TypeError`，且会遮蔽真实属性）。

### 修复
- 单元测试中存在的若干 unused import / 未使用局部变量 / 行尾换行 / 超长行（lint 通过）。
- CI：`.github/workflows/test.yml` 不再向 `pytest` 注入 `NACOS_*` secret（之前会让 `HAS_NACOS_SERVER=True`，在没有 Nacos 服务的 CI 环境里集成测试会去连不可达地址，挂死 1 小时）；同时 `test` job 新增 `timeout-minutes: 15` 兜底。

### 文档
- `docs/api/client.md`：新增「上下文管理器」与「认证行为」小节。
- `docs/api/config.md`：新增「长轮询订阅」小节，说明 `timeout` 单位为毫秒、`cache` 默认共享全局缓存、停止订阅的方式。
- `docs/api/cache.md`：说明 `get()` 与 `subscribe()` 共享全局 `memory_cache`。
- `README.md`：新增 `context manager (auto close)` 用法示例。
- `CHANGELOG.md`（本文件）：汇总上述用户可见变更。

### 升级注意
- 升级前若依赖 `subscribe` 内置的新 `MemoryCache()`，请显式传入 `cache=MemoryCache()` 以保持隔离。
- `weight` 字段类型从 `int` 变为 `float`，如代码中做了严格 isinstance 校验需更新。
- 凭据注入仅在 `username` 和 `password` 同时存在时发生：若曾依赖空 `username` 参数访问匿名接口，请确认服务端是否需要该行为。
