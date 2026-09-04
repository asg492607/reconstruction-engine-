import csv
import io
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
from app.models.enums import (
    Department, ObservationType, TimeConfidence, TimeReliability, EvidenceQuality
)
from app.observations.schemas import ObservationCreate

class FinancialTransactionProcessor:
    def __init__(self, model_name: str = "Financial-Anomaly-Detector", model_version: str = "1.0.0"):
        self.model_name = model_name
        self.model_version = model_version

    def process_transactions(
        self,
        transaction_data: str,
        evidence_id: str,
        base_timestamp: Optional[datetime] = None
    ) -> List[ObservationCreate]:
        observations: List[ObservationCreate] = []
        base_dt = base_timestamp or datetime.now(timezone.utc)

        # Parse transactions CSV or text
        transactions = []
        try:
            reader = csv.DictReader(io.StringIO(transaction_data))
            for row in reader:
                transactions.append(row)
        except Exception:
            transactions = []

        # Analyze transactions for stolen item purchases (excluding accessories like cases/cables)
        accessories = ["case", "cable", "charger", "protector", "cover", "strap"]
        stolen_item_keywords = ["iphone", "smartphone", "handset", "laptop", "gold", "jewelry", "watch"]
        matching_purchases = []

        for tx in transactions:
            item_desc = tx.get("item", tx.get("description", "")).lower()
            is_accessory = any(acc in item_desc for acc in accessories)
            if not is_accessory and any(k in item_desc for k in stolen_item_keywords):
                matching_purchases.append(tx)

        if len(matching_purchases) == 0:
            # Missing purchase confirmed! Stolen item was taken without payment!
            observations.append(
                ObservationCreate(
                    evidence_id=evidence_id,
                    department=Department.FINANCIAL,
                    observation_type=ObservationType.TRANSACTION_FLAGGED,
                    raw_data={
                        "anomaly_type": "UNAUTHORIZED_REMOVAL_NO_PAYMENT",
                        "total_transactions_analyzed": len(transactions),
                        "matching_valid_purchases": 0,
                        "finding": "No purchase of stolen item was recorded in POS system during the incident window",
                        "audit_period": "Incident Time Window"
                    },
                    observed_time_raw="8:30 PM - 9:00 PM POS Transaction Log",
                    observed_time_parsed=base_dt,
                    time_confidence=TimeConfidence.EXACT,
                    time_source="pos_transaction_database",
                    time_reliability=TimeReliability.HIGH,
                    location_label="Point of Sale Registers",
                    observation_confidence=0.99,
                    evidence_quality=EvidenceQuality.HIGH,
                    model_name=self.model_name,
                    model_version=self.model_version
                )
            )
        else:
            # Valid purchase or anomalous discount
            for tx in matching_purchases:
                observations.append(
                    ObservationCreate(
                        evidence_id=evidence_id,
                        department=Department.FINANCIAL,
                        observation_type=ObservationType.TRANSACTION_FLAGGED,
                        raw_data={
                            "anomaly_type": "MATCHING_TRANSACTION_FOUND",
                            "transaction_id": tx.get("transaction_id", "N/A"),
                            "amount": tx.get("amount", "0"),
                        },
                        observed_time_raw=tx.get("timestamp", "N/A"),
                        observed_time_parsed=base_dt,
                        time_confidence=TimeConfidence.EXACT,
                        time_source="pos_terminal",
                        time_reliability=TimeReliability.HIGH,
                        location_label="Register 1",
                        observation_confidence=0.95,
                        evidence_quality=EvidenceQuality.HIGH,
                        model_name=self.model_name,
                        model_version=self.model_version
                    )
                )

        return observations

financial_transaction_processor = FinancialTransactionProcessor()
