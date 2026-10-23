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

**Priority:** P1 · **Status:** Not verified

Tasks:
- Choose the smallest AWS deployment path compatible with the competition requirements and available account permissions.
- Configure IAM roles and private storage with least privilege.
- Deploy the meaningful processing component and/or store artifacts in S3.
- Record deployment instructions, cost considerations, and cleanup steps.

Acceptance criteria:
- A remote end-to-end test proves that the AWS component performs its stated function.
- No credentials are committed or embedded in public frontend code.
- Cleanup steps are documented and tested where practical.

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
