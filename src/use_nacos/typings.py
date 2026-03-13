"""Type definitions for use-nacos."""

from typing import Awaitable, Optional, TypedDict, TypeVar, Union

import httpx

T = TypeVar("T")

#: Union type for sync/async return values
SyncAsync = Union[T, Awaitable[T]]

#: Union type for httpx sync/async clients
HttpxClient = Union[httpx.Client, httpx.AsyncClient]


class BeatType(TypedDict):
    """Nacos heartbeat beat info.

    Attributes:
        service_name: Service name.
        ip: Instance IP address.
        port: Instance port.
        weight: Instance weight for load balancing.
        ephemeral: Whether the instance is ephemeral.
        cluster: Cluster name.
        metadata: Instance metadata.
    """

    service_name: str
    ip: str
    port: int
    weight: int
    ephemeral: bool
    cluster: Optional[str]
    metadata: Optional[Union[dict, str]]
