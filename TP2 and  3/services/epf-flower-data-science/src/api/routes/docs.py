from fastapi import APIRouter
from src.schemas.message import MessageResponse
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter()

# Redirect the root endpoint to the Swagger documentation
@router.get("/", include_in_schema=False)
def redirect_to_swagger(request: Request):
    return RedirectResponse(url="/docs")