"""API Router for Fast API."""
from fastapi import APIRouter

from src.api.routes import hello
from src.api.routes import docs
from src.api.routes import data
from src.api.routes import iris_model
from src.api.routes import parameters
from src.api.routes.authentication import public_router, private_router

router = APIRouter()

router.include_router(hello.router, tags=["Hello"])
router.include_router(docs.router, tags=["docs"])
router.include_router(data.router, tags=["data-iris"])
router.include_router(iris_model.router, tags=["model"])
router.include_router(parameters.router, tags=["firestore-parameters"])

router.include_router(public_router, prefix="/api", tags=["Public Authentication"])
router.include_router(private_router, prefix="/api", tags=["Private Authentication"])