from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import User, Organization
from app.models.enums import Role, Department
from app.auth.security import hash_password, verify_password
from app.auth.schemas import UserRegister

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_or_create_organization(db: AsyncSession, name: str) -> Organization:
    result = await db.execute(select(Organization).where(Organization.name == name))
    org = result.scalar_one_or_none()
    if not org:
        org = Organization(name=name)
        db.add(org)
        await db.commit()
        await db.refresh(org)
    return org

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user

async def create_user(db: AsyncSession, user_in: UserRegister) -> User:
    org = await get_or_create_organization(db, user_in.organization_name or "Default Organization")
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        department=user_in.department,
        organization_id=org.id,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_or_create_firebase_user(
    db: AsyncSession,
    email: str,
    full_name: Optional[str] = None,
    role: Optional[Role] = None,
    department: Optional[Department] = None
) -> User:
    import secrets
    user = await get_user_by_email(db, email)
    if user:
        updated = False
        if full_name and not user.full_name:
            user.full_name = full_name
            updated = True
        if role and user.role != role:
            user.role = role
            updated = True
        if department and user.department != department:
            user.department = department
            updated = True
        if updated:
            await db.commit()
            await db.refresh(user)
        return user

    org = await get_or_create_organization(db, "Default Police Department")
    dummy_password = secrets.token_urlsafe(32)
    user = User(
        email=email,
        hashed_password=hash_password(dummy_password),
        full_name=full_name or email.split("@")[0],
        role=role or Role.INVESTIGATOR,
        department=department or Department.INVESTIGATION,
        organization_id=org.id,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
