import io
import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers
from app.models.enums import ObservationType, Department, TargetType

@pytest.mark.asyncio
async def test_forensic_and_financial_processing(client: AsyncClient, seed_users):
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # 1. Create a case
    case_res = await client.post(
        "/cases",
        json={"title": "Store Burglary Multi-Department", "case_type": "THEFT"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # 2. Upload and process Crime Scene Photo (FORENSIC)
    photo_bytes = b"EXIF_CRIME_SCENE_PHOTO_OF_SHELF"
    img_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("crime_scene_shelf.jpg", io.BytesIO(photo_bytes), "image/jpeg")},
        headers=headers
    )
    img_id = img_upload.json()["id"]
    assert img_upload.json()["evidence_type"] == "IMAGE"

    img_proc = await client.post(f"/cases/{case_id}/evidence/{img_id}/process", headers=headers)
    assert img_proc.status_code == 200
    assert img_proc.json()["status"] == "COMPLETED"

    # Verify forensic observations
    forensic_obs = await client.get(
        f"/cases/{case_id}/observations?department=FORENSIC",
        headers=headers
    )
    assert forensic_obs.status_code == 200
    f_items = forensic_obs.json()
    assert len(f_items) >= 1
    assert f_items[0]["observation_type"] == "PHYSICAL_MARK_DETECTED"
    assert f_items[0]["department"] == "FORENSIC"

    # 3. Upload and process Transactions Record (FINANCIAL)
    tx_csv = """transaction_id,timestamp,item,amount
TX-1001,2026-01-15T20:31:00Z,Phone Case,1500
TX-1002,2026-01-15T20:49:00Z,USB Cable,800
"""
    tx_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("transactions.csv", io.BytesIO(tx_csv.encode("utf-8")), "text/csv")},
        headers=headers
    )
    tx_id = tx_upload.json()["id"]
    assert tx_upload.json()["evidence_type"] == "TRANSACTION_RECORD"

    tx_proc = await client.post(f"/cases/{case_id}/evidence/{tx_id}/process", headers=headers)
    assert tx_proc.status_code == 200
    assert tx_proc.json()["status"] == "COMPLETED"

    # Verify financial observations
    fin_obs = await client.get(
        f"/cases/{case_id}/observations?department=FINANCIAL",
        headers=headers
    )
    assert fin_obs.status_code == 200
    fin_items = fin_obs.json()
    assert len(fin_items) == 1
    assert fin_items[0]["observation_type"] == "TRANSACTION_FLAGGED"
    assert fin_items[0]["department"] == "FINANCIAL"
    assert fin_items[0]["raw_data"]["anomaly_type"] in ("NO_MATCHING_TRANSACTION_RECORDED", "UNAUTHORIZED_REMOVAL_NO_PAYMENT")

@pytest.mark.asyncio
async def test_candidate_entity_linking_and_confirmation(client: AsyncClient, seed_users):
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # 1. Create Case
    case_res = await client.post(
        "/cases",
        json={"title": "Suspect Identification Case", "case_type": "THEFT"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # 2. Upload and process CCTV entrance
    cctv_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("cctv_entrance.mp4", io.BytesIO(b"CCTV_ENTRANCE_DATA"), "video/mp4")},
        headers=headers
    )
    cctv_id = cctv_upload.json()["id"]
    await client.post(f"/cases/{case_id}/evidence/{cctv_id}/process", headers=headers)

    # 3. Trigger auto-linking
    auto_link_res = await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    assert auto_link_res.status_code == 200
    links = auto_link_res.json()
    assert len(links) >= 1
    assert links[0]["is_human_confirmed"] is False

    link_id = links[0]["id"]
    entity_id = links[0]["candidate_entity_id"]

    # 4. Human confirmation of entity link
    confirm_res = await client.post(
        f"/cases/{case_id}/entities/{entity_id}/links/{link_id}/confirm",
        headers=headers
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["is_human_confirmed"] is True
    assert confirm_res.json()["confirmed_by"] == lead.id

    # 5. Fetch entity details and verify confirmed link is populated
    entity_res = await client.get(f"/cases/{case_id}/entities/{entity_id}", headers=headers)
    assert entity_res.status_code == 200
    e_data = entity_res.json()
    assert e_data["label"] == "P1"
    assert len(e_data["links"]) >= 1
    assert any(l["id"] == link_id and l["is_human_confirmed"] is True for l in e_data["links"])
