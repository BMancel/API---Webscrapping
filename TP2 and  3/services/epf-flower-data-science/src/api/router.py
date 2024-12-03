"""API Router for Fast API."""
from fastapi import APIRouter

from src.api.routes import hello
from src.api.routes import docs
from src.api.routes import data
from src.api.routes import iris_model

router = APIRouter()

router.include_router(hello.router, tags=["Hello"])
router.include_router(docs.router, tags=["docs"])
router.include_router(data.router, tags=["data-iris"])
router.include_router(iris_model.router, tags=["model"])