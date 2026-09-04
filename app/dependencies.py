from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.security import decode_access_token
from app.auth.service import get_user_by_id
from app.models.entities import User
from app.models.enums import Role, Department
from app.policy import Action, check_access

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = await get_user_by_id(db, user_id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or non-existent user"
        )
    return user

def require_role(*allowed_roles: Role) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == Role.ADMIN:
            return current_user
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role: {current_user.role}"
            )
        return current_user
    return role_checker

def require_department(*allowed_departments: Department) -> Callable:
    async def department_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == Role.ADMIN:
            return current_user
        if current_user.department not in allowed_departments:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation restricted to departments: {[d.value for d in allowed_departments]}"
            )
        return current_user
    return department_checker
