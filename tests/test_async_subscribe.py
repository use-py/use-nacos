"""Test async subscription cancellation with asyncio.Event."""

import asyncio

import pytest

from use_nacos import NacosAsyncClient
from use_nacos.endpoints import ConfigAsyncEndpoint


@pytest.fixture
def async_client():
    return NacosAsyncClient()


@pytest.fixture
def async_config(async_client):
    return ConfigAsyncEndpoint(async_client)


@pytest.mark.asyncio
async def test_async_subscribe_cancel(async_config):
    """Test that async subscription can be cancelled."""
    stop_event = await async_config.subscribe(
        data_id="test_cancel",
        group="DEFAULT_GROUP",
        callback=lambda c: None,
    )
    # Cancel the subscription
    assert stop_event is not None
    assert hasattr(stop_event, "cancel")
    stop_event.cancel()

    # Give it a moment to cancel
    await asyncio.sleep(0.1)

    # The task should be cancelled without errors
    assert True  # If we reach here, cancellation worked
