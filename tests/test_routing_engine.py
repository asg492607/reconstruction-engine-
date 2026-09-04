import pytest
from app.routing_engine.rules import determine_authorized_departments
from app.models.enums import EvidenceType

def test_routing_engine_matrix():
    # CCTV routes to Investigation (required) + Forensic (optional)
    cctv_depts = determine_authorized_departments(EvidenceType.CCTV)
    assert "INVESTIGATION" in cctv_depts
    assert "FORENSIC" in cctv_depts
    assert "FINANCIAL" not in cctv_depts

    # IMAGE routes to Forensic (primary) + Investigation
    img_depts = determine_authorized_departments(EvidenceType.IMAGE)
    assert "FORENSIC" in img_depts
    assert "INVESTIGATION" in img_depts
    assert "FINANCIAL" not in img_depts

    # WITNESS_STATEMENT routes to Investigation only
    witness_depts = determine_authorized_departments(EvidenceType.WITNESS_STATEMENT)
    assert witness_depts == ["INVESTIGATION"]

    # TRANSACTION_RECORD routes to Financial (primary) + Investigation
    tx_depts = determine_authorized_departments(EvidenceType.TRANSACTION_RECORD)
    assert "FINANCIAL" in tx_depts
    assert "INVESTIGATION" in tx_depts
    assert "FORENSIC" not in tx_depts

    # INVENTORY_RECORD routes to Investigation + Financial
    inv_depts = determine_authorized_departments(EvidenceType.INVENTORY_RECORD)
    assert "INVESTIGATION" in inv_depts
    assert "FINANCIAL" in inv_depts
    assert "FORENSIC" not in inv_depts
