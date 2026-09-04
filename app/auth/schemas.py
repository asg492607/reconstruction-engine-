from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.enums import Role, Department

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Role = Role.INVESTIGATOR
    department: Department = Department.INVESTIGATION
    organization_name: Optional[str] = "Default Police Department"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class FirebaseSyncRequest(BaseModel):
    id_token: str
    role: Optional[Role] = Role.INVESTIGATOR
    department: Optional[Department] = Department.INVESTIGATION
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: Role
    department: Department

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: Role
    department: Department
    organization_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
