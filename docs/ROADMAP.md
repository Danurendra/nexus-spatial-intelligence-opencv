# Roadmap — Nexus Spatial Intelligence

**Planning baseline:** 2026-10-23. Adjust dates and priorities to the official competition deadline and rubric. This is a plan, not proof that any milestone has been completed.

## Prioritization rules

1. Protect a working, reproducible demo over feature count.
2. Validate OpenCV behavior locally before adding infrastructure.
3. Make every milestone have a concrete acceptance test.
4. Keep new services, models, and dependencies out of scope unless they improve a required outcome.
5. Reserve time for evaluation, documentation, demo recording, and final submission.

## Milestones

### M0 — Repository baseline and scope

**Priority:** P0 · **Status:** In progress / not yet verified

Tasks:
- Initialize the new repository and commit the continuity documents.
- Inspect the actual environment and confirm Python/package availability.
- Verify the installed OpenCV version directly; the required major version is 5.
- Select one narrow video-analysis use case and identify a lawful test clip.
- Write a short list of measurable acceptance criteria.

Acceptance criteria:
- Clean repository baseline exists.
- Setup instructions are reproducible.
- OpenCV version and video I/O support are recorded from actual command output.

### M1 — Local computer-vision pipeline

**Priority:** P0 · **Status:** IMPLEMENTED & VERIFIED

Tasks:
- ✓ Read one video and capture metadata.
- ✓ Process a documented set of frames.
- ✓ Apply a simple ROI and motion/foreground analysis.
- ✓ Write an annotated output and spatial heatmap.
- ✓ Generate a JSON report and run metadata.
- ✓ Comprehensive automated test suite.

Acceptance criteria:
- ✓ A test video completes end-to-end.
- ✓ All expected artifacts exist, are non-empty, and can be reopened/parsed.
- ✓ Report values match observed processing; errors are explicit.

**Evidence:**
- Tested with 300-frame synthetic video (640x480, 30 FPS)
- Processed in 2.06 seconds (158 FPS throughput)
- Generated all artifacts successfully
- 13 automated tests passing
- Motion metrics: avg 3.72%, min 0%, max 8.61%, std 1.90%

### M2 — Minimal API integration

**Priority:** P1 · **Status:** IMPLEMENTED & VERIFIED

Tasks:
- ✓ Add GET /health endpoint for service status.
- ✓ Add POST /analyze endpoint for video upload and analysis.
- ✓ Implement file validation (type, size, content).
- ✓ Safe file handling with temp directory cleanup.
- ✓ Return JSON with status, run_id, metrics, artifact references.
- ✓ Comprehensive error handling and logging.
- ✓ Automated API test suite (15 tests).

Acceptance criteria:
- ✓ Client can submit a supported video and receive a truthful report.
- ✓ Invalid inputs fail safely and predictably.
- ✓ Temporary upload files are cleaned up on success and failure.
- ✓ API response includes run ID, metrics, and artifact paths.
- ✓ All M1 tests continue to pass (core pipeline untouched).

**Evidence:**
- 15 API tests passing (health, valid upload, validation, error handling)
- Tested with synthetic video: 30 frames, 0.14s processing (209 FPS)
- File validation: type checks, size limits, content validation
- Temp file cleanup verified
- All error cases properly rejected (400/500)
- Response includes processing metrics and artifact references

### M3 — Adaptive analysis and decision trace

**Priority:** P1 · **Status:** IMPLEMENTED & VERIFIED

Tasks:
- ✓ Define measurable condition based on initial motion metrics.
- ✓ Implement bounded follow-up action (16x16 grid refinement).
- ✓ Record observation, decision, action, reanalysis result, and final status.
- ✓ Compare adaptive vs baseline results.
- ✓ Decision demonstrably changes next action (deterministic policy).

Acceptance criteria:
- ✓ The next action demonstrably changes when initial observation changes.
- ✓ Tests verify both action-triggered and non-triggered cases.
- ✓ Decision trace recorded in JSON report.
- ✓ Follow-up analysis respects processing bounds (uses same frames).

**Evidence:**
- 18 tests passing (policy logic, engine, decision traces, end-to-end)
- Both decision branches verified: triggered and skipped
- Low activity (3.72%) triggers follow-up ✓
- High activity (high threshold) skips follow-up ✓
- Decision trace includes: policy, observations, condition, decision, reason, config, results
- Follow-up heatmap generated separately (16x16 grid)
- Report version 1.1 with adaptive_analysis section
- CLI parameter: --adaptive-threshold allows policy tuning

