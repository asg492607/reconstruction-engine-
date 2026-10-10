import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.ocr.service import process_document_ocr
from app.models.entities import Evidence, Case
from app.models.enums import EvidenceType, Department, ObservationType
from app.department_engines.investigation.service import run_investigation_pipeline

@pytest.mark.asyncio
async def test_deterministic_ocr_extraction():
    receipt_text = b"""
    METRO LUXURY BOUTIQUE
    Store #402 - Terminal 03
    Date: 2026-03-29 02:45 AM
    Cashier Badge: DET-4091

    ITEM #1: ROLEX SUBMARINER OYSTER - $14,500.00
    SKU-88219-RLX
    ITEM #2: DIAMOND PENDANT 18K - $3,200.00
    SKU-11029-JWL

    SUBTOTAL: $17,700.00
    TAX (8.5%): $1,504.50
    TOTAL AMOUNT DUE: $19,204.50
    TRANSACTION STATUS: UNPAID - MANUAL OVERRIDE
    """

    res = await process_document_ocr(
        file_bytes=receipt_text,
        filename="register_receipt.txt",
        mime_type="text/plain"
    )

    assert res["status"] == "SUCCESS"
    assert "RECEIPT" in res["document_type"]
    assert any(a in str(res["monetary_amounts"]) for a in ["19,204.50", "17,700.00", "14,500.00", "19204.50"])
    assert "SKU-88219-RLX" in res["skus_and_serials"]
    assert "TRANSACTION_UNPAID" in res["forensic_flags"]
    assert res["sha256_hash"] is not None

@pytest.mark.asyncio
async def test_investigation_pipeline_with_ocr_metadata(db_session: AsyncSession, seed_users):
    lead = seed_users["lead"]
    test_case = Case(
        case_number="CASE-OCR-TEST-01",
        title="OCR Exhibit Case",
        created_by=lead.id
    )
    db_session.add(test_case)
    await db_session.flush()

    raw_text = "Store register tape found crumpled behind display counter."
    # Create evidence with pre-existing OCR metadata
    ev = Evidence(
        case_id=test_case.id,
        evidence_type=EvidenceType.DOCUMENT,
        original_filename="receipt_exhibit_01.txt",
        storage_key="receipt_key",
        file_size_bytes=len(raw_text.encode("utf-8")),
        uploaded_by=lead.id,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        metadata_json={
            "statement_text": raw_text,
            "ocr_data": {
                "document_type": "RECEIPT",
                "merchant_or_issuer": "Metro Luxury Boutique",
                "total_amount": "$19,204.50",
                "monetary_amounts": ["$19,204.50", "$14,500.00"],
                "skus_and_serials": ["SKU-88219-RLX"],
                "forensic_flags": ["UNPAID_TRANSACTION"],
                "confidence_score": 0.98
            }
        }
    )
    db_session.add(ev)
    await db_session.commit()
    await db_session.refresh(ev)

    observations = await run_investigation_pipeline(db_session, test_case, ev)
    assert len(observations) >= 1
    ocr_obs = next((o for o in observations if o.observation_type == ObservationType.TEXT_EXTRACTED), None)
    assert ocr_obs is not None
    assert ocr_obs.raw_data["total_amount"] == "$19,204.50"
    assert "UNPAID_TRANSACTION" in ocr_obs.raw_data["forensic_flags"]
