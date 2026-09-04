import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers

@pytest.mark.asyncio
async def test_case_lifecycle_and_snapshots(client: AsyncClient, seed_users):
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # 1. Create Case
    case_payload = {
        "title": "Jewelry Shop Nighttime Theft",
        "case_type": "THEFT",
        "incident_location": "Central Plaza Mall, Sector 4",
        "incident_time_observed": "2026-01-15T20:45:00Z",
        "incident_time_estimated": {"min": "2026-01-15T20:30:00Z", "max": "2026-01-15T21:00:00Z"}
    }
    res = await client.post("/cases", json=case_payload, headers=headers)
    assert res.status_code == 201
    case_data = res.json()
    case_id = case_data["id"]
    assert case_data["case_number"].startswith("THF-")
    assert case_data["status"] == "CREATED"
    assert case_data["current_version"] == 1

    # 2. Transition status: CREATED -> EVIDENCE_COLLECTION (Valid)
    patch_res = await client.patch(
        f"/cases/{case_id}",
        json={"status": "EVIDENCE_COLLECTION"},
        headers=headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "EVIDENCE_COLLECTION"

    # 3. Illegal Transition: EVIDENCE_COLLECTION -> RECONSTRUCTION (Invalid, must go to ANALYSIS first)
    bad_patch = await client.patch(
        f"/cases/{case_id}",
        json={"status": "RECONSTRUCTION"},
        headers=headers
    )
    assert bad_patch.status_code == 400
    assert "Illegal case state transition" in bad_patch.json()["detail"]

    # 4. Valid Transition: EVIDENCE_COLLECTION -> ANALYSIS
    analysis_patch = await client.patch(
        f"/cases/{case_id}",
        json={"status": "ANALYSIS"},
        headers=headers
    )
    assert analysis_patch.status_code == 200
    assert analysis_patch.json()["status"] == "ANALYSIS"

    # 5. Assign forensic officer to case
    forensic = seed_users["forensic"]
    assign_res = await client.post(
        f"/cases/{case_id}/assign",
        json={"user_id": forensic.id, "department": "FORENSIC"},
        headers=headers
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["user_id"] == forensic.id

    # 6. Create Case Version Snapshot
    snap_res = await client.post(
        f"/cases/{case_id}/snapshot",
        json={"reason": "Completed initial scene examination"},
        headers=headers
    )
    assert snap_res.status_code == 200
    snap_data = snap_res.json()
    assert snap_data["version_number"] == 2
    assert snap_data["snapshot"]["case"]["status"] == "ANALYSIS"

    # 7. List versions
    versions_res = await client.get(f"/cases/{case_id}/versions", headers=headers)
    assert versions_res.status_code == 200
    versions = versions_res.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 2
