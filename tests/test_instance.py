import os
import time

import pytest

from use_nacos.client import NacosClient
from use_nacos.endpoints import InstanceEndpoint
from use_nacos.exception import HTTPResponseError

server_addr = os.environ.get('SERVER_ADDR')


@pytest.fixture
def client():
    return NacosClient(server_addr=server_addr, username="nacos", password="nacos")


@pytest.fixture
def instance(client):
    return InstanceEndpoint(client)


def test_instance_get_not_found(instance):
    with pytest.raises(HTTPResponseError):
        instance.get('not_found', 'not_found', 8000)


def test_instance_register(instance):
    assert instance.register('test', '127.0.0.1', 8000) == 'ok'


def test_instance_get(instance):
    _instance = instance.get('test', '127.0.0.1', 8000)
    assert _instance['metadata'] == {}
    assert _instance['ip'] == '127.0.0.1'


def test_instance_update(instance):
    mock_service = {
        'service_name': 'test',
        'ip': '127.0.0.1',
        'port': 8000,
    }
    assert instance.register(**mock_service) == 'ok'
    assert instance.update(weight=2.0, **mock_service) == 'ok'
    time.sleep(.5)
    _instance = instance.get(**mock_service)
    assert _instance['weight'] == 2.0
    assert _instance['healthy'] is True
