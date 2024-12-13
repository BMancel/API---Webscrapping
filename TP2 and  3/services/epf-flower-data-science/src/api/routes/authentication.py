from fastapi import APIRouter, HTTPException, Header, Depends, Security, status
from fastapi.security import APIKeyHeader
from firebase_admin import auth, initialize_app, credentials, get_app
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os

api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

class HTTPValidationError(BaseModel):
    """
    Represents the structure of validation error responses.

    Attributes:
        detail (str): A message detailing the validation error.
    """
    detail: str

class UserCreate(BaseModel):
    """
    Schema for creating a user with email and password.

    Attributes:
        email (str): The user's email address.
        password (str): The user's password.
    """
    email: str
    password: str

class AdminRequest(BaseModel):
    """
    Schema for making a user an admin.

    Attributes:
        uid (str): The unique identifier of the user to promote to admin.
    """
    uid: str

class UserResponse(BaseModel):
    """
    Response model for user registration with user details.

    Attributes:
        message (str): A message describing the result of the registration.
        uid (str): The unique identifier of the created user.
        is_admin (bool): Whether the user has admin privileges.
    """
    message: str
    uid: str
    is_admin: bool = False

class TokenResponse(BaseModel):
    """
    Response model for login containing the authentication token.

    Attributes:
        token (str): The authentication token.
        uid (str): The unique identifier of the logged-in user.
    """
    token: str
    uid: str

class MessageResponse(BaseModel):
    """
    Generic message response model.

    Attributes:
        message (str): A descriptive message.
    """
    message: str

class UserList(BaseModel):
    """
    Response model containing a list of user details.

    Attributes:
        users (List[dict]): A list of user information including UID, email, and admin status.
    """
    users: list[dict]

# Initialize Firebase Admin SDK
try:
    firebase_app = get_app()
except ValueError:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, "../../../../../private_key.json")
    cred = credentials.Certificate(key_path)
    firebase_app = initialize_app(cred)

# Middleware for admin access
async def admin_required(authorization: str = Security(api_key_header)) -> auth.UserRecord:
    """
    Middleware for verifying admin privileges in requests.

    Args:
        authorization (str): The authorization header containing the Bearer token.

    Returns:
        auth.UserRecord: The user record of the authenticated admin.

    Raises:
        HTTPException: If the user is unauthorized or lacks admin privileges.
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header. Use format: Bearer <token>"
        )

    try:
        token = authorization.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(token)
        user = auth.get_user(decoded_token['uid'])

        if not user.custom_claims or not user.custom_claims.get('admin'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )

        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

public_router = APIRouter(
    prefix="/auth",
    responses={
        400: {"model": HTTPValidationError},
        401: {"model": HTTPValidationError},
        403: {"model": HTTPValidationError}
    }
)

@public_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register a new user.

    If this is the first user, admin privileges are assigned.

    Args:
        user (UserCreate): The user creation request.

    Returns:
        UserResponse: Details of the created user.
    """
    try:
        firebase_user = auth.create_user(
            email=user.email,
            password=user.password
        )

        try:
            page = auth.list_users()
            user_count = 0
            for _ in page.users:
                user_count += 1
                if user_count > 1:
                    break

            if user_count <= 1:
                auth.set_custom_user_claims(firebase_user.uid, {'admin': True})
                return UserResponse(
                    message='First user created successfully as admin',
                    uid=firebase_user.uid,
                    is_admin=True
                )
            else:
                auth.set_custom_user_claims(firebase_user.uid, {'admin': False})
                return UserResponse(
                    message='User created successfully',
                    uid=firebase_user.uid,
                    is_admin=False
                )
        except Exception:
            auth.set_custom_user_claims(firebase_user.uid, {'admin': False})
            return UserResponse(
                message='User created successfully',
                uid=firebase_user.uid,
                is_admin=False
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@public_router.post("/login", response_model=TokenResponse)
async def login(user: UserCreate):
    """
    Log in a user and generate an authentication token.

    Args:
        user (UserCreate): The login request containing email and password.

    Returns:
        TokenResponse: The authentication token and user UID.
    """
    try:
        firebase_user = auth.get_user_by_email(user.email)
        custom_token = auth.create_custom_token(firebase_user.uid)
        return TokenResponse(
            token=custom_token.decode(),
            uid=firebase_user.uid
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

private_router = APIRouter(
    prefix="/auth",
    dependencies=[Depends(api_key_header)],
    responses={
        400: {"model": HTTPValidationError},
        401: {"model": HTTPValidationError},
        403: {"model": HTTPValidationError}
    }
)

@private_router.get(
    "/users",
    response_model=UserList,
    responses={
        401: {"model": HTTPValidationError, "description": "Unauthorized"},
        403: {"model": HTTPValidationError, "description": "Forbidden - Admin only"}
    },
    summary="List all users",
    description="Requires admin privileges. Token must be provided in Authorization header."
)
async def list_users(current_user: auth.UserRecord = Depends(admin_required)):
    """
    List all registered users.

    Admin privileges are required to access this endpoint.

    Args:
        current_user (auth.UserRecord): The authenticated admin user.

    Returns:
        UserList: A list of all registered users.
    """
    try:
        page = auth.list_users()
        users = []
        for user in page.users:
            users.append({
                'uid': user.uid,
                'email': user.email,
                'disabled': user.disabled,
                'admin': user.custom_claims.get('admin', False) if user.custom_claims else False
            })
        return UserList(users=users)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@private_router.post(
    "/make-admin",
    response_model=MessageResponse,
    responses={
        401: {"model": HTTPValidationError, "description": "Unauthorized"},
        403: {"model": HTTPValidationError, "description": "Forbidden - Admin only"}
    },
    summary="Make a user admin",
    description="Requires admin privileges. Token must be provided in Authorization header."
)
async def make_admin(request: AdminRequest, current_user: auth.UserRecord = Depends(admin_required)):
    """
    Assign admin privileges to a user.

    Admin privileges are required to access this endpoint.

    Args:
        request (AdminRequest): The request containing the UID of the user to promote.
        current_user (auth.UserRecord): The authenticated admin user.

    Returns:
        MessageResponse: A message indicating the success of the operation.
    """
    try:
        auth.set_custom_user_claims(request.uid, {'admin': True})
        return MessageResponse(message=f'User {request.uid} is now an admin')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
