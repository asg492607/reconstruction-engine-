from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.department_engines.framework.registry import engine_registry

class EnginePlanItem(BaseModel):
    engine_id: str
    engine_name: str
    department: Optional[str] = None
    level: str
    status: str # "REQUIRED", "OPTIONAL", "UNAVAILABLE", "BLOCKED"
    reason: str
    dependencies: List[str] = []

class DynamicAnalysisPlan(BaseModel):
    case_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    required_engines: List[str] = []
    optional_engines: List[str] = []
    unavailable_engines: List[Dict[str, str]] = []
    execution_order: List[str] = [] # Topologically sorted DAG execution sequence
    all_items: List[EnginePlanItem] = []

class DynamicAnalysisPlanner:
    """
    Implements Stage 6: Dynamic Analysis Planning.
    Constructs a capability plan tailored to the case exhibits, quality, and context,
    rather than forcing hard-coded crime-specific stories.
    """

    def generate_plan(
        self,
        case_id: str,
        evidence_list: List[Any],
        specific_offense: Optional[str] = None,
        investigative_objectives: Optional[List[str]] = None
    ) -> DynamicAnalysisPlan:
        # 1. Analyze evidence manifest
        evidence_types = set()
        for ev in evidence_list:
            ev_type = getattr(ev, "evidence_type", None)
            if ev_type:
                evidence_types.add(str(ev_type.value if hasattr(ev_type, "value") else ev_type))

        has_video = bool(evidence_types.intersection({"CCTV", "VIDEO", "MP4", "MOV"}))
        has_image = bool(evidence_types.intersection({"IMAGE", "JPEG", "PNG", "JPG", "FORENSIC_REPORT"}))
        has_audio = bool(evidence_types.intersection({"AUDIO", "WAV", "MP3"}))
        has_inventory = bool(evidence_types.intersection({"INVENTORY_RECORD", "INVENTORY", "CSV"}))
        has_pos = bool(evidence_types.intersection({"TRANSACTION_RECORD", "POS"}))
        has_witness = bool(evidence_types.intersection({"WITNESS_STATEMENT", "DOCUMENT"}))
        has_vehicle_rec = bool(evidence_types.intersection({"VEHICLE_RECORD"}))

        required: List[str] = []
        optional: List[str] = []
        unavailable: List[Dict[str, str]] = []
        all_items: List[EnginePlanItem] = []

        # Video engine sets
        video_required = {"I01", "I02", "I03", "I04", "I06", "I08", "I12"}
        video_optional = {"I05", "I07", "I09", "I10"}
        if has_vehicle_rec or (specific_offense and "VEHICLE" in specific_offense):
            video_required.add("I05")

        # Forensic image engine sets
        image_required = {"F01", "F02", "F03", "F04", "F05"}
        image_optional = {"F06", "F07"}

        # Audio engine sets
        audio_engines = {"F08", "F09"}

        # Financial engine sets
        inventory_required = {"FI01", "FI02", "FI03"}
        pos_required = {"FI04", "FI05", "FI06"}
        financial_discrepancy = {"FI07"}

        # 2. Evaluate all registered engines
        all_defs = engine_registry.list_all()
        for ed in all_defs:
            eid = ed.engine_id
            level = ed.engine_level.value
            dept = ed.department
            deps = ed.dependencies

            # Level A: Evidence Foundation (E01–E07)
            if level == "EVIDENCE" or eid.startswith("E0"):
                if evidence_list:
                    status = "REQUIRED"
                    reason = "Foundational evidence preservation, integrity, and relationship mapping"
                    required.append(eid)
                else:
                    status = "UNAVAILABLE"
                    reason = "No evidence exhibits uploaded to case"
                    unavailable.append({"engine_id": eid, "reason": reason})

            # Level B: Investigation AI (I01–I12)
            elif eid.startswith("I"):
                if eid in video_required:
                    if has_video:
                        status = "REQUIRED"
                        reason = "Active CCTV / video exhibit requires video analytics"
                        required.append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "No CCTV or video exhibit attached to case"
                        unavailable.append({"engine_id": eid, "reason": reason})
                elif eid in video_optional:
                    if has_video:
                        status = "OPTIONAL"
                        reason = "Secondary / specialized video analytics pipeline"
                        optional.append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "No CCTV or video exhibit attached to case"
                        unavailable.append({"engine_id": eid, "reason": reason})
                elif eid == "I11":
                    if has_witness:
                        status = "REQUIRED"
                        reason = "Witness statement attached for statement intelligence"
                        required.append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "No witness statements or interview transcripts attached"
                        unavailable.append({"engine_id": eid, "reason": reason})
                else:
                    status = "OPTIONAL" if evidence_list else "UNAVAILABLE"
                    reason = "General investigative synthesis"
                    (optional if status == "OPTIONAL" else unavailable).append(eid if status == "OPTIONAL" else {"engine_id": eid, "reason": reason})

            # Level B: Forensic AI (F01–F09)
            elif eid.startswith("F") and not eid.startswith("FI"):
                if eid in audio_engines:
                    if has_audio or has_video:
                        status = "OPTIONAL" if has_video and not has_audio else "REQUIRED"
                        reason = "Acoustic / speech stream available for acoustic inspection"
                        (required if status == "REQUIRED" else optional).append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "No audio recording or video soundtrack provided"
                        unavailable.append({"engine_id": eid, "reason": reason})
                elif eid in image_required:
                    if has_image:
                        status = "REQUIRED"
                        reason = "Photographic scene exhibits present for forensic feature extraction"
                        required.append(eid)
                    elif has_video:
                        status = "OPTIONAL"
                        reason = "Extracted video keyframes available for forensic image inspection"
                        optional.append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "No scene photographs or keyframes uploaded"
                        unavailable.append({"engine_id": eid, "reason": reason})
                elif eid in image_optional:
                    if has_image or has_video:
                        status = "OPTIONAL"
                        reason = "Comparative / toolmark forensic inspection available"
                        optional.append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "No scene photographs uploaded"
                        unavailable.append({"engine_id": eid, "reason": reason})
                else:
                    status = "OPTIONAL" if evidence_list else "UNAVAILABLE"
                    reason = "Forensic inspection capability"
                    (optional if status == "OPTIONAL" else unavailable).append(eid if status == "OPTIONAL" else {"engine_id": eid, "reason": reason})

            # Level B: Financial AI (FI01–FI07)
            elif eid.startswith("FI"):
                if eid in inventory_required:
                    if has_inventory:
                        status = "REQUIRED"
                        reason = "Inventory ledger exhibit provided for stock reconciliation"
                        required.append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "No inventory ledger exhibits supplied"
                        unavailable.append({"engine_id": eid, "reason": reason})
                elif eid in pos_required:
                    if has_pos:
                        status = "REQUIRED"
                        reason = "Electronic transaction / POS log exhibit present"
                        required.append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "No electronic POS transaction log supplied"
                        unavailable.append({"engine_id": eid, "reason": reason})
                elif eid in financial_discrepancy:
                    if has_inventory or has_pos:
                        status = "REQUIRED"
                        reason = "Financial transaction/stock ledger available for discrepancy calculation"
                        required.append(eid)
                    else:
                        status = "UNAVAILABLE"
                        reason = "Neither inventory nor POS records supplied for financial discrepancy"
                        unavailable.append({"engine_id": eid, "reason": reason})
                else:
                    status = "OPTIONAL" if (has_inventory or has_pos) else "UNAVAILABLE"
                    reason = "Financial audit capability"
                    (optional if status == "OPTIONAL" else unavailable).append(eid if status == "OPTIONAL" else {"engine_id": eid, "reason": reason})

            # Level C & D: Intelligence (X01–X06) & Reconstruction (R01–R04)
            elif eid.startswith("X") or eid.startswith("R"):
                if evidence_list:
                    status = "REQUIRED"
                    reason = "Universal cross-department intelligence, correlation, sufficiency & reconstruction backbone"
                    required.append(eid)
                else:
                    status = "UNAVAILABLE"
                    reason = "Awaiting evidence intake"
                    unavailable.append({"engine_id": eid, "reason": reason})

            else:
                status = "OPTIONAL" if evidence_list else "UNAVAILABLE"
                reason = "General analytical capability"
                (optional if status == "OPTIONAL" else unavailable).append(eid if status == "OPTIONAL" else {"engine_id": eid, "reason": reason})

            all_items.append(EnginePlanItem(
                engine_id=eid,
                engine_name=ed.engine_name,
                department=dept,
                level=level,
                status=status,
                reason=reason,
                dependencies=deps
            ))

        # 3. Compute topological execution sequence for active engines
        active_ids = required + optional
        try:
            execution_order = engine_registry.resolve_dag(active_ids)
        except Exception:
            execution_order = active_ids

        return DynamicAnalysisPlan(
            case_id=case_id,
            generated_at=datetime.now(timezone.utc),
            required_engines=required,
            optional_engines=optional,
            unavailable_engines=unavailable,
            execution_order=execution_order,
            all_items=all_items
        )

dynamic_planner = DynamicAnalysisPlanner()
