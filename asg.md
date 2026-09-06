# Reality Reconstruction Engine (RRE 2.0)

## Complete Architectural Specification, System Roles, Engine Catalog & Operational Workflows

---

## 1. Executive Summary & Purpose

The **Reality Reconstruction Engine (RRE 2.0)** is an enterprise-grade forensic intelligence and crime reconstruction platform designed specifically for property crimes, theft, and robbery investigations. In conventional policing and commercial loss prevention, evidence is fragmented across disconnected silos: surveillance video (CCTV), crime scene photographs, witness depositions, inventory databases, and Point-of-Sale (POS) transaction logs.

RRE 2.0 transforms scattered, multimodal theft evidence into traceable observations, routes evidence to authorized specialist departments, correlates independent findings across space and time, and generates evidence-constrained hypotheses for human investigator evaluation.

### Core Distinguishing Tenets

1. **Evidence Vault & Cryptographic Integrity**: Every exhibit is preserved immutably with a SHA-256 cryptographic fingerprint calculated at intake, establishing a verifiable Chain of Custody.
2. **Strict Separation of Evidentiary Layers**: The system forbids conflating raw data with factual conclusions. It enforces an 8-tier progression:
   $$\text{Evidence} \longrightarrow \text{Observation} \longrightarrow \text{Finding} \longrightarrow \text{Claim} \longrightarrow \text{Correlated Event} \longrightarrow \text{Candidate Entity} \longrightarrow \text{Hypothesis} \longrightarrow \text{Verified Finding}$$
3. **Assisted Analysis with Human Primacy**: Computer vision and NLP models perform assisted measurement and feature extraction; human specialists review, correct, or verify findings.
4. **Two-Layer Validation & Self-Challenge**: Generated hypotheses undergo deterministic physical/mathematical checks (Layer 1: velocity limits, spatial exclusivity, temporal monotonicity) and adversarial AI counter-scrutiny (Layer 2: defense attorney simulation seeking contradictions and coverage gaps).
5. **Categorical Support Levels**: RRE eliminates arbitrary, misleading statistical percentages (e.g., "87.4% probability of guilt") in favor of categorical legal support ratings: `STRONG`, `MODERATE`, `LIMITED`, `SPECULATIVE`, `UNCONFIRMED`, and `REFUTED`.
6. **Non-Verdict Safeguard**: RRE never renders a judicial verdict, assigns criminal culpability, or declares guilt. Judicial determinations remain the sole prerogative of human investigators, prosecutors, and the courts.

---

## 2. System Architecture & Component Topology

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    REACT 19 FRONTEND                                   │
│  ┌───────────────────────────┬───────────────────────────┬──────────────────────────┐  │
│  │ Lead Investigator Command │  Forensic Workstation     │ Financial Ledger Workst. │  │
│  ├───────────────────────────┼───────────────────────────┼──────────────────────────┤  │
│  │ Judicial Review / Export  │  Evidence Vault & Intake  │ Unified Reconstruct Studio│  │
│  └───────────────────────────┴───────────────────────────┴──────────────────────────┘  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ HTTPS / REST / WebSockets
┌──────────────────────────────────────────▼─────────────────────────────────────────────┐
│                                   FASTAPI CORE BACKEND                                 │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Authentication & ABAC Policy Enforcement (Role, Department, Case Assignment)    │  │
│  ├──────────────────────────────────────────────────────────────────────────────────┤  │
│  │  Evidence Ingestion & Cryptographic Verification Engine (SHA-256)                │  │
│  ├──────────────────────────────────────────────────────────────────────────────────┤  │
│  │  Dynamic Analysis Planner & DAG Dependency Sequencer                             │  │
│  ├──────────────────────────────────────────────────────────────────────────────────┤  │
│  │  45-Engine Departmental Backbone & Dispatcher                                    │  │
│  ├──────────────────────────────────────────────────────────────────────────────────┤  │
│  │  Cross-Domain Intelligence, Gaps & Conflicts Radar, Sufficiency Gate (X06)       │  │
│  ├──────────────────────────────────────────────────────────────────────────────────┤  │
│  │  Multi-Hypothesis Synthesis & 2-Layer Validation Engine (R01 - R04)              │  │
│  ├──────────────────────────────────────────────────────────────────────────────────┤  │
│  │  Dual-Mode Investigation Copilot (Gemini 1.5 Flash + Prohibited Query Filter)    │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────┬───────────────────────────────┬────────────────────────────────┘
                        │                               │
        ┌───────────────▼───────────────┐       ┌───────▼────────────────────────┐
        │  DATABASE & STORAGE LAYER     │       │   EXTERNAL AI PROVIDERS        │
        │  - SQLite (aiosqlite) / PG    │       │   - Google Gemini 1.5 Flash    │
        │  - SQLAlchemy 2.0 Async ORM   │       │   - Structured JSON Extraction │
        │  - Local Vault / MinIO S3     │       │   - Adversarial Challenging    │
        │  - Immutable Audit Ledger     │       │   - Vector Embeddings          │
        └───────────────────────────────┘       └────────────────────────────────┘
