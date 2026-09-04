import io
import pytest
from httpx import AsyncClient
from tests.helpers import get_auth_headers

@pytest.mark.asyncio
async def test_full_demo_theft_scenario(client: AsyncClient, seed_users):
    """
    End-to-end demonstration of the complete theft scenario:
    Case: Shop theft, Rs 80,000 electronics store, 8:35-8:50 PM.
    Validates all 9 canonical milestones from the RRE V2 Architecture.
    """
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # Step 1: Create Case
    case_res = await client.post(
        "/cases",
        json={
            "title": "Grand Electronics Showroom iPhone 15 Pro Theft",
            "case_type": "THEFT",
            "incident_location": "Grand Electronics, Sector 18, Central Mall",
            "incident_time_observed": "2026-01-15T20:45:00Z",
            "incident_time_estimated": {"min": "2026-01-15T20:30:00Z", "max": "2026-01-15T21:00:00Z"}
        },
        headers=headers
    )
    assert case_res.status_code == 201
    case_data = case_res.json()
    case_id = case_data["id"]
    assert case_data["case_number"].startswith("THF-")

    # Step 2: Upload all 7 Evidence items
    evidence_manifest = [
        ("cctv_entrance.mp4", b"SIMULATED_CCTV_ENTRANCE_FRAME_001_500", "video/mp4"),
        ("cctv_aisle.mp4", b"SIMULATED_CCTV_AISLE_DISPLAY_FRAME_001_500", "video/mp4"),
        ("cctv_exit.mp4", b"SIMULATED_CCTV_EXIT_TURNSTILE_FRAME_001_500", "video/mp4"),
        ("witness_statement.txt", b"I saw a person in a black jacket near the electronics shelf around 8:40 PM.", "text/plain"),
        ("inventory_log.csv", b"item,serial,status,delta\niPhone 15 Pro,SN-88219,MISSING,-1\n", "text/csv"),
        ("transactions.csv", b"transaction_id,timestamp,item,amount\nTX-1,2026-01-15T20:35:00Z,Screen Guard,499\n", "text/csv"),
        ("vehicle_sighting.txt", b"Dark SUV seen outside at 8:48 PM, partial plate noted: MH12-AB-9821.", "text/plain"),
        ("crime_scene_shelf.jpg", b"EXIF_CRIME_SCENE_SHELF_IMAGE", "image/jpeg")
    ]

    uploaded_evidence = {}
    for filename, content, mime in evidence_manifest:
        upload_res = await client.post(
            f"/cases/{case_id}/evidence",
            files={"file": (filename, io.BytesIO(content), mime)},
            headers=headers
        )
        assert upload_res.status_code == 201
        ev = upload_res.json()
        uploaded_evidence[filename] = ev["id"]
        assert len(ev["sha256_hash"]) == 64

    # Step 3: Process all evidence through Departmental Engines
    for filename, ev_id in uploaded_evidence.items():
        proc_res = await client.post(f"/cases/{case_id}/evidence/{ev_id}/process", headers=headers)
        assert proc_res.status_code == 200
        assert proc_res.json()["status"] == "COMPLETED"

    # Step 4: Verify Candidate Entity Linkage (Milestone 2)
    auto_link_res = await client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    assert auto_link_res.status_code == 200
    links = auto_link_res.json()
    assert len(links) >= 2

    # Verify link unconfirmed by default, then human investigator confirms
    p1_link = links[0]
    assert p1_link["is_human_confirmed"] is False
    confirm_res = await client.post(
        f"/cases/{case_id}/entities/{p1_link['candidate_entity_id']}/links/{p1_link['id']}/confirm",
        headers=headers
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["is_human_confirmed"] is True

    # Step 5: Timeline Correlation & Source Timelines (Milestone 1 & 3)
    corr_res = await client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)
    assert corr_res.status_code == 200
    corr_events = corr_res.json()
    assert len(corr_events) >= 6

    # Source timelines independently preserved
    src_res = await client.get(f"/cases/{case_id}/timelines/sources", headers=headers)
    assert src_res.status_code == 200
    assert len(src_res.json()) >= 6

    # Step 6: Gap & Conflict Detection (Milestone 7 & 3)
    gaps_res = await client.get(f"/cases/{case_id}/gaps-conflicts", headers=headers)
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    
    # 1 critical corridor blind spot gap
    corridor_gap = next((g for g in gaps if g["gc_type"] == "GAP" and g["significance"] == "CRITICAL"), None)
    assert corridor_gap is not None

    # 1 soft timestamp discrepancy
    soft_disc = next((g for g in gaps if g["gc_type"] == "SOFT_DISCREPANCY"), None)
    assert soft_disc is not None

    # Step 7: Evidence-Constrained Hypothesis Generation & Self-Challenge (Milestones 4, 5, 6)
    hyp_res = await client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201
    hypotheses = hyp_res.json()
    assert len(hypotheses) == 2

    hyp_a = next((h for h in hypotheses if "Hypothesis A" in h["label"]), None)
    hyp_b = next((h for h in hypotheses if "Hypothesis B" in h["label"]), None)

    assert hyp_a is not None and hyp_a["overall_strength"] == "STRONG"
    assert hyp_b is not None and hyp_b["overall_strength"] == "SPECULATIVE"

    # Self-challenge outputs present
    assert len(hyp_a["deterministic_issues"]) >= 1
    assert len(hyp_a["ai_challenge_notes"]) >= 1

    # Human reviews and accepts Hypothesis A
    await client.post(
        f"/cases/{case_id}/hypotheses/{hyp_a['id']}/review",
        json={"status": "ACCEPTED", "review_note": "Corroborated by entrance/exit timing and severed tether evidence."},
        headers=headers
    )

    # Step 8: Copilot Safeguards and Citations (Milestone 8)
    # 8a: Prohibited verdict query must be blocked
    prohibited_res = await client.post(
        f"/cases/{case_id}/copilot/query",
        json={"query": "Who is the thief?"},
        headers=headers
    )
    assert prohibited_res.status_code == 200
    p_data = prohibited_res.json()
    assert p_data["is_prohibited_query"] is True
    assert p_data["mode"] == "SYSTEM_SAFEGUARD"

    # 8b: Evidence Mode query returns citations
    ev_mode_res = await client.post(
        f"/cases/{case_id}/copilot/query",
        json={"query": "What observations were recorded at the entrance and exit?", "mode": "EVIDENCE"},
        headers=headers
    )
    assert ev_mode_res.status_code == 200
    ev_data = ev_mode_res.json()
    assert ev_data["mode"] == "EVIDENCE"
    assert len(ev_data["evidence_references"]) >= 1

    # 8c: Reasoning Mode query returns counter-hypotheses and blind-spot notes
    reason_res = await client.post(
        f"/cases/{case_id}/copilot/query",
        json={"query": "How could the suspect have concealed the phone without being detected on camera?", "mode": "REASONING"},
        headers=headers
    )
    assert reason_res.status_code == 200
    reason_data = reason_res.json()
    assert reason_data["mode"] == "REASONING"
    assert "blind spot" in reason_data["answer"].lower()

    # Step 9: Final Report Generation (Milestone 9)
    report_res = await client.post(f"/cases/{case_id}/reports/generate", headers=headers)
    assert report_res.status_code == 201
    report_data = report_res.json()
    assert report_data["version"] == 1
    r_content = report_data["report_data"]
    assert "chain_of_custody_and_evidence" in r_content
    assert "reconstructed_hypotheses" in r_content
    assert "ai_disclosure_and_judicial_compliance" in r_content
    assert r_content["ai_disclosure_and_judicial_compliance"]["platform"] == "Reality Reconstruction Engine (RRE) v2.0"
