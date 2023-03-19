from fastapi import APIRouter

stores_router = APIRouter(
    prefix="/stores",
)

from . import views, models, tasks

