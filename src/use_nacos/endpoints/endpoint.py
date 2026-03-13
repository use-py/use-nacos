from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import BaseClient


class Endpoint:
    def __init__(self, client: "BaseClient") -> None:
        self.client = client
