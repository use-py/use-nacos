from typing import Awaitable, Union, TypeVar, TypedDict, Optional

import httpx

T = TypeVar("T")
SyncAsync = Union[T, Awaitable[T]]
HttpxClient = Union[httpx.Client, httpx.AsyncClient]


class BeatType(TypedDict):
    service_name: str
    ip: str
    port: int
    weight: int
    ephemeral: bool
    cluster: Optional[str]
    metadata: Optional[Union[dict, str]]