```

### 2.1 Backend Technology Stack

- **Web Framework**: FastAPI 0.110+ (Python 3.12+) running asynchronously with Uvicorn.
- **Persistence & ORM**: SQLAlchemy 2.0 (Async Session) paired with `aiosqlite` for local development and `asyncpg` for PostgreSQL production deployments.
- **Schema Validation**: Pydantic v2 schemas enforcing strict model validation for all inputs and outputs.
- **Authentication**: Dual-mode auth integrating Firebase Admin SDK (ID Token verification) and local JWT authentication.
- **AI / LLM Integration**: Google Gemini API via official `google-genai` SDK, supporting multimodal context, structured JSON output extraction, and fallback mechanisms.

### 2.2 Frontend Technology Stack

- **UI Framework**: React 19 bootstrapped with Vite 6.
- **Design System**: Strict Blue & White light theme (`#2563eb` Royal Blue, `#ffffff` Crisp White, `#f8fafc` Ice Slate background) utilizing Vanilla CSS variables.
- **Icons & Visuals**: Lucide React for consistent iconography.
- **Client Auth**: Firebase Client SDK for user authentication, password resets, and session tokens.

---

## 3. User Roles & Access Control Matrix (ABAC)

RRE 2.0 implements **Attribute-Based Access Control (ABAC)**. Permissions depend on:

1. **User Role** (Authority tier)
2. **User Department** (Functional domain)
3. **Case Assignment** (Active assignment to the specific case)
4. **Evidence Routing Tags** (`authorized_departments` metadata)

### 3.1 Role Descriptions

| Role | Department | Primary Responsibilities |
| :--- | :--- | :--- |
| **`ADMIN`** | `ADMIN` | Full administrative control, organization onboarding, global audit log review, engine telemetry configuration. |
| **`LEAD_INVESTIGATOR`** | `INVESTIGATION` | Case creation, team assignment, dynamic plan generation, triggering reconstruction, hypothesis evaluation, case closure. |
| **`INVESTIGATOR`** | `INVESTIGATION` | Field surveillance review, CCTV evidence upload, observation notation, candidate entity linking, witness statement intake. |
| **`FORENSIC_OFFICER`** | `FORENSIC` | Scene photo intake, toolmark impression analysis, entry/exit point damage verification, physical evidence custody. |
| **`FINANCIAL_ANALYST`** | `FINANCIAL` | Inventory log parsing, SKU stock reconciliation, Point-of-Sale (POS) transaction log matching, monetary loss calculation. |
| **`PROSECUTOR_JUDGE`** | `LEGAL` | Read-only dossier review, evidence integrity auditing, hypothesis plausibility evaluation, legal report generation. |

### 3.2 ABAC Permission Matrix

| Action | `ADMIN` | `LEAD_INVESTIGATOR` | `INVESTIGATOR` | `FORENSIC_OFFICER` | `FINANCIAL_ANALYST` | `PROSECUTOR_JUDGE` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`VIEW_CASE`** | Any | Assigned / Owned | Assigned | Assigned | Assigned | Assigned (Read-Only) |
| **`UPDATE_CASE`** | Yes | Yes | Assigned Case | No | No | No |
| **`ASSIGN_CASE`** | Yes | Yes | No | No | No | No |
| **`UPLOAD_EVIDENCE`** | Yes | Yes | Yes | Yes (Forensic) | Yes (Financial) | No |
| **`VIEW_EVIDENCE`** | Yes | Yes | Routing-based | Routing-based | Routing-based | Yes (Read-Only) |
| **`PROCESS_EVIDENCE`** | Yes | Yes | Yes | Forensic Only | Financial Only | No |
| **`CREATE_OBSERVATION`** | Yes | Yes | Yes | Forensic Only | Financial Only | No |
| **`VERIFY_OBSERVATION`** | Yes | Yes | Yes | No | No | No |
| **`CONFIRM_ENTITY_LINK`** | Yes | Yes | Yes | No | No | No |
| **`MODIFY_TIMELINE`** | Yes | Yes | Yes | Yes | **No (Blocked)** | No |
| **`TRIGGER_RECONSTRUCTION`** | Yes | Yes | No | No | No | No |
| **`REVIEW_HYPOTHESIS`** | Yes | Yes | Yes | No | No | No |
| **`RESOLVE_GAP_CONFLICT`** | Yes | Yes | Yes | No | No | No |
| **`QUERY_COPILOT`** | Yes | Yes | Yes | Yes | Yes | Yes |
| **`GENERATE_REPORT`** | Yes | Yes | Yes | Yes | Yes | Yes |

