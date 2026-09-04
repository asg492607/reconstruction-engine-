import io
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from tests.helpers import get_auth_headers
from app.department_engines.investigation.cctv import cctv_processor
from app.department_engines.investigation.witness import witness_processor
from app.department_engines.investigation.inventory import inventory_processor
from app.department_engines.investigation.vehicle import vehicle_processor
from app.models.enums import ObservationType, TimeConfidence

def test_witness_statement_processor():
    statement = "I saw a person in a black jacket near the electronics shelf around 8:40 PM."
    observations = witness_processor.process_witness_statement(
        statement_text=statement,
        evidence_id="ev_witness_01"
    )
    assert len(observations) >= 1
    person_obs = observations[0]
    assert person_obs.observation_type == ObservationType.ENTITY_EXTRACTED
    assert "black jacket" in person_obs.raw_data["clothing"]
    assert "shelf" in person_obs.raw_data["location_reported"]
    assert person_obs.time_confidence == TimeConfidence.APPROXIMATE
    assert person_obs.observed_time_raw == "8:40 PM"

def test_inventory_processor_delta_detection():
    csv_data = """item,serial,status,delta,last_verified,reported_missing
iPhone 15 Pro,SN-99881,MISSING,-1,2026-01-15T20:30:00Z,2026-01-15T21:00:00Z
AirPods Max,SN-22100,PRESENT,0,2026-01-15T20:30:00Z,2026-01-15T21:00:00Z
"""
    observations = inventory_processor.process_inventory_data(
        content=csv_data,
        evidence_id="ev_inventory_01"
    )
    assert len(observations) == 1
    obs = observations[0]
    assert obs.observation_type == ObservationType.OBJECT_DETECTED
    assert obs.raw_data["item_name"] == "iPhone 15 Pro"
    assert obs.raw_data["status"] == "CONFIRMED_DISAPPEARANCE"
    assert obs.raw_data["delta"] == -1
    assert obs.time_window_min is not None
    assert obs.time_window_max is not None

def test_vehicle_sighting_processor():
    text = "Dark SUV seen outside at 8:48 PM, partial plate noted: MH12-AB-9821."
    observations = vehicle_processor.process_vehicle_record(
        record_text=text,
        evidence_id="ev_vehicle_01"
    )
    assert len(observations) == 1
    obs = observations[0]
    assert obs.observation_type == ObservationType.VEHICLE_DETECTED
    assert obs.raw_data["vehicle_type"] == "SUV"
    assert "MH12-AB-9821" in obs.raw_data["license_plate"]

@pytest.mark.asyncio
async def test_end_to_end_evidence_processing_and_observations(client: AsyncClient, seed_users):
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # 1. Create case
    case_res = await client.post(
        "/cases",
        json={"title": "Store Burglary", "case_type": "THEFT", "incident_time_observed": "2026-01-15T20:40:00Z"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # 2. Upload entrance CCTV evidence
    cctv_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("cctv_entrance.mp4", io.BytesIO(b"CCTV_VIDEO_STREAM_BYTES"), "video/mp4")},
        headers=headers
    )
    cctv_id = cctv_upload.json()["id"]

    # 3. Process CCTV evidence through Investigation Engine
    process_res = await client.post(
        f"/cases/{case_id}/evidence/{cctv_id}/process",
        headers=headers
    )
    assert process_res.status_code == 200
    p_data = process_res.json()
    assert p_data["status"] == "COMPLETED"
    assert p_data["observations_generated"] >= 2

    # 4. Upload and process witness statement
    witness_text = "I saw a person in a black jacket near the electronics shelf around 8:40 PM."
    witness_upload = await client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("witness_statement.txt", io.BytesIO(witness_text.encode("utf-8")), "text/plain")},
        headers=headers
    )
    witness_id = witness_upload.json()["id"]

    w_proc_res = await client.post(
        f"/cases/{case_id}/evidence/{witness_id}/process",
        headers=headers
    )
    assert w_proc_res.status_code == 200
    assert w_proc_res.json()["observations_generated"] >= 1

    # 5. List observations for case
    obs_res = await client.get(f"/cases/{case_id}/observations", headers=headers)
    assert obs_res.status_code == 200
    observations = obs_res.json()
    assert len(observations) >= 3

    # 6. Filter observations by department and type
    inv_obs = await client.get(
        f"/cases/{case_id}/observations?department=INVESTIGATION&observation_type=PERSON_DETECTED",
        headers=headers
    )
    assert inv_obs.status_code == 200
    person_detections = inv_obs.json()
    assert len(person_detections) >= 1
    assert person_detections[0]["observation_type"] == "PERSON_DETECTED"
