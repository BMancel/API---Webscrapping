from fastapi import APIRouter, HTTPException, Header, Depends, Security, status
from fastapi.security import APIKeyHeader
from firebase_admin import auth, initialize_app, credentials, get_app
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os

api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

class HTTPValidationError(BaseModel):
    detail: str

class UserCreate(BaseModel):
    email: str
    password: str

class AdminRequest(BaseModel):
    uid: str

class UserResponse(BaseModel):
    message: str
    uid: str
    is_admin: bool = False

class TokenResponse(BaseModel):
    token: str
    uid: str

class MessageResponse(BaseModel):
    message: str

class UserList(BaseModel):
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
    try:
        auth.set_custom_user_claims(request.uid, {'admin': True})
        return MessageResponse(message=f'User {request.uid} is now an admin')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
