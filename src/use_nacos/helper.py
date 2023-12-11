from typing import Union

import httpx


def is_async_client(client: Union[httpx.Client, httpx.AsyncClient]):
    """ Check if the client is async client """
    return isinstance(client, httpx.AsyncClient)
