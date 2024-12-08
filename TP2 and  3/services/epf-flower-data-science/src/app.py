from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.api.router import router
from src.api.routes.authentication import UserCreate, HTTPValidationError

def get_application() -> FastAPI:
    application = FastAPI(
        title="EPF Flower Data Science API",
        description="API for EPF Flower Data Science project",
        version="1.0.0",
    )
    
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def custom_openapi():
        if application.openapi_schema:
            return application.openapi_schema

        openapi_schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
        )

        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
            
        openapi_schema["components"]["securitySchemes"] = {
            "Bearer": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Enter the token with the `Bearer: ` prefix, e.g. `Bearer abcde12345`"
            }
        }

        openapi_schema["security"] = [{"Bearer": []}]

        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}

        openapi_schema["components"]["schemas"]["HTTPValidationError"] = {
            "title": "HTTPValidationError",
            "type": "object",
            "properties": {
                "detail": {
                    "title": "Detail",
                    "type": "string"
                }
            }
        }

        application.openapi_schema = openapi_schema
        return application.openapi_schema

    application.openapi = custom_openapi
    application.include_router(router)
    
    return application
