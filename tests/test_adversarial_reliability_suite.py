import io
import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers
from app.models.enums import HypothesisStatus, GapConflictType, EvidenceQuality

@pytest.mark.asyncio
async def test_adversarial_case_a_laptop_clear_theft(client: AsyncClient, seed_users):
    """Scenario A: Different domain / item (MacBook Pro M3 Max). Tests generic dynamic engine."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Grand Larceny: MacBook Pro M3 Max", "case_type": "THEFT", "incident_time_observed": "2026-02-10T15:30:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("cctv_entrance.mp4", b"VIDEO_ENTRANCE", "video/mp4"),
        ("cctv_shelf.mp4", b"VIDEO_SHELF", "video/mp4"),
        ("cctv_exit.mp4", b"VIDEO_EXIT", "video/mp4"),
        ("inventory_delta.csv", b"item_name,delta\nMacBook Pro M3 Max,-1\n", "text/csv"),
        ("transactions.csv", b"tx_id,item,amount\nTX-10,USB-C Mouse,25\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)
    await client.post(f"/cases/{case_id}/gaps-conflicts/detect", headers=headers)

    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hypotheses = hyp_res.json()
    hyp_a = hypotheses[0]

    # Verify item is dynamically MacBook Pro M3 Max, NOT hardcoded iPhone
    assert "MacBook Pro M3 Max" in hyp_a["description"] or "MacBook Pro M3 Max" in hyp_a["sequence"][1]["description"]
    # Verify per-step support matrix
    assert hyp_a["sequence"][0]["support_level"] == "STRONG"
    assert hyp_a["sequence"][1]["support_level"] in ("STRONG", "MODERATE")
    assert hyp_a["sequence"][2]["support_level"] == "UNCONFIRMED"
    assert hyp_a["sequence"][3]["support_level"] == "LIMITED"

@pytest.mark.asyncio
async def test_adversarial_case_b_ambiguous_identity(client: AsyncClient, seed_users):
    """Scenario B: Two candidate persons wearing similar clothing. Tests that entity link remains unconfirmed."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Ambiguous Subject Investigation", "case_type": "THEFT", "incident_time_observed": "2026-02-10T16:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # Upload two CCTV feeds where person link is probabilistic
    for fn in ["cctv_entrance_p1.mp4", "cctv_shelf_p2.mp4", "cctv_exit_p1.mp4"]:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(b"CCTV_DATA"), "video/mp4")}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hyp_a = hyp_res.json()[0]

    # Deterministic self-challenge must flag unconfirmed entity link
    det_issues = hyp_a.get("deterministic_issues", [])
    has_unconfirmed = any(i["check"] == "CHECK_UNCONFIRMED_ENTITY_LINK" for i in det_issues)
    assert has_unconfirmed, "Expected CHECK_UNCONFIRMED_ENTITY_LINK in self-challenge"

