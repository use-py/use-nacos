import json
import random
import time

import httpx
import pytest

from use_nacos.cache import MemoryCache
from use_nacos.client import NacosClient, NacosAsyncClient
from use_nacos.endpoints import ConfigEndpoint, ConfigAsyncEndpoint, config as conf
from use_nacos.exception import HTTPResponseError
from use_nacos.serializer import JsonSerializer, AutoSerializer, YamlSerializer, TomlSerializer


@pytest.fixture
def client():
    return NacosClient()


@pytest.fixture
def async_client():
    return NacosAsyncClient()


@pytest.fixture
def config(client):
    yield ConfigEndpoint(client)


@pytest.fixture
def async_config(async_client):
    yield ConfigAsyncEndpoint(async_client)


def test_config_get_not_found(config):
    with pytest.raises(HTTPResponseError):
        config.get('not_found', 'not_found')


def test_config_get_not_found_default_value(config, mocker):
    mocker.patch.object(ConfigEndpoint, '_get', side_effect=HTTPResponseError(response=httpx.Response(404)))
    assert config.get('test_config_miss', 'DEFAULT_GROUP', default="default_value") == "default_value"


@pytest.mark.parametrize('data_id, group', [
    ('test_config', 'DEFAULT_GROUP'),
])
@pytest.mark.parametrize('content ,tenant, type, serialized, expected', [
    ('test_config', '', None, None, 'test_config'),
    (json.dumps({"a": "b"}), '', 'json', True, {"a": "b"}),
    ('<p>hello nacos</p>', '', 'html', False, '<p>hello nacos</p>'),
    (1234, '', None, True, 1234),
])
def test_config_publish_get(config, data_id, group, content, tenant, type, serialized, expected):
    assert config.publish(data_id, group, content, tenant, type)
    assert config.get(
        data_id,
        group,
        tenant,
        serializer=serialized
    ) == expected


@pytest.mark.parametrize('data_id, group', [
    ('test_config_delete', 'DEFAULT_GROUP'),
])
def test_config_delete(config, data_id, group):
    config.publish(data_id, group, "123")
    assert config.delete(data_id, group)
    time.sleep(.1)
    with pytest.raises(HTTPResponseError):
        config.get(data_id, group)


def test_config_subscriber(config):
    dataId = f"test_config_{random.randint(0, 1000)}"
    assert config.publish(data_id=dataId, group="DEFAULT_GROUP", content="123")

    def _callback(new_config):
        assert new_config == "456"
        config_subscriber.cancel()

    config_subscriber = config.subscribe(
        data_id=dataId,
        group="DEFAULT_GROUP",
        callback=_callback
    )
    # update config
    config.publish(data_id=dataId, group="DEFAULT_GROUP", content="456")


# ===================== async config tests =====================
@pytest.mark.asyncio
async def test_async_config_get_not_found(async_config):
    with pytest.raises(HTTPResponseError):
        await async_config.get('not_found', 'not_found')


@pytest.mark.parametrize('data_id, group', [
    ('test_config', 'DEFAULT_GROUP'),
])
@pytest.mark.parametrize('content ,tenant, type, serializer, expected', [
    ('test_config', '', None, False, 'test_config'),
    (json.dumps({"a": "b"}), '', 'json', JsonSerializer(), {"a": "b"}),
    ('<p>hello nacos</p>', '', 'html', False, '<p>hello nacos</p>'),
    (1234, '', None, True, 1234),
])
@pytest.mark.asyncio
async def test_async_config_publish_get(async_config, data_id, group, content, tenant, type, serializer, expected):
    assert await async_config.publish(data_id, group, content, tenant, type)
    assert await async_config.get(
        data_id,
        group,
        tenant,
        serializer=serializer
    ) == expected


@pytest.mark.parametrize('data_id, group', [
    ('test_config_delete_async', 'DEFAULT_GROUP'),
])
@pytest.mark.asyncio
async def test_async_config_delete(async_config, data_id, group):
    assert await async_config.publish(data_id, group, "123")
    assert await async_config.delete(data_id, group)
    time.sleep(.1)
    with pytest.raises(HTTPResponseError):
        await async_config.get(data_id, group)


@pytest.mark.parametrize("data_id, group, tenant, expected", [
    ("test_config", "DEFAULT_GROUP", "", "test_config#DEFAULT_GROUP#"),
    ("test_config", "DEFAULT_GROUP", "test_tenant", "test_config#DEFAULT_GROUP#test_tenant"),
])
def test__get_config_key(config, data_id, group, tenant, expected):
    assert conf._get_config_key(data_id, group, tenant) == expected


@pytest.mark.parametrize("content, expected", [
    ("1234", "81dc9bdb52d04dc20036dbd8313ed055"),
    ({"a": 1}, "5268827fe25d043c696340679639cf67")
])
def test__get_md5(content, expected):
    assert conf._get_md5(content) == expected


def test_mock_exception(config, mocker):
    mocker.patch.object(ConfigEndpoint, '_get', side_effect=HTTPResponseError(response=httpx.Response(500)))
    with pytest.raises(HTTPResponseError):
        config.get('test_config', 'DEFAULT_GROUP')


def test_mock_network_error_exception(config, mocker):
    mocker.patch.object(ConfigEndpoint, '_get', side_effect=httpx.TimeoutException(""))
    assert config.get('test_config_1', 'DEFAULT_GROUP') is None
    mocker.patch.object(ConfigEndpoint, '_get', side_effect=httpx.ConnectError(""))
    assert config.get('test_config_1', 'DEFAULT_GROUP') is None


def test_config_from_cache(config, mocker):
    mc = MemoryCache()
    mc.set("test_config_cache#DEFAULT_GROUP#", "abc")
    # mock timeout
    mocker.patch.object(ConfigEndpoint, '_get', side_effect=httpx.TimeoutException(""))
    assert config.get('test_config_cache', 'DEFAULT_GROUP', cache=mc) == "abc"


@pytest.mark.parametrize("conf_str, serializer, expected", [
    ("123", AutoSerializer(), 123),
    ('{"a": 2}', JsonSerializer(), {"a": 2}),
    ('a: 1\nfoo:\n  b: 2', YamlSerializer(), {'a': 1, 'foo': {'b': 2}}),
    ('a = 1\n[foo]\nb = 2', TomlSerializer(), {'a': 1, 'foo': {'b': 2}}),
])
def test_config_serializer(conf_str, serializer, expected):
    assert conf._serialize_config(conf_str, serializer) == expected
