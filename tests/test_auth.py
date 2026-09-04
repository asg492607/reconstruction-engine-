import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # 1. Register new user
    reg_payload = {
        "email": "new_officer@police.gov",
        "password": "securepassword123",
        "full_name": "Officer Blake",
        "role": "INVESTIGATOR",
        "department": "INVESTIGATION",
        "organization_name": "Metropolitan Police"
    }
    res = await client.post("/auth/register", json=reg_payload)
    assert res.status_code == 201
    user_data = res.json()
    assert user_data["email"] == "new_officer@police.gov"
    assert user_data["role"] == "INVESTIGATOR"

    # 2. Login
    login_payload = {
        "email": "new_officer@police.gov",
        "password": "securepassword123"
    }
    res = await client.post("/auth/login/json", json=login_payload)
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" == "access_token"
    assert token_data["token_type"] == "bearer"

    # 3. Access protected /auth/me
    token = token_data["access_token"]
    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    me_data = res.json()
    assert me_data["email"] == "new_officer@police.gov"

@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, seed_users):
    login_payload = {
        "email": "lead@police.gov",
        "password": "wrongpassword"
    }
    res = await client.post("/auth/login/json", json=login_payload)
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_firebase_sync_endpoint(client: AsyncClient, monkeypatch):
    import app.auth.router as auth_router_mod
    monkeypatch.setattr(
        auth_router_mod,
        "verify_firebase_id_token",
        lambda token: {"email": "agent.smith@fbi.gov", "name": "Agent Smith"} if token == "valid-fb-token" else None
    )

    # 1. Invalid token
    res = await client.post("/auth/firebase-sync", json={"id_token": "bad-token"})
    assert res.status_code == 401

    # 2. Valid token sync
    res = await client.post("/auth/firebase-sync", json={
        "id_token": "valid-fb-token",
        "role": "INVESTIGATOR",
        "department": "INVESTIGATION",
        "full_name": "Agent Smith"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "agent.smith@fbi.gov"
    assert "access_token" in data

    # 3. Test access with returned token
    token = data["access_token"]
    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "agent.smith@fbi.gov"