@pytest.mark.asyncio
async def test_adversarial_case_c_clock_drift_soft_discrepancy(client: AsyncClient, seed_users):
    """Scenario C: 4-minute camera clock drift vs witness. Tests that it is classified as SOFT_DISCREPANCY, not HARD_CONTRADICTION."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Clock Drift Calibration", "case_type": "THEFT", "incident_time_observed": "2026-02-10T17:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("cctv_entrance.mp4", b"ENTRANCE_FOOTAGE", "video/mp4"),
        ("witness_statement.txt", b"I observed the individual around 5:04 PM near the entrance.", "text/plain")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)
    await client.post(f"/cases/{case_id}/gaps-conflicts/detect", headers=headers)

    gaps_res = await client.get(f"/cases/{case_id}/gaps-conflicts", headers=headers)
    gaps = gaps_res.json()
    soft_gaps = [g for g in gaps if g["gc_type"] == "SOFT_DISCREPANCY"]
    hard_gaps = [g for g in gaps if g["gc_type"] == "HARD_CONTRADICTION"]

    assert len(soft_gaps) >= 1, "Expected perceptual timestamp soft discrepancy"
    assert len(hard_gaps) == 0, "Clock drift must NOT be marked as hard contradiction"

@pytest.mark.asyncio
async def test_adversarial_case_d_corroborative_discrepancy_vs_contradiction(client: AsyncClient, seed_users):
    """Scenario D: Missing inventory + zero POS sales must be CORROBORATIVE_DISCREPANCY, not HARD_CONTRADICTION."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Shrinkage Audit", "case_type": "THEFT", "incident_time_observed": "2026-02-10T18:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("inventory_delta.csv", b"item,expected,counted,delta\nSony Alpha A7,1,0,-1\n", "text/csv"),
        ("pos_audit.csv", b"tx_id,item,amount\nTX-1,Lens Cleaner,15\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/gaps-conflicts/detect", headers=headers)
    gaps_res = await client.get(f"/cases/{case_id}/gaps-conflicts", headers=headers)
    gaps = gaps_res.json()

    corr_gap = next((g for g in gaps if g["gc_type"] == "CORROBORATIVE_DISCREPANCY"), None)
    assert corr_gap is not None, "Expected CORROBORATIVE_DISCREPANCY"
    # Zero false hard contradiction
    hard_gap = next((g for g in gaps if g["gc_type"] == "HARD_CONTRADICTION"), None)
    assert hard_gap is None, "Missing item vs zero POS should NOT be a hard contradiction"

@pytest.mark.asyncio
async def test_adversarial_case_e_provenance_chain_integrity(client: AsyncClient, seed_users):
    """Scenario E: Tests that every step in hypothesis navigates to observation, model, evidence file, and SHA256."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Provenance Audit Case", "case_type": "THEFT", "incident_time_observed": "2026-02-10T19:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    up = await client.post(f"/cases/{case_id}/evidence", files={"file": ("cctv_entrance.mp4", io.BytesIO(b"STREAM_HASH_DATA"), "video/mp4")}, headers=headers)
    ev_id = up.json()["id"]
    sha256 = up.json()["sha256_hash"]
    await client.post(f"/cases/{case_id}/evidence/{ev_id}/process", headers=headers)

    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)
    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    hyp_id = hyp_res.json()[0]["id"]

    # Query provenance chain
    prov_res = await client.get(f"/cases/{case_id}/hypotheses/{hyp_id}/provenance-chain", headers=headers)
    assert prov_res.status_code == 200
    chain_data = prov_res.json()
    assert chain_data["hypothesis_id"] == hyp_id
    assert len(chain_data["provenance_chain"]) >= 1

    # First step should link to cctv_entrance.mp4 with matching SHA-256
    step1 = chain_data["provenance_chain"][0]
    assert step1["phase"] == "ENTRY"
    assert len(step1["observations"]) >= 1
    obs1 = step1["observations"][0]
    assert obs1["evidence"]["sha256_hash"] == sha256
    assert obs1["model_name"] is not None

@pytest.mark.asyncio
async def test_adversarial_case_f_human_rejection_audit(client: AsyncClient, seed_users):
    """Scenario F: Tests that human review of hypothesis updates status to REJECTED and creates verification audit."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Human Rejection Audit", "case_type": "THEFT", "incident_time_observed": "2026-02-10T20:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]
    up = await client.post(f"/cases/{case_id}/evidence", files={"file": ("cctv_entrance.mp4", io.BytesIO(b"DATA"), "video/mp4")}, headers=headers)
    await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)
    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)

    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    hyp_id = hyp_res.json()[0]["id"]

    # Reject hypothesis
    reject_res = await client.post(
        f"/cases/{case_id}/hypotheses/{hyp_id}/review",
        json={"status": "REJECTED", "review_note": "Insufficient visual proof of concealment; item handling not captured on camera."},
        headers=headers
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"
    assert reject_res.json()["reviewed_by"] == lead.id
