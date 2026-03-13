import os

import pytest

# 检查是否有可用的 Nacos 服务器
HAS_NACOS_SERVER = bool(
    os.environ.get("SERVER_ADDR") or os.environ.get("NACOS_SERVER_ADDR")
)


def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line("markers", "nacos: 标记需要真实 Nacos 服务器的测试")


def pytest_collection_modifyitems(config, items):
    """根据是否有 Nacos 服务器自动跳过测试"""
    if HAS_NACOS_SERVER:
        return

    skip_nacos = pytest.mark.skip(
        reason="需要 Nacos 服务器（设置 SERVER_ADDR 或 NACOS_SERVER_ADDR 环境变量）"
    )
    for item in items:
        if "nacos" in item.keywords or any(
            keyword in item.name for keyword in ["register", "beat", "publish"]
        ):
            item.add_marker(skip_nacos)
