from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.schemas import UserRegister, UserLogin, TokenResponse, UserResponse, FirebaseSyncRequest
from app.auth.service import authenticate_user, create_user, get_user_by_email, get_or_create_firebase_user
from app.auth.security import create_access_token
from app.auth.firebase import verify_firebase_id_token
from app.dependencies import get_current_user
from app.models.entities import User
from app.audit import record_audit_log

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    user = await create_user(db, user_in)
    await record_audit_log(
        db=db,
        action="USER_REGISTERED",
        user=user,
        target_type="USER",
        target_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Support OAuth2 form (username field holds email)
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role.value, "dept": user.department.value})
    await record_audit_log(
        db=db,
        action="USER_LOGIN",
        user=user,
        target_type="USER",
        target_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        department=user.department
    )

@router.post("/login/json", response_model=TokenResponse)
async def login_json(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role.value, "dept": user.department.value})
    await record_audit_log(
        db=db,
        action="USER_LOGIN",
        user=user,
        target_type="USER",
        target_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        department=user.department
    )

@router.post("/firebase-sync", response_model=TokenResponse)
async def firebase_sync(
    payload: FirebaseSyncRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    decoded = verify_firebase_id_token(payload.id_token)
    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = decoded.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firebase token does not contain a verified email"
        )
    
    full_name = payload.full_name or decoded.get("name")
    user = await get_or_create_firebase_user(
        db=db,
        email=email,
        full_name=full_name,
        role=payload.role,
        department=payload.department
    )
    
    token = create_access_token(data={
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "dept": user.department.value
    })
    
    await record_audit_log(
        db=db,
        action="FIREBASE_USER_SYNC",
        user=user,
        target_type="USER",
        target_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        department=user.department
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
