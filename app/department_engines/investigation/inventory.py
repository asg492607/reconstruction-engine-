import csv
import io
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
from app.models.enums import (
    Department, ObservationType, TimeConfidence, TimeReliability, EvidenceQuality
)
from app.observations.schemas import ObservationCreate

class InventoryProcessor:
    def __init__(self, model_name: str = "Inventory-Delta-Analyzer", model_version: str = "1.0.0"):
        self.model_name = model_name
        self.model_version = model_version

    def process_inventory_data(
        self,
        content: str,
        evidence_id: str,
        base_timestamp: Optional[datetime] = None
    ) -> List[ObservationCreate]:
        observations: List[ObservationCreate] = []
        base_dt = base_timestamp or datetime.now(timezone.utc)

        # Attempt to parse as CSV or text lines
        rows = []
        try:
            reader = csv.DictReader(io.StringIO(content))
            for r in reader:
                rows.append(r)
        except Exception:
            rows = []

        if rows:
            for row in rows:
                # Look for delta or missing indicators
                status = row.get("status", "").upper()
                delta = row.get("delta", "")
                item_name = row.get("item", row.get("item_name", "Unknown Item"))
                serial = row.get("serial", row.get("unit_id", "N/A"))

                is_adj = any(k in str(row).lower() for k in ["authorized", "adjustment", "transfer", "write-off", "write_off", "rma", "damaged"])
                if is_adj:
                    observations.append(
                        ObservationCreate(
                            evidence_id=evidence_id,
                            department=Department.INVESTIGATION,
                            observation_type=ObservationType.OBJECT_DETECTED,
                            raw_data={
                                "item_name": item_name,
                                "anomaly_type": "AUTHORIZED_STOCK_ADJUSTMENT_RECORDED",
                                "status": "AUTHORIZED_STOCK_ADJUSTMENT",
                                "reason": row.get("reason", "Authorized adjustment / transfer"),
                                "delta": 0
                            },
                            observed_time_raw=row.get("timestamp", "Inventory Log"),
                            observed_time_parsed=base_dt,
                            time_confidence=TimeConfidence.EXACT,
                            time_source="inventory_adjustment_log",
                            time_reliability=TimeReliability.HIGH,
                            location_label="Inventory Management",
                            observation_confidence=0.99,
                            evidence_quality=EvidenceQuality.HIGH,
                            model_name=self.model_name,
                            model_version=self.model_version
                        )
                    )

                is_missing = "MISSING" in status or delta.startswith("-") or row.get("count", "") == "0"
                if is_missing and not is_adj:
                    # Parse times if present
                    last_seen_str = row.get("last_verified", row.get("time_in", None))
                    missing_str = row.get("reported_missing", row.get("time_out", None))

                    t_min = date_parser.parse(last_seen_str) if last_seen_str else base_dt
                    t_max = date_parser.parse(missing_str) if missing_str else base_dt

                    observations.append(
                        ObservationCreate(
                            evidence_id=evidence_id,
                            department=Department.INVESTIGATION,
                            observation_type=ObservationType.OBJECT_DETECTED,
                            raw_data={
                                "item_name": item_name,
                                "serial_number": serial,
                                "status": "CONFIRMED_DISAPPEARANCE",
                                "expected_quantity": 1,
                                "actual_quantity": 0,
                                "delta": -1,
                                "last_seen": last_seen_str or t_min.isoformat(),
                                "first_reported_missing": missing_str or t_max.isoformat(),
                            },
                            observed_time_raw=f"Missing between {last_seen_str or 'start'} and {missing_str or 'end'}",
                            observed_time_parsed=t_max,
                            time_confidence=TimeConfidence.ESTIMATED,
                            time_source="inventory_audit_log",
                            time_reliability=TimeReliability.HIGH,
                            time_window_min=t_min,
                            time_window_max=t_max,
                            location_label="Display Shelf / Inventory Stock",
                            observation_confidence=0.98,
                            evidence_quality=EvidenceQuality.HIGH,
                            model_name=self.model_name,
                            model_version=self.model_version
                        )
                    )
        else:
            # Fallback plain-text parsing
            lower_content = content.lower()
            if "missing" in lower_content or "discrepancy" in lower_content or "theft" in lower_content:
                # Extract first prominent keyword or default
                extracted_item = "Discrepant Inventory Item"
                for kw in ["iphone 15 pro", "iphone", "smartphone", "laptop", "watch", "tablet", "jewelry"]:
                    if kw in lower_content:
                        extracted_item = kw.title()
                        break

                observations.append(
                    ObservationCreate(
                        evidence_id=evidence_id,
                        department=Department.INVESTIGATION,
                        observation_type=ObservationType.OBJECT_DETECTED,
                        raw_data={
                            "item_name": extracted_item,
                            "status": "CONFIRMED_DISAPPEARANCE",
                            "delta": -1,
                            "audit_note": content.strip()[:300]
                        },
                        observed_time_raw=base_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        observed_time_parsed=base_dt,
                        time_confidence=TimeConfidence.ESTIMATED,
                        time_source="inventory_audit",
                        time_reliability=TimeReliability.HIGH,
                        time_window_min=base_dt,
                        time_window_max=base_dt,
                        location_label="Display Case / Stock Area",
                        observation_confidence=0.90,
                        evidence_quality=EvidenceQuality.HIGH,
                        model_name=self.model_name,
                        model_version=self.model_version
                    )
                )

        return observations

inventory_processor = InventoryProcessor()