---

## 4. The 45-Engine Backbone

RRE 2.0 organizes processing into **45 specialized analytical engines** arranged across 6 hierarchical tiers. Every engine adheres to the standard `BaseEngine` interface and outputs structured `EngineExecutionRecord` telemetry.

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               45-ENGINE TAXONOMY                                 │
├────────────────────────────────┬─────────────────────────────────────────────────┤
│ Tier 1: Evidence Foundation    │ E01–E07 (7 Engines): Integrity, Hashes, Custody │
│ Tier 2: Investigation AI       │ I01–I12 (12 Engines): Video, Tracks, Re-ID       │
│ Tier 3: Forensic AI            │ F01–F09 (9 Engines): Toolmarks, Damage, Images  │
│ Tier 4: Financial AI           │ FI01–FI07 (7 Engines): Stock, SKU, POS Audits   │
│ Tier 5: Intelligence & Gaps    │ X01–X06 (6 Engines): Correlation, Gaps, Gate    │
│ Tier 6: Reconstruction Studio  │ R01–R04 (4 Engines): Hypotheses, 2-Layer Verify │
└────────────────────────────────┴─────────────────────────────────────────────────┘
```

### 4.1 Tier 1: Evidence Foundation (E01–E07)

Foundational engines guarantee forensic integrity, extract raw container metadata, and map exhibit relationships.

1. **`E01: EvidenceMetadataEngine`** (Deterministic)
   - *Purpose*: Extracts container-level properties (MIME type, file size, EXIF, creation timestamp, container encoding).
   - *Inputs*: Raw exhibit binary.
   - *Outputs*: Formatted metadata dictionary, capture timestamps, equipment models.
2. **`E02: EvidenceIntegrityEngine`** (Deterministic)
   - *Purpose*: Calculates SHA-256 cryptographic digest upon intake and re-verifies it during processing to guarantee non-tampering.
   - *Outputs*: SHA-256 hash string, bit-level integrity status (`INTACT` or `CORRUPTED`).
3. **`E03: EvidenceQualityEngine`** (Deterministic)
   - *Purpose*: Measures video resolution, frame drops, audio signal-to-noise ratio (SNR), and image blur.
   - *Outputs*: Categorical quality rating (`HIGH`, `MEDIUM`, `LOW`, `POOR`).
4. **`E04: DuplicateEvidenceEngine`** (Deterministic)
   - *Purpose*: Flags byte-identical files or perceptual duplicate images to prevent redundant processing.
   - *Outputs*: Duplicate match percentage, primary exhibit reference ID.
5. **`E05: EvidenceClassificationEngine`** (Hybrid)
   - *Purpose*: Classifies exhibit modality into recognized forensic types (`CCTV`, `IMAGE`, `AUDIO`, `INVENTORY_RECORD`, `TRANSACTION_RECORD`, `WITNESS_STATEMENT`).
   - *Outputs*: Target department tags, downstream engine eligibility.
6. **`E06: ProvenanceCustodyEngine`** (Workflow)
   - *Purpose*: Records logging user, uploading IP, legal collection jurisdiction, and intake custody timestamps.
   - *Outputs*: Chain of Custody entry.
7. **`E07: CrossEvidenceRelationshipEngine`** (Deterministic)
   - *Purpose*: Discovers relationships between exhibits (e.g., Camera A and Camera B covering opposite angles of Entrance Door 1).
   - *Outputs*: Spatial and temporal exhibit pairing links.

### 4.2 Tier 2: Investigation AI (I01–I12)

Specialized computer vision and natural language processing engines for video surveillance and witness analysis.

1. **`I01: VideoMetadataEngine`** (Deterministic): Parses stream duration, FPS, codecs, aspect ratio, and native timecode tracks.
2. **`I02: FrameExtractionEngine`** (Deterministic): Performs scene-change detection, keyframe extraction, and downsampled interval slicing.
3. **`I03: PersonObjectDetectionEngine`** (Model): Employs object detection to bound human subjects, backpacks, carried bags, and tools.
4. **`I04: PersonTrackingEngine`** (Model): Executes temporal Multi-Object Tracking (MOT), assigning tracklet IDs (e.g., `TRK_01`) across continuous video frames.
5. **`I05: VehicleTrackingEngine`** (Model): Detects vehicles, extracts make/model/color characteristics, and tracks ingress/egress trajectories.
6. **`I06: AppearanceAttributeEngine`** (Model): Extracts soft biometric features (upper/lower clothing color, headwear, face coverings, backpack presence).
7. **`I07: CandidateReIDEngine`** (Model): Extracts visual feature embeddings to match subjects across non-overlapping camera feeds.
8. **`I08: ZoneTransitionDwellEngine`** (Deterministic): Computes loitering times and zone boundary crossing timestamps (e.g., entering "Stockroom Restricted Zone").
9. **`I09: ObjectInteractionEngine`** (Model): Flags physical interactions between detected subjects and retail merchandise or display fixtures.
10. **`I10: CameraBlindSpotEngine`** (Deterministic): Maps camera fields-of-view against floor plans, highlighting unmonitored transition corridors.
11. **`I11: WitnessIntelligenceEngine`** (LLM): Parses witness transcripts to extract observed times, actor descriptions, and action narratives.
12. **`I12: VideoEventTimelineEngine`** (Deterministic): Synthesizes detected video incidents into a source-specific timeline of events.

### 4.3 Tier 3: Forensic AI (F01–F09)

Physical scene examination, structural deformation assessment, and acoustic forensics.

1. **`F01: ImageMetadataEngine`** (Deterministic): Extracts detailed EXIF metadata, lens parameters, focal lengths, and camera sensor specs.
2. **`F02: ImageQualityEnhancementEngine`** (Deterministic): Applies adaptive contrast equalization and de-noising to reveal latent details.
3. **`F03: SceneObjectDetectionEngine`** (Model): Identifies evidence markers, discarded tools, and physical evidence items in crime scene photos.
4. **`F04: DamageForceDetectionEngine`** (Model): Classifies physical destruction (e.g., forced lock cylinder, shattered display glass, bent metal frames).
5. **`F05: EntryExitPointsEngine`** (Hybrid): Evaluates doors, windows, and perimeter breach points for indicators of forced vs. authorized ingress.
6. **`F06: ToolmarkImpressionEngine`** (Hybrid): Measures toolmark impressions (pry gouges, bolt-cutter shears) and compares them with standard tool profiles.
7. **`F07: ForensicImageComparisonEngine`** (Deterministic): Calculates Structural Similarity Index (SSIM) and pixel differences between baseline and post-incident states.
8. **`F08: AudioForensicEngine`** (Deterministic): Generates spectral audio waterfalls and filters background acoustic hums.
9. **`F09: SpeechAudioEventEngine`** (Model): Flags transient acoustic anomalies (glass breaks, alarm sirens, metal impact clatter, shouting).

### 4.4 Tier 4: Financial AI (FI01–FI07)

Reconciliation of physical inventory against transactional books and electronic cash registers.

1. **`FI01: InventoryParserEngine`** (Deterministic): Ingests and standardizes inventory spreadsheets, stock lists, CSVs, and SKU catalog files.
2. **`FI02: InventoryReconciliationEngine`** (Deterministic): Reconciles physical counts against expected stock levels, computing unit shortages and shrinkage.
3. **`FI03: ItemSkuResolutionEngine`** (Deterministic): Maps barcodes, serial numbers, and retail descriptions to standardized item identities.
4. **`FI04: PosAnalyzerEngine`** (Deterministic): Parses Point-of-Sale transaction logs, timestamps, terminal IDs, and operator employee codes.
5. **`FI05: TransactionItemMatcherEngine`** (Deterministic): Matches missing items against registered sales transactions to rule out legitimate purchases.
6. **`FI06: UnmatchedTransactionEngine`** (Deterministic): Detects anomalous POS events (no-sale till openings, immediate voids, abnormal price overrides).
7. **`FI07: FinancialDiscrepancyEngine`** (Deterministic): Calculates total monetary loss, missing unit quantities, and financial discrepancy categories.

### 4.5 Tier 5: Cross-Department Intelligence (X01–X06)

Correlates findings across separate departments, detects evidentiary gaps and contradictions, and gates reconstruction.

1. **`X01: CandidateEntityResolutionEngine`** (Hybrid): Merges visual tracks, witness descriptions, and physical markers into candidate entities (e.g., `Person P1`, `Vehicle V1`, `Item ITEM_01`).
2. **`X02: SourceTimelinesEngine`** (Deterministic): Assembles independent, unadulterated chronological streams per evidence source (CCTV, POS, Witness, Forensics).
3. **`X03: CrossSourceCorrelationEngine`** (Deterministic): Detects spatio-temporal coincidences between independent streams (e.g., Subject P1 in Zone 2 coincident with unrecorded inventory deficit).
4. **`X04: InvestigationGapEngine`** (Deterministic): Detects critical coverage blind spots (e.g., missing video coverage, unmonitored exits, gaps between cameras).
5. **`X05: ConflictDiscrepancyEngine`** (Hybrid): Evaluates evidence across **7 locked conflict classes**:
   - `HARD_CONTRADICTION`: Incompatible facts (e.g., suspect clocked at location A while phone records show location B).
   - `SOFT_DISCREPANCY`: Minor non-fatal differences in reporting (e.g., 5-minute time difference).
   - `SOURCE_DISAGREEMENT`: Witness description conflicts with sensor data (e.g., witness reports "red jacket", camera shows "navy jacket").
   - `TEMPORAL_DISCREPANCY`: Non-synchronized clock sources.
   - `CORROBORATIVE_DISCREPANCY`: Independent witnesses disagree on secondary details.
   - `WITNESS_CONFLICT`: Direct contradictions between two witness depositions.
   - `UNCERTAINTY`: Unresolved ambiguities where data is insufficient to establish fact.
6. **`X06: EvidenceSufficiencyEngine`** (Hybrid — **The Reconstruction Gate**)
   - Evaluates whether collected evidence meets the threshold for a defensible reconstruction.
   - Returns one of four ratings:
     - `SUFFICIENT_FOR_RECONSTRUCTION`: Multi-source corroboration exists; authorizes R01 hypothesis generation.
     - `MARGINAL_PROBATIVE_VALUE`: Proceed with warnings regarding severe gaps.
     - `INSUFFICIENT_FOR_RECONSTRUCTION`: **Halts downstream reconstruction**. Prevents hallucinated conclusions.
     - `NO_DEFENSIBLE_RECONSTRUCTION`: Modality absent or contradictory; downstream engines return `BLOCKED`.

### 4.6 Tier 6: Reconstruction & Human Control (R01–R04)

Synthesizes competing hypotheses, validates physical plausibility, and subjects claims to adversarial challenge.

1. **`R01: EvidenceConstrainedHypothesisEngine`** (Hybrid)
   - *Gated by*: `X06` sufficiency check.
   - *Operation*: Generates competing hypotheses (Primary, Alternative Benign, Third-Party). Every claim cites verified engine outputs.
2. **`R02: DeterministicConsistencyEngine`** (Deterministic — **Layer 1 Validation**)
   - *Temporal Monotonicity*: Checks that timestamps progress forward without retrograde time travel.
   - *Spatial Exclusivity*: Checks that an entity is not recorded in two distant places at the same second.
   - *Transit Velocity Feasibility*: Calculates velocity ($v = d / t$); if velocity exceeds human running thresholds ($>4.0\text{ m/s}$), flags impossibility. If spatial data is missing, returns `NOT_ASSESSABLE`.
3. **`R03: AdversarialChallengeEngine`** (Hybrid — **Layer 2 Validation**)
   - Plays the role of a skeptical defense advocate.
   - Scrutinizes gaps from X04 and conflicts from X05 to challenge each hypothesis, highlighting reasonable doubt and unobserved intervals.
4. **`R04: HumanVerificationAuditEngine`** (Workflow)
   - Manages the human verification lifecycle: `ACCEPT`, `CORRECT`, `REJECT`, `REANALYSIS_REQUESTED`.
   - Records every human determination into the immutable audit ledger.

---

## 5. End-to-End Working Flows

### 5.1 The Complete Investigation Lifecycle

```text
[1. Case Creation] ──> [2. Evidence Intake] ──> [3. Dynamic Planning] ──> [4. Engine Dispatch]
        │                       │                        │                       │
        ▼                       ▼                        ▼                       ▼
