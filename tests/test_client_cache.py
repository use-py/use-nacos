"""Test instance client caching."""

from unittest.mock import MagicMock, patch

import pytest

from use_nacos import NacosAsyncClient, NacosClient
from use_nacos.endpoints import InstanceAsyncEndpoint, InstanceEndpoint


@pytest.fixture
def client():
    return NacosClient()


@pytest.fixture
def async_client():
    return NacosAsyncClient()


@pytest.fixture
def instance(client):
    return InstanceEndpoint(client)


@pytest.fixture
def async_instance(async_client):
    return InstanceAsyncEndpoint(async_client)


def test_client_caching(instance):
    """Test that httpx.Client instances are cached."""
    # Create a mock client that tracks creation
    client_creation_count = 0
    original_client_init = None
    created_clients = []

    def mock_client_init(*args, **kwargs):
        nonlocal client_creation_count
        client_creation_count += 1
        mock_client = MagicMock()
        mock_client.request = MagicMock(return_value="response")
        return mock_client

    # Patch httpx.Client to track creations
    with patch("use_nacos.endpoints.instance.httpx.Client") as mock_client_class:
        mock_client_class.side_effect = mock_client_init

        # First request should create a client
        instance.request("GET", "/test", instance={"ip": "127.0.0.1", "port": 8000})
        assert client_creation_count == 1

        # Second request to same instance should reuse client
        instance.request("GET", "/test2", instance={"ip": "127.0.0.1", "port": 8000})
        assert client_creation_count == 1

        # Request to different instance should create new client
        instance.request("GET", "/test3", instance={"ip": "127.0.0.1", "port": 8001})
        assert client_creation_count == 2


@pytest.mark.asyncio
async def test_async_client_caching(async_instance):
    """Test that httpx.AsyncClient instances are cached."""
    client_creation_count = 0
    created_clients = {}

    def mock_client_class(*args, **kwargs):
        nonlocal client_creation_count
        client_creation_count += 1
        mock_client = MagicMock()

        async def mock_request(*args_inner, **kwargs_inner):
            return "response"

        mock_client.request = mock_request
        return mock_client

    # Patch httpx.AsyncClient to track creations
    with patch(
        "use_nacos.endpoints.instance.httpx.AsyncClient", side_effect=mock_client_class
    ):
        # First request should create a client
        await async_instance.request(
            "GET",
            "/test",
            instance={"ip": "127.0.0.1", "port": 8000},
        )
        assert client_creation_count == 1

        # Second request to same instance should reuse client
        await async_instance.request(
            "GET",
            "/test2",
            instance={"ip": "127.0.0.1", "port": 8000},
        )
        assert client_creation_count == 1

        # Request to different instance should create new client
        await async_instance.request(
            "GET",
            "/test3",
            instance={"ip": "127.0.0.1", "port": 8001},
        )
        assert client_creation_count == 2
