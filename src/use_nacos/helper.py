"""Helper utilities for use-nacos."""

from typing import Union

import httpx


def is_async_client(client: Union[httpx.Client, httpx.AsyncClient]) -> bool:
    """Check if the client is an async client.

    Args:
        client: An httpx client instance (sync or async).

    Returns:
        True if the client is an AsyncClient, False otherwise.

    Example:
        >>> client = httpx.AsyncClient()
        >>> is_async_client(client)
        True
    """
    return isinstance(client, httpx.AsyncClient)