Case metadata,          SHA-256 Hash,           DAG generated based     45-Engine execution;
objectives & context    ABAC routing & vault    on uploaded modalities  telemetry logged
                                                                                 │
┌────────────────────────────────────────────────────────────────────────────────┘
│
▼
[5. Cross-Domain Intelligence] ──> [6. Sufficiency Gate (X06)] ──> [7. Multi-Hypothesis (R01)]
        │                                        │                              │
        ▼                                        ▼                              ▼
Candidate entities (X01),                If INSUFFICIENT:               Synthesizes Primary &
source timelines (X02),                  Halt downstream                Alternative Hypotheses;
gaps (X04) & conflicts (X05)             with clear reason              Strict citation check
                                                                                │
┌───────────────────────────────────────────────────────────────────────────────┘
│
▼
[8. Two-Layer Validation] ───────> [9. Human Specialist Review] ──> [10. Copilot & Court Export]
        │                                        │                              │
        ▼                                        ▼                              ▼
Layer 1: Physics & Speed (R02)           Specialist verification:       Dual-mode Copilot,
Layer 2: Adversarial AI (R03)            Accept, Correct, Reject        Signed Report generation
```

#### Step 1: Case Creation & Intake Wizard

The Lead Investigator creates a case, setting the case type (`THEFT` or `ROBBERY`), specific offense (e.g., `BURGLARY_THEFT`, `COMMERCIAL_ROBBERY`), incident location, time window, and investigative objectives.

#### Step 2: Evidence Intake & Cryptographic Vaulting

1. Exhibits are uploaded via the Evidence Vault.
2. The server streams the file directly, computes its **SHA-256 hash**, extracts file size, and stores the file immutably.
3. The exhibit is tagged with authorized departments (e.g., `["INVESTIGATION", "FORENSIC"]`).
4. An entry is recorded in the `audit_log` with user ID, IP address, and timestamp.

#### Step 3: Dynamic Analysis Planning

The `DynamicAnalysisPlanner` inspects the case exhibit manifest. It determines:

- Which modalities exist (Video, Photos, Audio, Inventory, POS, Witness Statements).
- Which of the 45 engines are **REQUIRED**, **OPTIONAL**, or **UNAVAILABLE**.
- Computes a topologically sorted DAG (Directed Acyclic Graph) execution sequence.

#### Step 4: Departmental Processing & Feature Extraction

The engine dispatcher executes the planned engines in topological order:

- Video engines extract tracks, appearance attributes, and zone dwell events.
- Forensic engines measure damage markers and toolmark impressions.
- Financial engines parse inventory spreadsheets, calculate unit shortages, and check POS logs.

Outputs are stored in memory and converted into database `Observation` records.

#### Step 5: Entity Resolution & Timeline Synthesis

- `X01` clusters observations across cameras and witness statements into candidate entities (`P1`, `V1`, `ITEM1`).
- `X02` generates clean, source-specific chronologies for each exhibit.
- `X03` correlates spatial and temporal overlap between independent streams.

#### Step 6: Gap & Conflict Detection

- `X04` scans for unmonitored zones, blind corridors, and missing camera coverage.
- `X05` evaluates all 7 conflict classes, flagging contradictions between witness statements and sensor logs.

#### Step 7: Sufficiency Gate (X06) & Hypothesis Synthesis (R01)

- `X06` checks if the minimum threshold for reconstruction is satisfied.
  - *If Insufficient*: Downstream engines `R01`, `R02`, and `R03` are automatically set to `BLOCKED`. The UI shows a clear explanation of what missing evidence prevented reconstruction.
  - *If Sufficient*: `R01` synthesizes competing hypotheses. Each claim is checked against the **Evidence Reference Integrity Gate**; any ungrounded citation is rejected.

#### Step 8: Two-Layer Validation & Self-Challenge

- **Layer 1 (R02)**: Tests mathematical and physical feasibility.
  - Monotonicity: Ensures timeline proceeds chronologically.
  - Spatial exclusivity: Ensures no teleportation across cameras.
  - Transit velocity: Checks that movement speed between points is physically possible ($<4\text{ m/s}$).
- **Layer 2 (R03)**: Adversarial AI challenges the hypotheses, identifying unobserved exit routes, camera blind spots, and alternative explanations.

#### Step 9: Human Verification Workflow

Human specialists review findings in their department workstations:

- Specialists inspect AI detections and submit verifications (`ACCEPTED`, `CORRECTED`, `REJECTED`, `REANALYSIS_REQUESTED`).
- Corrections update the downstream graph while preserving the original model output for forensic auditability.

#### Step 10: Investigation Copilot & Report Generation

- Authorized personnel query the **Investigation Copilot** in either `EVIDENCE` or `REASONING` mode. Prohibited queries (asking for verdicts or declarations of guilt) are intercepted by safety guardrails.
- The platform compiles a comprehensive **Evidence Reconstruction Report** with cryptographic hashes, timeline charts, and audit trails for judicial review.

---

## 6. Database Entity Architecture

The database schema is organized into normalized relational tables mapped via SQLAlchemy ORM.

```text
                           ┌──────────────────┐
                           │   Organization   │
                           └────────┬─────────┘
                                    │ 1:N
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            ┌──────────────┐                ┌──────────────┐
            │     User     │                │     Case     │
            └───────┬──────┘                └───────┬──────┘
                    │                               │
       ┌────────────┼─────────────┐                 ├─────────────────────────────┐
       │            │             │                 │                             │
       ▼            ▼             ▼                 ▼                             ▼
