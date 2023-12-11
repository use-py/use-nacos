from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from use_nacos import NacosAsyncClient


def config_update(config):
    print(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    nacos = NacosAsyncClient()

    config_subscriber = await nacos.config.subscribe(
        data_id="test-config",
        group="DEFAULT_GROUP",
        callback=config_update,
    )
    await nacos.instance.register(
        service_name=f"python-api-1",
        ip="10.10.10.1",
        port=8000,
        weight=1
    )
    yield
    config_subscriber.cancel()


app = FastAPI(lifespan=lifespan)

if __name__ == '__main__':
    uvicorn.run("in_fastapi:app", host="0.0.0.0", port=1081)
