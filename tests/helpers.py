from app.models.entities import User
from app.auth.security import create_access_token

def get_auth_headers(user: User) -> dict:
    token = create_access_token(data={
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "dept": user.department.value
    })
    return {"Authorization": f"Bearer {token}"}
