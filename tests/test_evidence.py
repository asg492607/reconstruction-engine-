import io
import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers

@pytest.mark.asyncio
async def test_evidence_upload_routing_and_provenance(client: AsyncClient, seed_users):
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # 1. Create a Case
    case_res = await client.post(
        "/cases",
        json={"title": "Electronics Store Theft", "case_type": "THEFT"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # 2. Upload CCTV video file
    video_content = b"SIMULATED_CCTV_H264_STREAM_CONTENT_FRAME_001_TO_500"
    files = {"file": ("cctv_entrance.mp4", io.BytesIO(video_content), "video/mp4")}
    
    upload_res = await client.post(
        f"/cases/{case_id}/evidence",
        files=files,
        headers=headers
    )
    assert upload_res.status_code == 201
    ev_data = upload_res.json()
    evidence_id = ev_data["id"]
    assert ev_data["evidence_type"] == "CCTV"
    assert len(ev_data["sha256_hash"]) == 64
    assert ev_data["file_size_bytes"] == len(video_content)
    assert "INVESTIGATION" in ev_data["authorized_departments"]
    assert "FORENSIC" in ev_data["authorized_departments"]

    # 3. Download evidence and verify byte exactness
    dl_res = await client.get(f"/cases/{case_id}/evidence/{evidence_id}/download", headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.content == video_content

    # 4. Check routing endpoint
    routing_res = await client.get(f"/cases/{case_id}/evidence/{evidence_id}/routing", headers=headers)
    assert routing_res.status_code == 200
    r_data = routing_res.json()
    assert r_data["evidence_type"] == "CCTV"
    assert r_data["is_classified"] is True

    # 5. Manual classification override
    classify_res = await client.post(
        f"/cases/{case_id}/evidence/{evidence_id}/classify",
        json={
            "authorized_departments": ["INVESTIGATION"],
            "classification_notes": "Contains sensitive entrance camera restricted to primary detectives"
        },
        headers=headers
    )
    assert classify_res.status_code == 200
    assert classify_res.json()["authorized_departments"] == ["INVESTIGATION"]

    # 6. Check provenance
    prov_res = await client.get(f"/cases/{case_id}/evidence/{evidence_id}/provenance", headers=headers)
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert prov_data["evidence_id"] == evidence_id
    assert prov_data["sha256_hash"] == ev_data["sha256_hash"]
