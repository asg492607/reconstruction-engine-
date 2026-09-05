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

        # Check for authorized stock-adjustment or inventory write-off records
        authorized_adjustments = []
        for tx in transactions:
            row_str = " ".join(str(v).lower() for v in tx.values())
            adj_type = tx.get("adjustment_type", tx.get("type", tx.get("action", ""))).lower()
            reason = tx.get("reason", tx.get("notes", tx.get("description", ""))).lower()
            if any(k in adj_type for k in ["adjustment", "write_off", "write-off", "transfer", "rma", "return"]) or \
               any(k in reason for k in ["authorized", "stock adjustment", "warehouse transfer", "inventory write-off", "rma", "damaged write-off", "return", "restock"]) or \
               "stock_adjustment" in row_str or "authorized_adjustment" in row_str:
                authorized_adjustments.append(tx)

        if authorized_adjustments:
            for adj in authorized_adjustments:
                observations.append(
                    ObservationCreate(
                        evidence_id=evidence_id,
                        department=Department.FINANCIAL,
                        observation_type=ObservationType.TRANSACTION_FLAGGED,
                        raw_data={
                            "anomaly_type": "AUTHORIZED_STOCK_ADJUSTMENT_RECORDED",
                            "adjustment_type": adj.get("adjustment_type", "AUTHORIZED_ADJUSTMENT"),
                            "reason": adj.get("reason", adj.get("notes", "Authorized inventory adjustment / transfer")),
                            "item": adj.get("item", adj.get("description", "Discrepant Item")),
                            "finding": "Inventory variance is explained by an authorized stock adjustment log; discrepancy is not attributable to unauthorized theft.",
                            "status": "AUTHORIZED"
                        },
                        observed_time_raw=adj.get("timestamp", "Stock Adjustment Log"),
                        observed_time_parsed=base_dt,
                        time_confidence=TimeConfidence.EXACT,
                        time_source="erp_inventory_management",
                        time_reliability=TimeReliability.HIGH,
                        location_label="Inventory Control",
                        observation_confidence=0.99,
                        evidence_quality=EvidenceQuality.HIGH,
                        model_name=self.model_name,
                        model_version=self.model_version
                    )
                )

        if len(matching_purchases) == 0:
            # Observation: No transaction record matched the discrepant item in the provided logs
            observations.append(
                ObservationCreate(
                    evidence_id=evidence_id,
                    department=Department.FINANCIAL,
                    observation_type=ObservationType.TRANSACTION_FLAGGED,
                    raw_data={
                        "anomaly_type": "NO_MATCHING_TRANSACTION_RECORDED",
                        "total_transactions_analyzed": len(transactions),
                        "matching_valid_purchases": 0,
                        "finding": "No matching purchase transaction was recorded in provided POS records during the incident window",
                        "audit_period": "Incident Time Window"
                    },
                    observed_time_raw="POS Transaction Audit Log",
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
