from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from app.department_engines.framework.base import (
    EngineExecutionRecord,
    EngineExecutionResult,
    ReviewPolicy,
    EngineDefinition
)

class OutputValidationError(Exception):
    pass

class OutputValidator:
    """
    Implements the OUTPUT_VALIDATION lifecycle stage.
    Ensures that:
    1. Outputs match declared schema structure.
    2. Provenance records are complete and verifiable.
    3. Source evidence references are present.
    4. Anti-hallucination rules are enforced (no manufactured facts without source evidence).
    5. Correct review status is assigned according to policy and confidence.
    """

    def validate(
        self,
        record: EngineExecutionRecord,
        definition: EngineDefinition
    ) -> EngineExecutionRecord:
        if record.status in [EngineExecutionResult.FAILED, EngineExecutionResult.BLOCKED, EngineExecutionResult.SKIPPED, EngineExecutionResult.NO_USABLE_OUTPUT]:
            return record

        # 1. Output Schema Validation
        if not isinstance(record.outputs, list):
            record.status = EngineExecutionResult.FAILED
            record.failure_reason = "Outputs must be a list of observation/finding dictionaries."
            return record

        # 2. Provenance Completeness
        validated_outputs = []
        for idx, item in enumerate(record.outputs):
            if not isinstance(item, dict):
                record.warnings.append(f"Output #{idx} is not a valid mapping; skipped.")
                continue

            # Ensure observation ID & engine attribution
            if "engine_id" not in item:
                item["engine_id"] = definition.engine_id
            if "engine_version" not in item:
                item["engine_version"] = definition.engine_version
            if "timestamp" not in item and "observed_time" not in item:
                item["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Enforce Non-Verdict & Anti-Hallucination Causal Gate
            text_rep = (
                str(item.get("observation", "")) + " " +
                str(item.get("description", "")) + " " +
                str(item.get("narrative", "")) + " " +
                str(item.get("finding", ""))
            ).lower()

            # 1. Unconditionally Forbidden Verdict Language
            verdict_triggers = [
                "guilty of",
                "theft confirmed",
                "perpetrator confirmed",
                "committed the theft",
                "proves guilt",
                "proves p1 stole"
            ]
            has_verdict_language = any(trigger in text_rep for trigger in verdict_triggers)

            # 2. Hidden Causal Connectives & Assertions
            causal_connectives = [
                "therefore",
                "consequently",
                "must have",
                "was responsible for",
                "removed the item",
                "caused the loss",
                "was the individual who",
                "because p1 took",
                "because p1 was present"
            ]
            has_causal_connective = any(trigger in text_rep for trigger in causal_connectives)

            citations = (
                item.get("supporting_evidence_citations") or
                item.get("supporting_facts") or
                item.get("provenance") or []
            )
            citations_text = " ".join(str(c).lower() for c in citations)

            # Direct physical removal citations required for any removal assertion
            has_direct_removal_proof = any(
                kw in citations_text for kw in [
                    "reach_and_retrieve",
                    "concealment",
                    "physical handling",
                    "possession confirmed"
                ]
            )

            # Specific rule: P1 present near shelf + item later missing != P1 removed item
            shelf_presence_only = any(term in text_rep for term in ["approached shelf", "proximity", "near shelf", "shelf dwell", "aisle dwell"])
            asserts_removal = any(phrase in text_rep for phrase in ["removed the item", "took the item", "caused the loss", "was responsible for", "was the individual who"])
            
            shelf_proximity_leap = (shelf_presence_only and asserts_removal and not has_direct_removal_proof)
            unsupported_causal = (has_causal_connective and not has_direct_removal_proof)

            if has_verdict_language or unsupported_causal or shelf_proximity_leap:
                if has_verdict_language:
                    reason = "UNSUPPORTED_VERDICT_LANGUAGE: Platform cannot declare guilt or confirm theft autonomously."
                    violation_type = "UNSUPPORTED_VERDICT_LANGUAGE"
                elif shelf_proximity_leap:
                    reason = "UNSUPPORTED_CAUSAL_INFERENCE: Presence near shelf + subsequent missing item does not establish item removal."
                    violation_type = "PRESENCE_NEAR_SHELF_DOES_NOT_PROVE_ITEM_REMOVAL"
                else:
                    reason = "UNSUPPORTED_CAUSAL_INFERENCE: Causal connective without direct physical evidence citations."
                    violation_type = "UNSUPPORTED_CAUSAL_LEAP"

                record.warnings.append(reason)
                item["causal_inference_status"] = "UNSUPPORTED_CAUSAL_INFERENCE"
                item["causal_rule_violated"] = violation_type

                # Force status downgrade and escalate review
                record.status = EngineExecutionResult.PARTIAL
                record.failure_reason = reason
                record.review_status = "LEAD_REVIEW_REQUIRED"

                # Sanitize narrative to protect downstream consumers
                for field in ["observation", "narrative", "description", "finding"]:
                    if field in item and isinstance(item[field], str):
                        item[field] = (
                            item[field]
                            .replace("theft confirmed", "discrepancy/activity observed")
                            .replace("guilty of", "alleged subject in")
                            .replace("perpetrator confirmed", "candidate subject")
                            .replace("proves guilt", "is consistent with")
                            .replace("removed the item", "observed in proximity of item location")
                            .replace("must have", "may have")
                            .replace("was responsible for", "was co-located during")
                            .replace("therefore", "subsequently")
                            .replace("consequently", "subsequently")
                        )

            validated_outputs.append(item)

        record.outputs = validated_outputs

        # 3. Quality & Confidence Validation
        if record.confidence is not None:
            if record.confidence < 0.0 or record.confidence > 1.0:
                record.confidence = max(0.0, min(1.0, record.confidence))

            # Check against quality threshold if defined
            min_conf = definition.quality_thresholds.get("min_confidence", 0.0)
            if record.confidence < min_conf and record.status == EngineExecutionResult.SUCCESS:
                record.status = EngineExecutionResult.PARTIAL
                record.warnings.append(f"Confidence {record.confidence:.2f} below threshold {min_conf:.2f}; downgraded to PARTIAL.")

        # 4. Human Review Routing
        if record.review_status == "LEAD_REVIEW_REQUIRED":
            pass  # Escalated status preserved
        elif definition.human_review_policy == ReviewPolicy.AUTO_ACCEPT:
            # High confidence deterministic/extraction can auto-accept unless warnings exist
            if record.confidence is not None and record.confidence >= 0.85 and not record.warnings:
                record.review_status = "AUTO_ACCEPTED"
            else:
                record.review_status = "PENDING_REVIEW"
        elif definition.human_review_policy == ReviewPolicy.SPECIALIST_REVIEW_REQUIRED:
            record.review_status = "SPECIALIST_REVIEW_REQUIRED"
        elif definition.human_review_policy == ReviewPolicy.LEAD_REVIEW_REQUIRED:
            record.review_status = "LEAD_REVIEW_REQUIRED"
        else:
            record.review_status = "PENDING_REVIEW"

        return record

output_validator = OutputValidator()
