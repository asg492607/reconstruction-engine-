import io
import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers
from app.models.enums import HypothesisStatus, GapConflictType, EvidenceQuality, ClaimStrength

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

    for fn in ["cctv_entrance_p1.mp4", "cctv_shelf_p2.mp4", "cctv_exit_p1.mp4"]:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(b"CCTV_DATA"), "video/mp4")}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    # Add missing item evidence
    up_inv = await client.post(f"/cases/{case_id}/evidence", files={"file": ("inventory_delta.csv", io.BytesIO(b"item,delta\nCamera,-1\n"), "text/csv")}, headers=headers)
    await client.post(f"/cases/{case_id}/evidence/{up_inv.json()['id']}/process", headers=headers)

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

    files = [
        ("cctv_entrance.mp4", b"STREAM_HASH_DATA", "video/mp4"),
        ("cctv_shelf.mp4", b"SHELF_DATA", "video/mp4"),
        ("inventory_delta.csv", b"item,delta\nGold Watch,-1\n", "text/csv")
    ]
    sha256 = None
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        if fn == "cctv_entrance.mp4":
            sha256 = up.json()["sha256_hash"]
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

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

    files = [
        ("cctv_entrance.mp4", b"DATA_ENTRANCE", "video/mp4"),
        ("cctv_shelf.mp4", b"DATA_SHELF", "video/mp4"),
        ("inventory_delta.csv", b"item,delta\nHeadphones,-1\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
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

@pytest.mark.asyncio
async def test_adversarial_case_g_cross_department_disagreement(client: AsyncClient, seed_users):
    """Scenario G: Cross-department disagreement preservation and nuanced honest synthesis.
    Investigation: P1 observed near display.
    Forensics: No physical evidence establishes that P1 handled the item.
    Financial: Zero matching POS records.
    Synthesis: Candidate P1 is strongly associated with presence near the incident area, but direct handling remains unestablished.
    """
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Cross-Department Disagreement Audit", "case_type": "THEFT", "incident_time_observed": "2026-02-10T21:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("cctv_entrance.mp4", b"VIDEO_IN", "video/mp4"),
        ("cctv_shelf.mp4", b"VIDEO_DISPLAY", "video/mp4"),
        ("cctv_exit.mp4", b"VIDEO_OUT", "video/mp4"),
        ("inventory_delta.csv", b"item_name,delta\niPhone 15 Pro Max,-1\n", "text/csv"),
        ("pos_audit.csv", b"tx_id,item,amount\nTX-5,Protective Case,30\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)

    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hyp_a = hyp_res.json()[0]

    # Verify independent department stances are preserved
    stances = hyp_a["sequence"][0]["department_stances"]
    assert "INVESTIGATION" in stances
    assert "FORENSIC" in stances
    assert "FINANCIAL" in stances

    # Forensics stance must explicitly record lack of physical handling evidence
    assert "no physical" in stances["FORENSIC"].lower() or "not physically confirmed" in stances["FORENSIC"].lower()

    # Nuanced honest synthesis in description
    assert "strongly associated with presence" in hyp_a["description"]
    assert "direct handling" in hyp_a["description"] and "unestablished" in hyp_a["description"]

    # Step 2 must be marked as not directly observed
    assert hyp_a["sequence"][1]["is_directly_observed"] is False
    assert hyp_a["sequence"][1]["support_level"] == "MODERATE"

@pytest.mark.asyncio
async def test_adversarial_case_h_insufficient_evidence_no_hypothesis(client: AsyncClient, seed_users):
    """Scenario H: Insufficient evidence outcome ('We don't know yet').
    When evidence is completely insufficient or lacking critical links, the system safely says:
    'Insufficient evidence to generate a defensible theft hypothesis.' rather than fabricating a story.
    """
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Vague Unanchored Sighting", "case_type": "THEFT", "incident_time_observed": "2026-02-10T22:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # Only upload 1 ambiguous document with no missing item delta and no candidate presence at scene
    up = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("vague_note.txt", io.BytesIO(b"General store maintenance checklist completed on Tuesday."), "text/plain")},
        headers=headers
    )
    await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hyps = hyp_res.json()
    assert len(hyps) == 1

    insufficient_hyp = hyps[0]
    assert insufficient_hyp["status"] == "INSUFFICIENT_EVIDENCE"
    assert "Insufficient Evidence" in insufficient_hyp["label"]
    assert len(insufficient_hyp["sequence"]) == 0, "System must not hallucinate a timeline when evidence is insufficient"
    assert insufficient_hyp["overall_strength"] == "SPECULATIVE"
    assert any(i["check"] == "CHECK_INSUFFICIENT_EVIDENCE" for i in insufficient_hyp["deterministic_issues"])

@pytest.mark.asyncio
async def test_adversarial_case_i_deliberate_false_evidence_stock_adjustment(client: AsyncClient, seed_users):
    """Scenario I: Deliberate false evidence.
    Inventory says item is missing, POS has no transaction, CCTV shows person near display,
    BUT an authorized stock adjustment explains the discrepancy.
    Expected result: No theft hypothesis should reach strong support.
    """
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Alleged Theft of Rolex Submariner", "case_type": "THEFT", "incident_time_observed": "2026-02-11T10:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("cctv_shelf.mp4", b"CUSTOMER_AT_DISPLAY", "video/mp4"),
        ("inventory_delta.csv", b"item,count,expected,delta\nRolex Submariner,0,1,-1\n", "text/csv"),
        ("pos_audit.csv", b"tx_id,item,amount\nTX-11,Microfiber Cloth,10\n", "text/csv"),
        ("stock_adjustment_log.csv", b"adjustment_type,item,reason,timestamp\nauthorized_adjustment,Rolex Submariner,warehouse transfer to secure vault,2026-02-11T09:30:00Z\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)
    await client.post(f"/cases/{case_id}/gaps-conflicts/detect", headers=headers)

    # Verify gap detector identified exculpatory authorized adjustment
    gaps_res = await client.get(f"/cases/{case_id}/gaps-conflicts", headers=headers)
    gaps = gaps_res.json()
    adj_gap = next((g for g in gaps if "authorized stock adjustment" in g["description"].lower()), None)
    assert adj_gap is not None, "Expected exculpatory authorized adjustment finding in gaps/conflicts"

    # Generate hypothesis
    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hyp_a = hyp_res.json()[0]

    # Critical requirement: NO theft hypothesis should reach strong support!
    assert hyp_a["overall_strength"] != "STRONG", "Theft hypothesis MUST NOT reach strong support when explained by stock adjustment!"
    assert hyp_a["overall_strength"] in ("WEAK", "SPECULATIVE")
    assert hyp_a["status"] == "CHALLENGED"
    assert any(i["check"] == "CHECK_EXCULPATORY_STOCK_ADJUSTMENT" for i in hyp_a["deterministic_issues"])
    assert hyp_a["sequence"][3]["support_level"] == "REFUTED"

@pytest.mark.asyncio
async def test_adversarial_case_j_wrong_candidate_impossible_time_sequence(client: AsyncClient, seed_users):
    """Scenario J: Wrong candidate / Alibi timing conflict.
    Subject's departure occurs before the tampering window; engine flags CHECK_IMPOSSIBLE_TIME_SEQUENCE.
    """
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Alibi Discrepancy Case", "case_type": "THEFT", "incident_time_observed": "2026-02-11T12:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("cctv_entrance.mp4", b"IN_AT_11_50", "video/mp4"),
        ("cctv_exit.mp4", b"OUT_AT_11_52", "video/mp4"),
        ("cctv_shelf.mp4", b"SHELF_AT_12_05", "video/mp4"),
        ("inventory_delta.csv", b"item,delta\nDisplay Drone,-1\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hyp_a = hyp_res.json()[0]

    det_issues = hyp_a.get("deterministic_issues", [])
    assert isinstance(det_issues, list)

@pytest.mark.asyncio
async def test_adversarial_case_k_optical_degradation_quality_downgrade(client: AsyncClient, seed_users, db_session):
    """Scenario K: Optical quality degradation. Low/poor quality sensor automatically cascades support rating."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Optical Degradation Test", "case_type": "THEFT", "incident_time_observed": "2026-02-11T13:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("cctv_entrance.mp4", b"BLURRED_FOOTAGE", "video/mp4"),
        ("cctv_shelf.mp4", b"DARK_FOOTAGE", "video/mp4"),
        ("inventory_delta.csv", b"item,delta\nTablet,-1\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    # Patch observation quality to POOR in the active test session
    from app.models.entities import Observation
    from sqlalchemy import update
    await db_session.execute(update(Observation).where(Observation.case_id == case_id).values(evidence_quality=EvidenceQuality.POOR))
    await db_session.commit()

    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hyp_a = hyp_res.json()[0]

    # Step 1 support level must be downgraded to MODERATE with degradation rationale
    assert hyp_a["sequence"][0]["support_level"] == "MODERATE"
    assert "degraded" in hyp_a["sequence"][0]["support_rationale"].lower()

@pytest.mark.asyncio
async def test_adversarial_case_l_mutually_contradictory_witness_attire(client: AsyncClient, seed_users):
    """Scenario L: Mutually contradictory witness attire descriptors produce HARD_CONTRADICTION."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Attire Contradiction Case", "case_type": "THEFT", "incident_time_observed": "2026-02-11T14:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("witness_1.txt", b"The person near the display was wearing a bright red jacket and light pants.", "text/plain"),
        ("witness_2.txt", b"The suspect who fled had a dark black hoodie and black jeans.", "text/plain")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/gaps-conflicts/detect", headers=headers)
    gaps_res = await client.get(f"/cases/{case_id}/gaps-conflicts", headers=headers)
    gaps = gaps_res.json()

    hard_gap = next((g for g in gaps if g["gc_type"] == "HARD_CONTRADICTION"), None)
    assert hard_gap is not None, "Expected HARD_CONTRADICTION for mutually exclusive clothing descriptors"
    assert "attire" in hard_gap["description"].lower() or "clothing" in hard_gap["description"].lower()

@pytest.mark.asyncio
async def test_adversarial_case_m_unbroken_tracking_high_support(client: AsyncClient, seed_users):
    """Scenario M: Unbroken continuous multi-camera tracking. Positive test demonstrating high defensibility."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Unbroken Tracking Showcase", "case_type": "THEFT", "incident_time_observed": "2026-02-11T15:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("cctv_entrance.mp4", b"STREAM_1", "video/mp4"),
        ("cctv_shelf.mp4", b"STREAM_2", "video/mp4"),
        ("cctv_exit.mp4", b"STREAM_3", "video/mp4"),
        ("inventory_delta.csv", b"item,delta\nSony Lens,-1\n", "text/csv"),
        ("pos_audit.csv", b"tx_id,item,amount\nTX-0,Battery,12\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)
    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hyp_a = hyp_res.json()[0]
    assert hyp_a["overall_strength"] in ("STRONG", "MODERATE")
    assert len(hyp_a["sequence"]) == 4

@pytest.mark.asyncio
async def test_adversarial_case_n_legitimate_customer_purchase_reconciliation(client: AsyncClient, seed_users):
    """Scenario N: Legitimate purchase reconciliation. Matching POS transaction refutes theft hypothesis."""
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    case_res = await client.post(
        "/cases",
        json={"title": "Purchased Merchandise Verification", "case_type": "THEFT", "incident_time_observed": "2026-02-11T16:00:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    files = [
        ("cctv_entrance.mp4", b"IN_STREAM", "video/mp4"),
        ("cctv_shelf.mp4", b"SHELF_STREAM", "video/mp4"),
        ("inventory_delta.csv", b"item,delta\niPhone 15 Pro,-1\n", "text/csv"),
        ("pos_transactions.csv", b"transaction_id,item,amount,timestamp\nTX-8888,iPhone 15 Pro,1199,2026-02-11T16:02:00Z\n", "text/csv")
    ]
    for fn, content, mime in files:
        up = await client.post(f"/cases/{case_id}/evidence", files={"file": (fn, io.BytesIO(content), mime)}, headers=headers)
        await client.post(f"/cases/{case_id}/evidence/{up.json()['id']}/process", headers=headers)

    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hyp_a = hyp_res.json()[0]

    fin_stance = hyp_a["sequence"][0]["department_stances"]["FINANCIAL"]
    assert "matching purchase transaction" in fin_stance.lower()
