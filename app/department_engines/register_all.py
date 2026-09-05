import logging
from app.department_engines.framework.registry import engine_registry

logger = logging.getLogger(__name__)

# Evidence Foundation (E01–E07)
from app.department_engines.evidence import (
    EvidenceMetadataEngine,
    EvidenceIntegrityEngine,
    EvidenceQualityEngine,
    DuplicateEvidenceEngine,
    EvidenceClassificationEngine,
    ProvenanceCustodyEngine,
    CrossEvidenceRelationshipEngine
)

# Investigation AI (I01–I12)
from app.department_engines.investigation import (
    VideoMetadataEngine,
    FrameExtractionEngine,
    PersonObjectDetectionEngine,
    PersonTrackingEngine,
    VehicleTrackingEngine,
    AppearanceAttributeEngine,
    CandidateReIDEngine,
    ZoneTransitionDwellEngine,
    ObjectInteractionEngine,
    CameraBlindSpotEngine,
    WitnessIntelligenceEngine,
    VideoEventTimelineEngine
)

# Forensic AI (F01–F09)
from app.department_engines.forensic import (
    ImageMetadataEngine,
    ImageQualityEnhancementEngine,
    SceneObjectDetectionEngine,
    DamageForceDetectionEngine,
    EntryExitPointsEngine,
    ToolmarkImpressionEngine,
    ForensicImageComparisonEngine,
    AudioForensicEngine,
    SpeechAudioEventEngine
)

# Financial AI (FI01–FI07)
from app.department_engines.financial import (
    InventoryParserEngine,
    InventoryReconciliationEngine,
    ItemSkuResolutionEngine,
    PosAnalyzerEngine,
    TransactionItemMatcherEngine,
    UnmatchedTransactionEngine,
    FinancialDiscrepancyEngine
)

# Cross-Department Intelligence (X01–X06)
from app.department_engines.intelligence import (
    CandidateEntityResolutionEngine,
    SourceTimelinesEngine,
    CrossSourceCorrelationEngine,
    InvestigationGapEngine,
    ConflictDiscrepancyEngine,
    EvidenceSufficiencyEngine
)

# Reconstruction & Human Control (R01–R04)
from app.department_engines.reconstruction import (
    EvidenceConstrainedHypothesisEngine,
    DeterministicConsistencyEngine,
    AdversarialChallengeEngine,
    HumanVerificationAuditEngine
)

logger = logging.getLogger(__name__)

def register_all_45_engines():
    """
    Registers the complete locked 45-Engine Backbone for RRE.
    E01–E07: Evidence Foundation (7)
    I01–I12: Investigation AI (12)
    F01–F09: Forensic AI (9)
    FI01–FI07: Financial AI (7)
    X01–X06: Cross-Department Intelligence (6)
    R01–R04: Reconstruction / Human Control (4)
    Total = 45 engines.
    """
    engines = [
        # Evidence Foundation
        EvidenceMetadataEngine(),
        EvidenceIntegrityEngine(),
        EvidenceQualityEngine(),
        DuplicateEvidenceEngine(),
        EvidenceClassificationEngine(),
        ProvenanceCustodyEngine(),
        CrossEvidenceRelationshipEngine(),

        # Investigation AI
        VideoMetadataEngine(),
        FrameExtractionEngine(),
        PersonObjectDetectionEngine(),
        PersonTrackingEngine(),
        VehicleTrackingEngine(),
        AppearanceAttributeEngine(),
        CandidateReIDEngine(),
        ZoneTransitionDwellEngine(),
        ObjectInteractionEngine(),
        CameraBlindSpotEngine(),
        WitnessIntelligenceEngine(),
        VideoEventTimelineEngine(),

        # Forensic AI
        ImageMetadataEngine(),
        ImageQualityEnhancementEngine(),
        SceneObjectDetectionEngine(),
        DamageForceDetectionEngine(),
        EntryExitPointsEngine(),
        ToolmarkImpressionEngine(),
        ForensicImageComparisonEngine(),
        AudioForensicEngine(),
        SpeechAudioEventEngine(),

        # Financial AI
        InventoryParserEngine(),
        InventoryReconciliationEngine(),
        ItemSkuResolutionEngine(),
        PosAnalyzerEngine(),
        TransactionItemMatcherEngine(),
        UnmatchedTransactionEngine(),
        FinancialDiscrepancyEngine(),

        # Intelligence
        CandidateEntityResolutionEngine(),
        SourceTimelinesEngine(),
        CrossSourceCorrelationEngine(),
        InvestigationGapEngine(),
        ConflictDiscrepancyEngine(),
        EvidenceSufficiencyEngine(),

        # Reconstruction & Control
        EvidenceConstrainedHypothesisEngine(),
        DeterministicConsistencyEngine(),
        AdversarialChallengeEngine(),
        HumanVerificationAuditEngine()
    ]

    for eng in engines:
        engine_registry.register(eng)

    logger.info(f"Registered {len(engines)} engines into RRE Engine Registry.")
    return len(engines)

# Automatically invoke registration when module is imported
total_registered = register_all_45_engines()
