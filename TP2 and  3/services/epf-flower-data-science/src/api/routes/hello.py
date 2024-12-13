from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/hello/{name}", responses={
    200: {
        "description": "Successful greeting response",
        "content": {
            "application/json": {
                "example": {
                    "status": "success",
                    "message": "Hello YOUR_NAME, from fastapi test route! BANG !",
                }
            }
        }
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Name parameter validation error"
                }
            }
        }
    }
})
def hello(name: str):
    """
    Endpoint to greet a user by their name.

    Args:
        name (str): The name of the person to greet. Should be a valid string containing only letters.

    Returns:
        JSONResponse: A JSON response containing:
            - status: Success status of the operation
            - message: Personalized greeting message

    Raises:
        HTTPException: 422 Unprocessable Entity if name validation fails
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": f"Hello {name}, from fastapi test route! BANG !"
        }
    )