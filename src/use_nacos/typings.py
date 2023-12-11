from typing import Awaitable, Union, TypeVar, TypedDict, Optional

T = TypeVar("T")
SyncAsync = Union[T, Awaitable[T]]


class BeatType(TypedDict):
    service_name: str
    ip: str
    port: int
    weight: int
    ephemeral: bool
    cluster: Optional[str]
    metadata: Optional[Union[dict, str]]
