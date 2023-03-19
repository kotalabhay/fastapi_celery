from broadcaster import Broadcast
from fastapi import FastAPI

from project.config import settings

broadcast = Broadcast(settings.WS_MESSAGE_QUEUE)


def create_app() -> FastAPI:
    app = FastAPI()

    from project.logging import configure_logging
    configure_logging()

    # do this before loading routes
    from project.celery_utils import create_celery
    app.celery_app = create_celery()



    from project.loop import stores_router
    app.include_router(stores_router)



    @app.on_event("startup")
    async def startup_event():
        await broadcast.connect()

    @app.on_event("shutdown")
    async def shutdown_event():
        await broadcast.disconnect()

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    return app
