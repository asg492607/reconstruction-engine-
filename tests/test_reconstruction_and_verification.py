import io
import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers
from app.models.enums import HypothesisStatus, VerificationAction, ClaimStrength

@pytest.mark.asyncio
async def test_reconstruction_engine_and_self_challenge(client: AsyncClient, seed_users):
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # 1. Create Case
    case_res = await client.post(
        "/cases",
        json={"title": "Retail Theft Reconstruction", "case_type": "THEFT", "incident_time_observed": "2026-01-15T20:40:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # 2. Upload and process entrance CCTV, aisle CCTV, exit CCTV, witness statement, inventory, and transactions
    files_to_upload = [
        ("cctv_entrance.mp4", b"ENTRANCE_STREAM", "video/mp4"),
        ("cctv_aisle.mp4", b"AISLE_STREAM", "video/mp4"),
        ("cctv_exit.mp4", b"EXIT_STREAM", "video/mp4"),
        ("witness_statement.txt", b"I saw a person in a black jacket near the shelf around 8:40 PM.", "text/plain"),
        ("inventory_log.csv", b"item,status,delta\niPhone 15 Pro,MISSING,-1\n", "text/csv"),
        ("transactions.csv", b"transaction_id,timestamp,item,amount\nTX-1,2026-01-15T20:30:00Z,Accessory,200\n", "text/csv")
    ]

    for fn, content, mime in files_to_upload:
        ev_res = await client.post(
            f"/cases/{case_id}/evidence",
            files={"file": (fn, io.BytesIO(content), mime)},
            headers=headers
        )
        ev_id = ev_res.json()["id"]
        await client.post(f"/cases/{case_id}/evidence/{ev_id}/process", headers=headers)

    # 3. Auto-link candidate entities and correlate timelines
    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)

    # 4. Generate Hypotheses (Evidence-constrained Reconstruction)
    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hypotheses = hyp_res.json()
    assert len(hypotheses) == 2

    hyp_a = next((h for h in hypotheses if "Hypothesis A" in h["label"]), None)
    hyp_b = next((h for h in hypotheses if "Hypothesis B" in h["label"]), None)

    assert hyp_a is not None
    assert hyp_a["overall_strength"] == "STRONG"
    assert len(hyp_a["sequence"]) == 4

    # Verify Self-Challenge Layer 1 (Deterministic checks ran)
    assert len(hyp_a["deterministic_issues"]) >= 1
    unconfirmed_check = next((i for i in hyp_a["deterministic_issues"] if i["check"] == "CHECK_UNCONFIRMED_ENTITY_LINK"), None)
    assert unconfirmed_check is not None

    # Verify Self-Challenge Layer 2 (AI Adversarial Review ran)
    assert len(hyp_a["ai_challenge_notes"]) >= 1
    blind_spot_note = next((n for n in hyp_a["ai_challenge_notes"] if "BLIND_SPOT" in n.get("dimension", "")), None)
    assert blind_spot_note is not None


    # 5. Human Review of Hypothesis
    review_res = await client.post(
        f"/cases/{case_id}/hypotheses/{hyp_a['id']}/review",
        json={
            "status": "ACCEPTED",
            "review_note": "Hypothesis A accepted based on corroborating CCTV timestamps and physical tether damage."
        },
        headers=headers
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "ACCEPTED"
    assert review_res.json()["reviewed_by"] == lead.id

    # 6. Human Verification workflow: query pending verifications
    pending_res = await client.get(f"/cases/{case_id}/verifications/pending", headers=headers)
    assert pending_res.status_code == 200
    p_data = pending_res.json()
    assert len(p_data["pending_observations"]) >= 1

    first_obs_id = p_data["pending_observations"][0]["id"]

    # Verify / Accept an observation
    obs_ver_res = await client.post(
        f"/cases/{case_id}/verifications/observations/{first_obs_id}",
        json={
            "action": "ACCEPTED",
            "note": "Verified by lead investigator against surveillance high-resolution export."
        },
        headers=headers
    )
    assert obs_ver_res.status_code == 200
    assert obs_ver_res.json()["action"] == "ACCEPTED"
    assert obs_ver_res.json()["verified_by"] == lead.id
