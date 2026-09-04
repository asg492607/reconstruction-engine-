import io
import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers

@pytest.mark.asyncio
async def test_abac_policy_enforcement(client: AsyncClient, seed_users):
    lead = seed_users["lead"]
    outsider = seed_users["unassigned"]
    financial = seed_users["financial"]
    admin = seed_users["admin"]

    lead_headers = get_auth_headers(lead)
    outsider_headers = get_auth_headers(outsider)
    fin_headers = get_auth_headers(financial)
    admin_headers = get_auth_headers(admin)

    # 1. Lead creates a case
    case_res = await client.post(
        "/cases",
        json={"title": "High Security Bank Vault Theft", "case_type": "THEFT"},
        headers=lead_headers
    )
    case_id = case_res.json()["id"]

    # 2. Unassigned officer attempts to view case -> Denied (403)
    outsider_res = await client.get(f"/cases/{case_id}", headers=outsider_headers)
    assert outsider_res.status_code == 403

    # 3. Unassigned officer attempts to upload evidence -> Denied (403)
    upload_res = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("vault_scan.png", io.BytesIO(b"data"), "image/png")},
        headers=outsider_headers
    )
    assert upload_res.status_code == 403

    # 4. Assign financial analyst to the case
    await client.post(
        f"/cases/{case_id}/assign",
        json={"user_id": financial.id, "department": "FINANCIAL"},
        headers=lead_headers
    )

    # 5. Financial analyst can now view case details
    fin_case_res = await client.get(f"/cases/{case_id}", headers=fin_headers)
    assert fin_case_res.status_code == 200

    # 6. Upload CCTV evidence (only INVESTIGATION and FORENSIC authorized)
    cctv_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("vault_cctv.mp4", io.BytesIO(b"cctv_stream"), "video/mp4")},
        headers=lead_headers
    )
    cctv_id = cctv_upload.json()["id"]

    # 7. Financial analyst attempts to view/download CCTV evidence -> Denied (403) due to department policy
    fin_dl = await client.get(f"/cases/{case_id}/evidence/{cctv_id}/download", headers=fin_headers)
    assert fin_dl.status_code == 403

    # 8. Admin bypasses assignment and department restriction
    admin_dl = await client.get(f"/cases/{case_id}/evidence/{cctv_id}/download", headers=admin_headers)
    assert admin_dl.status_code == 200