### M4 — AWS integration

**Priority:** P1 · **Status:** IMPLEMENTED & VERIFIED (Optional S3 artifact storage component)

Tasks:
- ✓ Implement optional S3 artifact storage component (S3StorageConfig, S3StorageClient)
- ✓ Configure storage via environment variables (no hardcoded credentials)
- ✓ Integrate S3 uploads with FastAPI POST /analyze endpoint
- ✓ Add S3 metadata to health check and API responses
- ✓ Implement graceful fallback to local storage when S3 disabled
- ✓ Create comprehensive mock-based S3 tests (18 unit tests + 4 API tests)
- ✓ Verify all dependencies installed (boto3 1.34.39, botocore 1.34.162)
- ✓ Document configuration and behavior

Acceptance criteria:
- ✓ S3 storage is optional and disabled by default
- ✓ All 46 original tests still passing (no regressions)
- ✓ 22 new S3 tests all passing (18 unit + 4 integration)
- ✓ Environment-based configuration (S3_ENABLED, S3_BUCKET, AWS_REGION, S3_PREFIX)
- ✓ No credentials embedded in code
- ✓ Mock-based testing (no real AWS calls)
- ✓ Health endpoint reports S3 status
- ✓ API response includes S3 metadata when enabled

**Evidence:**
- S3 storage module: `src/s3_storage.py` (279 lines, fully documented)
- S3 tests: `tests/test_s3_storage.py` (337 lines, 18 comprehensive tests)
- API integration: Modified `src/api.py` for S3 upload and health reporting
- API tests: Added 4 new S3 integration tests to `tests/test_api.py`
- Dependencies: boto3==1.34.39, botocore==1.34.162 added to requirements.txt
- Test results: 68/68 tests passing (13+19+18+18)
- Verified behavior: S3 disabled by default, local storage preserved, error handling tested
- Real-AWS integration test (2026-10-23):
  - ✓ Local FastAPI application with S3_ENABLED=true authenticated via boto3 credential chain
  - ✓ Processed 300-frame synthetic video; 1.753 seconds, 171.13 FPS
  - ✓ Five artifacts successfully uploaded to real S3 bucket (total 1,750,627 bytes)
  - ✓ S3 ListObjectsV2 verified objects at outputs/run_20261023_111911_e964dd98/
  - ✓ API response correctly reported s3_storage metadata with S3 URIs

**Known limitations (by design):**
- No EC2 instance deployment (NexusSpatialIntelligenceEC2Role not yet exercised)
- No automatic artifact deletion from S3
- No presigned URLs or artifact download endpoints
- S3 upload failure returns HTTP 500 (hard error, not silent)
- Distinction: Mock tests verify code logic; real-AWS test verifies live integration

### M5 — Evaluation and reproducibility

**Priority:** P0 · **Status:** Not verified

Tasks:
- Create a small test matrix covering normal activity, high activity, and at least one difficult case.
- Record input provenance, configuration, versions, number of processed frames, duration, and failures.
- Use reference labels if reporting accuracy; otherwise report descriptive metrics only.

Acceptance criteria:
- Results can be reproduced from written instructions.
- Limitations and failure cases are documented.

### M6 — Competition submission package

**Priority:** P0 · **Status:** Not verified

Tasks:
- Complete README and architecture diagram.
- Verify all setup/test/demo links from a clean checkout.
- Capture application evidence and measured results.
- Record a concise demo video within the official duration limit.
- Complete all required competition submission fields and submit before the verified deadline.

Acceptance criteria:
- Public reviewer-facing links work.
- The demonstration shows the actual application, meaningful OpenCV processing, relevant AWS functionality, and honest evaluation.
- Submission confirmation is saved.

## Explicitly deferred until required

- Complex frontend redesign.
- Multiple simultaneous use cases.
- Large model training or fine-tuning.
- Multi-agent orchestration, queues, databases, and distributed services without an identified need.
- Unsupported claims about people counting, accuracy, privacy, or safety.

## Reprioritization log

When a priority changes, record the date, reason, changed milestone, and consequence here; add a decision in `DECISIONS.md` if the change is architecturally significant.
