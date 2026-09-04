import os
import sys
import json
import httpx
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_evidence_assets")

def run_real_evidence_e2e():
    print("\n========================================================")
    print("  REAL EVIDENCE END-TO-END VERIFICATION SUITE")
    print("========================================================\n")

    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    # 1. Health check
    print("[STEP 1] Verifying server health...")
    health_res = client.get("/health")
    assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
    print(f"  --> Server Healthy: {health_res.json()}")

    # 2. Register real investigator
    from datetime import timezone
    ts = int(datetime.now(timezone.utc).timestamp())
    email = f"lead.investigator_{ts}@police.gov"
    password = "SecurePassword2026!"
    print(f"\n[STEP 2] Registering real investigator: {email}...")
    reg_res = client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Lead Detective Sarah Chen",
            "password": password,
            "department": "INVESTIGATION",
            "role": "LEAD_INVESTIGATOR"
        }
    )
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    print(f"  --> Investigator registered: ID {reg_res.json()['id']}")

    # 3. Authenticate
    print("\n[STEP 3] Authenticating investigator...")
    login_res = client.post(
        "/auth/login/json",
        json={"email": email, "password": password}
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  --> JWT Bearer token acquired.")

    # 4. Create real case
    print("\n[STEP 4] Opening genuine investigation case...")
    case_payload = {
        "title": "Larceny Investigation: Diamond Chronograph Luxury Watch",
        "description": "Reported theft of high-value timepiece SKU-99214 from display pedestal with severed security tether.",
        "case_type": "THEFT",
        "incident_time_observed": "2026-03-01T19:44:00Z"
    }
    case_res = client.post("/cases", json=case_payload, headers=headers)
    assert case_res.status_code == 201, f"Case creation failed: {case_res.text}"
    case_data = case_res.json()
    case_id = case_data["id"]
    case_num = case_data["case_number"]
    print(f"  --> Case opened: {case_num} (UUID: {case_id})")

    # 5. Upload real multimedia evidence
    evidence_files = [
        ("cctv_entrance_real.mp4", "video/mp4", "INVESTIGATION", "Entry surveillance capture"),
        ("cctv_aisle_real.mp4", "video/mp4", "INVESTIGATION", "Aisle display pedestal camera"),
        ("cctv_exit_real.mp4", "video/mp4", "INVESTIGATION", "Exit turnstile surveillance"),
        ("scene_shelf_severed_tether.jpg", "image/jpeg", "FORENSIC", "Crime scene photography showing cut cable"),
        ("forensic_fingerprint_card.png", "image/png", "FORENSIC", "Latent fingerprint card lifted from display glass"),
        ("forensic_toolmark_report.txt", "text/plain", "FORENSIC", "Forensic toolmark microscopy examination report"),
        ("witness_associate_statement.txt", "text/plain", "INVESTIGATION", "Firsthand interview statement from floor associate"),
        ("inventory_records.csv", "text/csv", "INVESTIGATION", "Physical inventory count delta audit"),
        ("pos_transactions_audit.csv", "text/csv", "FINANCIAL", "Register audit transactions between 19:30 and 19:55 UTC"),
    ]

    print(f"\n[STEP 5] Uploading & dispatching {len(evidence_files)} real evidence files...")
    uploaded_evidence = []
    for fn, mime, dept, desc in evidence_files:
        path = os.path.join(ASSETS_DIR, fn)
        assert os.path.exists(path), f"Evidence file missing: {path}"
        file_size = os.path.getsize(path)

        with open(path, "rb") as f:
            up_res = client.post(
                f"/cases/{case_id}/evidence",
                files={"file": (fn, f, mime)},
                headers=headers
            )
        assert up_res.status_code == 201, f"Upload failed for {fn}: {up_res.text}"
        ev_info = up_res.json()
        ev_id = ev_info["id"]
        sha256 = ev_info["sha256_hash"]
        depts = ev_info.get("authorized_departments", [])
        ev_type = ev_info.get("evidence_type", "UNKNOWN")
        print(f"  --> Stored {fn} ({file_size} bytes) | SHA256: {sha256[:16]}... | Type: {ev_type} | Routed to: {depts}")

        # Process through departmental pipeline
        proc_res = client.post(f"/cases/{case_id}/evidence/{ev_id}/process", headers=headers)
        assert proc_res.status_code == 200, f"Processing failed for {fn}: {proc_res.text}"
        observations = proc_res.json()
        print(f"      Extracted {len(observations)} AI-generated observations (0 human-verified pending review)")
        uploaded_evidence.append((ev_id, fn, len(observations)))

    # 6. Verify observations catalog
    print("\n[STEP 6] Inspecting extracted observations...")
    obs_res = client.get(f"/cases/{case_id}/observations", headers=headers)
    assert obs_res.status_code == 200
    all_obs = obs_res.json()
    verified_count = sum(1 for o in all_obs if o.get("verification_status") == "ACCEPTED")
    print(f"  --> Total case observations: {len(all_obs)} AI-generated ({verified_count} human-verified)")
    assert len(all_obs) >= 8, f"Expected at least 8 observations, got {len(all_obs)}"
    for o in all_obs[:4]:
        print(f"      • [{o['department']}] {o['observation_type']} at {o['location_label']} (Status: {o.get('verification_status')})")

    # 7. Candidate Entity Resolution & Auto-linking
    print("\n[STEP 7] Performing cross-department entity resolution & linking...")
    link_res = client.post(f"/cases/{case_id}/entities/auto-link", headers=headers)
    assert link_res.status_code == 200, f"Auto-link failed: {link_res.text}"
    entities_res = client.get(f"/cases/{case_id}/entities", headers=headers)
    assert entities_res.status_code == 200
    entities = entities_res.json()
    print(f"  --> Candidate Entities Discovered: {len(entities)}")
    for e in entities:
        print(f"      • {e['label']} ({e['entity_type']}) - Status: {e.get('identity_status')}")

    # 8. Unified Temporal Correlation
    print("\n[STEP 8] Correlating multi-source temporal timelines...")
    corr_res = client.post(f"/cases/{case_id}/timelines/correlate", headers=headers)
    assert corr_res.status_code == 200, f"Correlation failed: {corr_res.text}"
    timeline_events = corr_res.json()
    print(f"  --> Unified Chronological Events: {len(timeline_events)}")
    for ev in timeline_events[:5]:
        print(f"      [{ev.get('event_time')}] [{ev.get('department')}] {ev.get('description', '')[:60]}...")

    # 9. Gap and Conflict Detection
    print("\n[STEP 9] Evaluating surveillance coverage gaps and physical discrepancies...")
    detect_res = client.post(f"/cases/{case_id}/gaps-conflicts/detect", headers=headers)
    assert detect_res.status_code == 200
    gaps_res = client.get(f"/cases/{case_id}/gaps-conflicts", headers=headers)
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    print(f"  --> Gaps & Discrepancies Flagged: {len(gaps)}")
    for g in gaps:
        print(f"      • [{g['gc_type']}] ({g['significance']}): {g['description']}")

    # 10. Evidence-Constrained Reality Reconstruction (Hypotheses)
    print("\n[STEP 10] Generating evidence-grounded theft hypotheses with Granular Per-Step Support...")
    hyp_res = client.post(f"/cases/{case_id}/hypotheses/generate", headers=headers)
    assert hyp_res.status_code == 201, f"Hypothesis generation failed: {hyp_res.text}"
    hypotheses = hyp_res.json()
    print(f"  --> Generated Hypotheses: {len(hypotheses)}")
    assert len(hypotheses) >= 1, "Expected at least one hypothesis"

    for h in hypotheses:
        print(f"\n      === {h['label']} (Overall Strength: {h['overall_strength']}) ===")
        print(f"      Description: {h['description']}")
        print(f"      Per-Step Evidence Support Matrix:")
        for step in h['sequence']:
            s_lvl = step.get('support_level', 'UNSTATED')
            is_dir = "Direct Observation" if step.get('is_directly_observed') else "Inferred Step"
            print(f"        Step {step['step']} [{step['phase']} @ {step['time']}]:")
            print(f"          • Description: {step['description']}")
            print(f"          • Support Level: {s_lvl} ({is_dir})")
            print(f"          • Rationale: {step.get('support_rationale')}")
            print(f"          • Sources: {step.get('evidence_sources')}")

        # Check Self-Challenge Results
        print(f"      Deterministic Issues Flagged (Layer 1): {len(h.get('deterministic_issues', []))}")
        for iss in h.get('deterministic_issues', []):
            print(f"        - {iss.get('check')}: {iss.get('detail')}")
        print(f"      AI Adversarial Review Points (Layer 2): {len(h.get('ai_challenge_notes', []))}")
        for note in h.get('ai_challenge_notes', []):
            print(f"        - [{note.get('dimension')}]: {note.get('challenge')}")

    # Verify no mock filenames in hypothesis sources
    hyp_a = hypotheses[0]
    all_sources = []
    for step in hyp_a["sequence"]:
        all_sources.extend(step.get("evidence_sources", []))

    # Assert that actual uploaded filenames are present
    assert any("cctv_entrance_real.mp4" in s for s in all_sources), "cctv_entrance_real.mp4 missing from hypothesis"
    assert any("scene_shelf_severed_tether.jpg" in s or "cctv_aisle_real.mp4" in s for s in all_sources), "Scene evidence missing from hypothesis"
    assert any("cctv_exit_real.mp4" in s for s in all_sources), "cctv_exit_real.mp4 missing from hypothesis"

    # 11. Human Investigator Review of Primary Hypothesis
    print("\n[STEP 11] Executing Lead Investigator Review...")
    rev_res = client.post(
        f"/cases/{case_id}/hypotheses/{hyp_a['id']}/review",
        json={
            "status": "ACCEPTED",
            "review_note": "Corroborated by physical toolmark examination, inventory delta, and timeline correlation of CCTV entrance and exit timestamps."
        },
        headers=headers
    )
    assert rev_res.status_code == 200, f"Review failed: {rev_res.text}"
    print(f"  --> Hypothesis Status: {rev_res.json()['status']} by Lead Investigator")

    # 11b. End-to-End Provenance Traceability Check
    print("\n[STEP 11b] Tracing End-to-End Provenance Chain (Hypothesis -> Observation -> Evidence -> SHA256 -> Model)...")
    prov_res = client.get(f"/cases/{case_id}/hypotheses/{hyp_a['id']}/provenance-chain", headers=headers)
    assert prov_res.status_code == 200, f"Provenance chain query failed: {prov_res.text}"
    p_chain = prov_res.json()
    print(f"  --> Provenance Chain Retrieved for: {p_chain['label']}")
    for step_p in p_chain.get("provenance_chain", [])[:2]:
        print(f"      Step {step_p['step']} ({step_p['phase']}) - Support: {step_p['support_level']}")
        for obs_p in step_p.get("observations", [])[:1]:
            ev_p = obs_p.get("evidence") or {}
            print(f"        |-- Obs: [{obs_p['department']}] {obs_p['type']} (Model: {obs_p['model_name']} v{obs_p['model_version']})")
            print(f"            |-- Source Evidence: {ev_p.get('filename')} | SHA256: {str(ev_p.get('sha256_hash'))[:16]}... | Verified: {obs_p['verification_status']}")

    # 12. Investigation Copilot Query with Strict Safeguards
    print("\n[STEP 12] Testing AI Copilot with Safeguards & Citations...")
    # 12a. Prohibited verdict query
    prohibited_res = client.post(
        f"/cases/{case_id}/copilot/query",
        json={"query": "Who is guilty of stealing the watch?"},
        headers=headers
    )
    assert prohibited_res.status_code == 200
    p_data = prohibited_res.json()
    assert p_data["is_prohibited_query"] is True, "Prohibited query was not blocked by safeguard!"
    print(f"  --> Safeguard successfully blocked prohibited query: '{p_data['answer'][:80]}...'")

    # 12b. Legitimate timeline query
    legit_res = client.post(
        f"/cases/{case_id}/copilot/query",
        json={"query": "What observations support the timing of the property detachment?"},
        headers=headers
    )
    assert legit_res.status_code == 200
    l_data = legit_res.json()
    print(f"  --> Copilot Answer: {l_data['answer'][:120]}...")
    print(f"  --> Citations provided: {len(l_data.get('citations', []))}")

    # 13. Reconstruction Report Generation
    print("\n[STEP 13] Exporting Official Reconstruction Report...")
    gen_res = client.post(f"/cases/{case_id}/reports/generate", headers=headers)
    assert gen_res.status_code == 201, f"Report generation failed: {gen_res.text}"
    report_meta = gen_res.json()
    report_id = report_meta["id"]

    rep_res = client.get(f"/cases/{case_id}/reports/{report_id}", headers=headers)
    assert rep_res.status_code == 200, f"Report retrieval failed: {rep_res.text}"
    report_data = rep_res.json()
    rd = report_data.get("report_data", {})
    print(f"  --> Report Generated: {report_id} (Version {report_data.get('version')})")
    print(f"      Case: {rd.get('case_number')}")
    print(f"      Accepted Hypothesis: {rd.get('accepted_hypothesis', {}).get('label')}")
    print(f"      Deterministic Issues: {len(rd.get('accepted_hypothesis', {}).get('deterministic_issues', []))}")
    print(f"      Adversarial Challenges: {len(rd.get('accepted_hypothesis', {}).get('ai_challenge_notes', []))}")

    print("\n===========================================================================")
    print("  ALL 13 AUTOMATED END-TO-END CHECKS PASSED ON GENERATED THEFT DATASET!   ")
    print("===========================================================================\n")

if __name__ == "__main__":
    try:
        run_real_evidence_e2e()
    except Exception as err:
        print(f"\n[FAILED] Verification failed with error: {err}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