┌──────────────┐┌──────────────┐┌───────────┐┌──────────────┐             ┌──────────────┐
│CaseAssignment││ Verification ││ AuditLog  ││   Evidence   │             │  Hypothesis  │
└──────────────┘└──────────────┘└───────────┘└──────┬───────┘             └──────────────┘
                                                    │ 1:N
                                                    ▼
                                            ┌──────────────┐
                                            │ Observation  │
                                            └───────┬──────┘
                                                    │
                                    ┌───────────────┴───────────────┐
                                    ▼                               ▼
                        ┌───────────────────────┐       ┌───────────────────────┐
                        │  CandidateEntityLink  │       │  SourceTimelineEvent  │
                        └───────────┬───────────┘       └───────────────────────┘
                                    │ N:1
                                    ▼
                        ┌───────────────────────┐
                        │    CandidateEntity    │
                        └───────────────────────┘
```

### 6.1 Database Models Summary

1. **`Organization`**: Multi-tenant isolation container.
2. **`User`**: User accounts with email, role (`Role`), department (`Department`), and active flags.
3. **`Case`**: Core case entity containing case number, title, offense type, objectives, context, status, and versioning.
4. **`CaseVersion`**: Snapshot history of case state for complete reproducibility.
5. **`CaseAssignment`**: ABAC mapping linking users to cases by department.
6. **`Evidence`**: Metadata, storage path, SHA-256 fingerprint, authorized departments, and processing status.
7. **`Observation`**: Individual feature extracted from evidence (bounding box, detection confidence, timestamp, model version, verification status).
8. **`CandidateEntity`**: Reconstructed person, vehicle, or item entity (`P1`, `V1`, `ITEM1`) with attribute profiles.
9. **`CandidateEntityLink`**: Association between an observation and a candidate entity with link confidence and human confirmation status.
10. **`Finding`**: Departmental finding aggregating multiple observations with composite confidence and corroboration sources.
11. **`Claim`**: Factual assertion derived from findings, rated by claim strength (`STRONG`, `MODERATE`, `WEAK`, `SPECULATIVE`).
12. **`SourceTimeline` & `SourceTimelineEvent`**: Source-specific chronological stream and timestamped events.
13. **`CorrelatedTimelineEvent`**: Multi-source correlated timeline event linking evidence across departments.
14. **`Hypothesis`**: Competing reconstructive narrative with step sequences, supporting/contradicting citations, assumptions, and validation outputs.
15. **`GapConflict`**: Evidentiary blind spots and cross-source contradictions with significance ratings.
16. **`Verification`**: Immutable record of human specialist review (`ACCEPTED`, `CORRECTED`, `REJECTED`, `REANALYSIS_REQUESTED`).
17. **`AuditLog`**: Comprehensive audit trail recording user, action, target entity, before/after JSON states, IP address, and timestamp.
18. **`Report`**: Generated case report with versioning and JSON snapshots.

---

## 7. Frontend User Interface Modules

The frontend provides dedicated views tailored to each role, while maintaining a unified Blue & White design aesthetic.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ NAVIGATION BAR: App Brand | Active Case Selector | Role Indicator | User Profile      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ MAIN CONTENT AREA: Role Dashboards or Specialized Modules                             │
│                                                                                        │
│  [Dashboards]                  [Investigation Modules]                                 │
│  - Lead Investigator           - Evidence Vault (Upload & Integrity)                   │
│  - Forensic Specialist         - Dynamic Analysis Plan Viewer                          │
│  - Financial Analyst           - Correlated Chronological Timeline                     │
│  - Judicial Review             - Reconstruction Studio (Hypotheses & Validation)      │
│                                - Gaps & Conflicts Radar                                │
│                                - Candidate Entity Linkage Network                      │
│                                - Investigation Copilot Chat                            │
│                                - Evidence Reconstruction Report & Dossier              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 7.1 Specialized Dashboards

- **Lead Investigator Command Dashboard**:
  - High-level case metrics (total exhibits, verified findings, active gaps, top hypothesis).
  - 1-Click "Trigger Full Reconstruction" button executing the complete 45-engine pipeline.
  - Quick-action buttons to open Case Intake Wizard, Review Studio, or Export Dossier.
- **Forensics Specialist Workstation**:
  - Direct inspection of photographic exhibits, macro toolmark views, and forced entry points.
  - Evidence Custody Ledger showing intake timestamps and verification statuses.
- **Financial Analyst Ledger Workstation**:
  - Interactive inventory deficit table showing missing SKUs, units, and monetary shrinkage.
  - POS discrepancy breakdown matching sales transactions against missing inventory.
- **Judicial Review & Export Workstation**:
  - Read-only legal presentation view with verified findings and complete chain of custody.
  - One-click print stylesheet and JSON export for court submission.

### 7.2 Core Investigation Modules

- **Evidence Vault**: Secure upload with drag-and-drop, real-time SHA-256 calculation, departmental policy routing, and file integrity validation.
- **Analysis Plan Viewer**: Visualizes the dynamically generated DAG plan, showing which engines are required, optional, or blocked.
- **Correlated Timeline**: Interactive chronological stream featuring department badges, source citations, and conflict highlights.
- **Reconstruction Studio**: Displays competing hypotheses evaluated across categorical Evidence Support Levels, along with Layer 1 (physics) and Layer 2 (adversarial) validation cards.
- **Gaps & Conflicts Radar**: Visualizes coverage blind spots, unobserved intervals, and cross-source disagreements.
- **Candidate Entity Network**: Visualizes links between observations and candidate entities (`P1`, `V1`), with human confirmation controls.
- **Investigation Copilot**: Interactive conversational assistant with strict operational modes (`EVIDENCE_ONLY` vs. `REASONING_MODE`) and judicial safeguards.
- **Unified Reconstruction Output**: Comprehensive multi-tab investigation overview unifying telemetry, timeline, hypotheses, gaps, and audit logs.

---

## 8. Security, Safeguards & Judicial Defensibility

### 8.1 Non-Verdict Design Principle

RRE 2.0 is an evidence intelligence tool, not an automated judge:

- **No Guilt Determinations**: The system never outputs declarations such as "Suspect X is guilty" or "This individual committed theft."
- **Prohibited Query Interception**: The Copilot detects prohibited phrases (e.g., "who is the thief", "is suspect guilty") and returns a standardized safeguard response stating that guilt is an exclusive judicial determination.
- **Evidence-Constrained Outputs**: Every AI-generated statement must cite specific, verified evidence exhibits. Ungrounded statements are automatically rejected by the integrity gate.

### 8.2 Cryptographic Chain of Custody & Audit Logging

- **Intake Hashing**: Every exhibit is hashed using SHA-256 upon receipt. The hash is verified prior to any downstream engine processing.
- **Immutable Audit Trail**: Every user action (evidence upload, engine execution, verification, hypothesis review) creates an immutable `audit_log` entry containing:
  - User ID, role, and organization.
  - Action name and target entity ID.
  - Complete `before_state` and `after_state` JSON snapshots.
  - Client IP address and UTC timestamp.

### 8.3 Truthful Execution Telemetry

RRE 2.0 enforces absolute transparency regarding AI involvement:

- Every engine record reports its exact execution path:
  - `DETERMINISTIC_ONLY`: Pure mathematical or algorithmic logic.
  - `REAL_LLM`: LLM was invoked and returned grounded output.
  - `BLOCKED_UNAVAILABLE_MODALITY`: Required evidence type was not provided.
  - `BLOCKED_PREREQUISITE_INSUFFICIENT`: Upstream engine output did not meet the sufficiency threshold.
- The system never substitutes synthetic or placeholder data for missing real-world inputs.

---

## 9. Quick Start & Execution Guide

### 9.1 Environment Configuration

Create a `.env` file in the project root:

```env
APP_NAME="Reality Reconstruction Engine"
ENVIRONMENT="development"
DATABASE_URL="sqlite+aiosqlite:///./rre.db"
GEMINI_API_KEY="your-google-gemini-api-key"
LLM_MODEL="gemini-1.5-flash"
SECRET_KEY="your-jwt-secret-key"
```

### 9.2 Running the Application

```bash
# Terminal 1: Backend API
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: React Frontend
cd frontend
npm run dev
```

- **Web Application**: `http://127.0.0.1:5173/` (or `http://127.0.0.1:8000/`)
- **Interactive Swagger API Docs**: `http://127.0.0.1:8000/docs`

### 9.3 Running the Automated Test Suite

```bash
pytest -v
```

All 17 automated test suites execute end-to-end checks across authentication, ABAC policy enforcement, evidence routing, timeline correlation, multi-hypothesis reconstruction, and non-verdict safeguards.

---

*Reality Reconstruction Engine (RRE 2.0) — Built for ethical, auditable, and transparent forensic intelligence.*
