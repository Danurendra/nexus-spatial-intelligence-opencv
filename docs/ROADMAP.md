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

**Priority:** P1 · **Status:** Not verified

Tasks:
- Add a health endpoint and one video-analysis endpoint if the HTTP workflow is useful.
- Add input validation, upload limits, safe paths, logging, and cleanup.
- Test valid and invalid requests.

Acceptance criteria:
- A client can submit a supported video and receive a truthful report.
- Invalid inputs fail safely and predictably.

### M3 — Adaptive analysis and decision trace

**Priority:** P1 · **Status:** Not verified

Tasks:
- Define a measurable condition based on the first visual result.
- Implement a bounded follow-up action, such as additional sampling in a selected region.
- Record observation, decision, action, reanalysis result, and final status.
- Compare the adaptive path with a simple baseline.

Acceptance criteria:
- The next action demonstrably changes when the initial observation changes.
- Tests verify both the action-triggered and non-triggered cases.
- Any claimed benefit is supported by observed results.

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
