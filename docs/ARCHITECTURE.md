# Architecture — Nexus Spatial Intelligence

**Document status:** M1 and M2 are IMPLEMENTED and VERIFIED. M3-M6 remain proposed.

## 1. Product goal

Nexus Spatial Intelligence analyzes short video clips to produce spatially organized visual evidence—such as motion/foreground activity by region, an activity heatmap, annotated frames/video, and a structured report. The system should communicate what it actually measures and should not equate foreground motion with an accurate count of people.

## 2. Current implementation status

**MILESTONE 1 — VERIFIED COMPLETE**
- ✓ Local video-analysis pipeline using OpenCV 5.0.0
- ✓ VideoReader, MotionAnalyzer, HeatmapGenerator, ReportBuilder classes
- ✓ CLI entry point (main.py) for end-to-end processing
- ✓ 13 automated tests

**MILESTONE 2 — VERIFIED COMPLETE**
- ✓ FastAPI service (api.py) with GET /health and POST /analyze
- ✓ File upload validation (type, size, content)
- ✓ Safe temporary file handling with cleanup
- ✓ JSON response with run ID, metrics, artifact references
- ✓ Server entry point (server.py) for development
- ✓ 15 automated API tests

**Remaining components are PROPOSED, not yet implemented:**
- Optional AWS-backed execution and object storage (M4).
- Optional adaptive analysis loop whose next action depends on the first visual result (M3).
- Evaluation harness and performance benchmarking (M5).
- Competition submission package (M6).

## 3. Proposed MVP components

| Component | Responsibility | Initial boundary |
|---|---|---|
| Input validation | Check file type, size, readability, and processing limits | Reject invalid input before analysis |
| Video reader | Read metadata and frames using OpenCV | No business logic in the HTTP layer |
| Spatial analysis | Apply configured ROIs and calculate documented motion/foreground indicators | Deterministic baseline before complex models |
| Artifact writer | Produce annotated frame/video, heatmap, JSON report, and run metadata | Every artifact must correspond to the same run |
| API layer | Expose health and video-analysis endpoints | Thin wrapper around the pipeline |
| Local artifact storage | Store temporary inputs and generated results | Keep generated artifacts outside source files |
| AWS adapter (later milestone) | Store selected inputs/results in S3 and/or run processing on AWS compute | Add only after local flow works; least privilege |
| Evaluation harness | Run repeatable test cases and measure outputs/time | Report limitations and avoid unsupported accuracy claims |
| UI (optional MVP extension) | Upload a clip and display outputs | Do not block the pipeline on elaborate UI work |

## 4. Proposed data flow

```text
User / test client
       |
       v
Input validation (type, size, path, readability)
       |
       v
Video reader (OpenCV 5) -----> video metadata
       |
       v
Frame sampling / ROI configuration
       |
       v
Motion or foreground analysis
       |
       +------> annotated frames / video
       +------> spatial activity heatmap
       +------> region-level measurements
       |
       v
Report builder
       |
       +------> report.json
       +------> run_metadata.json
       +------> artifact references
       |
       v
API response / local UI
```

A later adaptive-analysis path may extend the flow:

```text
Initial visual result -> evaluate explicit condition -> select a bounded follow-up
             -> analyze selected frames/regions -> compare results -> record decision trace
```

This path counts as adaptive/agentic behavior only when the first result demonstrably affects the next action. A static sequence with a fixed second pass is not sufficient evidence of such behavior.

## 5. Proposed interfaces

Exact paths and schemas are to be confirmed during implementation. Suggested minimal API:

- `GET /health` — reports whether the service is running.
- `POST /analyze` — accepts one video, validates it, runs analysis, and returns status, measured results, warnings, and artifact references.
- Artifact retrieval endpoint — add only if needed by the UI; constrain it to generated artifact IDs/paths rather than arbitrary filesystem paths.

Suggested report fields:

- Run ID and processing status.
- Input filename (avoid exposing an unsafe original path).
- Video dimensions, FPS, and frame count when available.
- Number of frames processed and sampling strategy.
- ROI definitions and analysis configuration.
- Precisely defined motion/foreground metrics.
- Processing duration and warnings/errors.
- Output artifact names/identifiers.
- Software versions and relevant environment metadata.

Do not fabricate unavailable metadata; represent missing fields explicitly.

## 6. Proposed technology choices

- **Language:** Python.
- **Computer vision:** OpenCV 5, with the runtime version verified directly.
- **API:** FastAPI, if an HTTP interface is needed for the MVP.
- **Packaging:** a Python virtual environment first; Docker where reproducibility or deployment needs it.
- **Cloud:** AWS only when the specific service and purpose are documented. An early deployment may use EC2 for application execution and S3 for object storage, subject to available account permissions and budget.
- **Frontend:** optional. Choose or retain a frontend only after inspecting what exists in this repository.

These choices are initial defaults, not irreversible commitments. Record material changes in `DECISIONS.md`.

## 7. Security, privacy, and operations

- Enforce upload size/type limits and use generated safe filenames.
- Do not execute user-supplied paths or expose arbitrary filesystem reads.
- Remove temporary data when appropriate and document artifact retention.
- Keep S3 private by default; use least-privilege IAM and avoid embedding credentials in code or frontend bundles.
- Use synthetic or openly licensed video for tests; record provenance and licensing.
- Avoid uploading identifiable footage without an appropriate lawful basis and clear handling rules.
- Record failure state and processing time; do not silently turn failures into apparently valid results.
- Check AWS resource cost and shut down unused resources when testing is complete.

## 8. Observability and evaluation

For each test run, capture the input identifier, settings, software version, number of frames processed, elapsed time, artifact paths, and errors. Compare output with manually labeled reference data when claiming accuracy. Without labeled reference data, report descriptive measurements and qualitative limitations rather than accuracy scores.

## 9. Open questions

- What video sources and licenses will be used?
- Which exact spatial metric is the product's primary output?
- Is person detection required, or is motion/foreground occupancy sufficient?
- Which AWS service will run computation, and which will store artifacts?
- What retention policy applies to uploaded videos and outputs?
- What rubric-specific integration or submission evidence is required?

Resolve questions when implementation makes them material; record consequential choices in `DECISIONS.md`.
