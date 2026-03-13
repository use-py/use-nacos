"""Base endpoint class for Nacos API."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import BaseClient


class Endpoint:
    """Base class for Nacos API endpoints.

    All endpoint classes (Config, Instance, Service, Namespace) inherit
    from this class to access the shared client.

    Attributes:
        client: The Nacos client instance.
    """

    def __init__(self, client: "BaseClient") -> None:
        """Initialize the endpoint with a Nacos client.

        Args:
            client: The Nacos client instance for making API requests.
        """
        self.client = client
