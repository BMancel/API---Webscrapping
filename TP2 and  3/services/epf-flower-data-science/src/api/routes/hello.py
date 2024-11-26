from fastapi import APIRouter
from src.schemas.message import MessageResponse
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter()


@router.get("/hello/{name}", name="Demo route", response_model=MessageResponse)
def hello(name: str) -> MessageResponse:
    return MessageResponse(message=f"Hello {name}, from fastapi test route ! BANG !")