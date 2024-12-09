# API 参考

本节提供 use-nacos 的详细 API 文档。

## NacosClient

`NacosClient` 是与 Nacos 服务器交互的主要类。

### 初始化参数

```python
class NacosClient:
    def __init__(
        self,
        server_addresses: str | list[str],
        namespace: str = "public",
        username: str | None = None,
        password: str | None = None,
        timeout: int = 3,
        tls_enabled: bool = False,
        ca_file: str | None = None,
        cert_file: str | None = None,
        key_file: str | None = None,
    ):
        """
        初始化 Nacos 客户端

        参数:
            server_addresses: Nacos 服务器地址，可以是单个地址或地址列表
            namespace: 命名空间 ID
            username: 认证用户名
            password: 认证密码
            timeout: 请求超时时间（秒）
            tls_enabled: 是否启用 TLS
            ca_file: CA 证书文件路径
            cert_file: 客户端证书文件路径
            key_file: 客户端私钥文件路径
        """
```

### 主要方法

#### 配置管理

```python
async def get_config(
    self,
    data_id: str,
    group: str = "DEFAULT_GROUP"
) -> str:
    """
    获取配置内容

    参数:
        data_id: 配置 ID
        group: 配置分组
    
    返回:
        配置内容字符串
    """

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

#### 服务发现

```python
async def register_instance(
    self,
    service_name: str,
    ip: str,
    port: int,
    metadata: dict | None = None
) -> bool:
    """
    注册服务实例

    参数:
        service_name: 服务名称
        ip: 实例 IP
        port: 实例端口
        metadata: 实例元数据
    
    返回:
        是否注册成功
    """

async def get_instances(
    self,
    service_name: str,
    healthy_only: bool = True
) -> list[dict]:
    """
    获取服务实例列表

    参数:
        service_name: 服务名称
        healthy_only: 是否只返回健康实例
    
    返回:
        实例列表
    """
```

## 异常类

```python
class NacosException(Exception):
    """Nacos 相关异常的基类"""

class NacosConnectionError(NacosException):
    """连接 Nacos 服务器失败"""

class NacosAuthException(NacosException):
    """认证失败"""

class NacosRequestException(NacosException):
    """请求处理失败"""
```

更多详细 API 信息，请参考各个具体功能的文档页面：

- [NacosClient 详细文档](./client)
- [配置管理 API](./config)
- [服务发现 API](./discovery)