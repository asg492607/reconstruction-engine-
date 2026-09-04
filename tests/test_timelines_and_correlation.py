import io
import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers
from app.models.enums import GapConflictType, Significance, ClaimStrength

@pytest.mark.asyncio
async def test_timelines_correlation_and_gap_detection(client: AsyncClient, seed_users):
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # 1. Create Case
    case_res = await client.post(
        "/cases",
        json={"title": "Store Burglary Timeline Analysis", "case_type": "THEFT", "incident_time_observed": "2026-01-15T20:40:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # 2. Upload Entrance CCTV
    cctv_in = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("cctv_entrance.mp4", io.BytesIO(b"CCTV_ENTRANCE_DATA"), "video/mp4")},
        headers=headers
    )
    cctv_in_id = cctv_in.json()["id"]
    await client.post(f"/cases/{case_id}/evidence/{cctv_in_id}/process", headers=headers)

    # 3. Upload Aisle CCTV
    cctv_aisle = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("cctv_aisle.mp4", io.BytesIO(b"CCTV_AISLE_DATA"), "video/mp4")},
        headers=headers
    )
    cctv_aisle_id = cctv_aisle.json()["id"]
    await client.post(f"/cases/{case_id}/evidence/{cctv_aisle_id}/process", headers=headers)

    # 4. Upload Exit CCTV
    cctv_exit = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("cctv_exit.mp4", io.BytesIO(b"CCTV_EXIT_DATA"), "video/mp4")},
        headers=headers
    )
    cctv_exit_id = cctv_exit.json()["id"]
    await client.post(f"/cases/{case_id}/evidence/{cctv_exit_id}/process", headers=headers)

    # 5. Upload Witness Statement
    w_text = "I saw a person in a black jacket near the shelf around 8:40 PM."
    w_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("witness_statement.txt", io.BytesIO(w_text.encode("utf-8")), "text/plain")},
        headers=headers
    )
    w_id = w_upload.json()["id"]
    await client.post(f"/cases/{case_id}/evidence/{w_id}/process", headers=headers)

    # 6. Upload Inventory record confirming disappearance
    inv_csv = """item,status,delta
iPhone 15 Pro,MISSING,-1
"""
    inv_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("inventory_log.csv", io.BytesIO(inv_csv.encode("utf-8")), "text/csv")},
        headers=headers
    )
    inv_id = inv_upload.json()["id"]
    await client.post(f"/cases/{case_id}/evidence/{inv_id}/process", headers=headers)

    # 7. Upload Transactions record confirming no payment
    tx_csv = "transaction_id,timestamp,item,amount\nTX-1,2026-01-15T20:30:00Z,Screen Guard,500\n"
    tx_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("transactions.csv", io.BytesIO(tx_csv.encode("utf-8")), "text/csv")},
        headers=headers
    )
    tx_id = tx_upload.json()["id"]
    await client.post(f"/cases/{case_id}/evidence/{tx_id}/process", headers=headers)

    # 8. Correlate Timelines
    corr_res = await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)
    assert corr_res.status_code == 200
    corr_events = corr_res.json()
    assert len(corr_events) >= 6

    # 9. Verify Source Timelines are independently queryable
    src_res = await client.get(f"/cases/{case_id}/timelines/sources", headers=headers)
    assert src_res.status_code == 200
    sources = src_res.json()
    assert len(sources) >= 5

    # 10. Verify Gaps and Conflicts Detection
    gaps_res = await client.get(f"/cases/{case_id}/gaps-conflicts", headers=headers)
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    assert len(gaps) >= 2

    # Check for critical corridor blind spot gap
    corridor_gap = next((g for g in gaps if g["gc_type"] == "GAP"), None)
    assert corridor_gap is not None
    assert corridor_gap["significance"] == "CRITICAL"

    # Check for soft timestamp discrepancy between witness and camera
    disc = next((g for g in gaps if g["gc_type"] == "SOFT_DISCREPANCY"), None)
    assert disc is not None

    # Check for hard contradiction (item missing vs zero sales)
    theft_contradiction = next((g for g in gaps if g["gc_type"] == "HARD_CONTRADICTION"), None)
    assert theft_contradiction is not None

    # 11. Resolve a gap with note
    resolve_res = await client.patch(
        f"/cases/{case_id}/gaps-conflicts/{corridor_gap['id']}/resolve",
        json={"resolution_note": "Blind spot verified. Supplementary hallway camera footage requested from mall security."},
        headers=headers
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["is_resolved"] is True
    assert resolve_res.json()["resolved_by"] == lead.id

    # 12. Create analytical Finding & Claim
    finding_res = await client.post(
        f"/cases/{case_id}/findings",
        json={
            "department": "INVESTIGATION",
            "finding_type": "MOVEMENT_PATH",
            "description": "Individual entered store at 8:37 PM, spent 3 minutes near display case, and exited at 8:46 PM with concealed item.",
            "detection_confidence": 0.88,
            "corroboration_count": 3
        },
        headers=headers
    )
    assert finding_res.status_code == 201
    finding_id = finding_res.json()["id"]

    claim_res = await client.post(
        f"/cases/{case_id}/claims",
        json={
            "claim_text": "Candidate Entity P1 was in immediate physical proximity to the missing iPhone at 8:42 PM without recording a valid sale.",
            "finding_ids": [finding_id],
            "claim_strength": "STRONG"
        },
        headers=headers
    )
    assert claim_res.status_code == 201
    assert claim_res.json()["claim_strength"] == "STRONG"
