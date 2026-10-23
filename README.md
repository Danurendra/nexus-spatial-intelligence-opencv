# Nexus Spatial Intelligence

**Adaptive video analytics with OpenCV 5 and AWS S3.**

Nexus Spatial Intelligence transforms uploaded video into structured spatial activity insights. It measures foreground motion, generates spatial heatmaps, applies a deterministic adaptive-refinement policy, and provides evidence-grounded recommendations through a local web interface.

The video-processing workload currently runs locally. Optional artifact storage has been tested against a real private Amazon S3 bucket; deployment of the processing backend to EC2 has **not** been performed.

## Project status

The project implements five milestones:

- **M1 — Local video pipeline:** video metadata, MOG2 foreground-motion metrics, annotated video, heatmaps, and JSON reports.
- **M2 — FastAPI:** health and video-analysis endpoints, input validation, and error handling.
- **M3 — Adaptive analysis:** a deterministic policy can trigger a follow-up analysis using a finer 16×16 grid when average foreground activity is below a configurable threshold. The baseline grid is 8×8.
- **M4 — Optional S3 storage:** generated artifacts can be uploaded to a private S3 bucket when enabled through environment configuration.
- **M5 — Vision Agent and GUI:** an evidence-grounded recommendation layer records observations, decisions, actions, follow-up results, and recommendations. A single-page browser interface displays the analysis.

The latest reported automated test result is **81/81 passing**. Re-run the test suite in your environment to verify the current checkout.

## What the application measures

Nexus currently uses OpenCV MOG2 background subtraction to estimate foreground activity. It reports the percentage of pixels classified as foreground and summarizes activity spatially with heatmaps.

The adaptive policy compares the observed average foreground percentage against a configurable threshold (default: 5.0%). When the condition is met, the system performs a follow-up analysis with a 16×16 grid; otherwise, it keeps the baseline 8×8 result. The decision and its supporting metrics are recorded in a structured trace.

The Vision Agent produces recommendations from measured values, the policy decision, and available analysis artifacts. It does not claim facts that are not supported by the analysis.

### Important limitations

- This is a **foreground-motion analysis** system, not a person detector.
- It does not identify people, recognize faces, infer identity, or establish that a threat or dangerous event exists.
- It processes uploaded videos offline; it is not a real-time surveillance system.
- A 16×16 heatmap offers finer spatial granularity than an 8×8 heatmap. This alone does not demonstrate improved accuracy.
- No supervised accuracy claim is made because a labeled ground-truth evaluation dataset has not been established.

## Architecture overview

```text
Browser GUI
    |
    | upload video
    v
FastAPI (/analyze)
    |
    v
OpenCV 5 video pipeline
    |  MOG2 foreground-motion metrics
    |  baseline 8x8 heatmap
    v
Adaptive policy / Vision Agent
    |-- threshold not met --> keep baseline result
    |
    `-- threshold met ------> follow-up 16x16 spatial analysis
    |
    v
Recommendation + decision trace + artifacts
    |
    | optional, when S3_ENABLED=true
    v
Private Amazon S3 bucket
```

## Quick start

### Requirements

- Python 3.12 or later is recommended.
- Git.
- Windows PowerShell instructions are shown below. Linux/macOS may require adjustments to activation commands and test-runner paths; those platforms have not been independently verified here.

### 1. Clone and install

```powershell
git clone https://github.com/Danurendra/nexus-spatial-intelligence-opencv.git
cd nexus-spatial-intelligence-opencv

python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python verify_opencv.py
```

If PowerShell blocks activation for the current terminal session, you can use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 2. Run the automated tests

With the virtual environment active, run:

```powershell
python run_all_tests.py
```

The previously verified suite contains 81 tests across the M1–M5 components. The expected final count is 81/81, but use the output from your own run as the actual result. Automated S3 tests use mocks and do not require AWS credentials or make real S3 writes.

### 3. Start the web application

From the repository root, with the virtual environment active:

```powershell
python src/server.py
```

Open the GUI at:

<http://localhost:8000/ui/>

The API health endpoint is available at:

<http://localhost:8000/health>

In the GUI:

1. Upload a supported video file.
2. Start the analysis.
3. Review the motion metrics and baseline 8×8 heatmap.
4. Inspect the adaptive decision and follow-up 16×16 heatmap when generated.
5. Review the recommendation and expandable decision trace.
6. Check the reported S3 storage status.

The API validates the uploaded file and applies a maximum upload size. The current GUI indicates a 100 MB limit; actual acceptance is determined by the server-side validation.

### 4. Run the command-line pipeline

Provide a local video file that exists on your machine:

```powershell
python src/main.py path\to\video.mp4 --adaptive-threshold 5.0
```

Generated artifacts are written under `artifacts/{run_id}/`, including applicable annotated video, heatmaps, report JSON, and run metadata.

## Optional Amazon S3 storage

S3 storage is disabled by default. Local artifact storage remains the default when S3 is not enabled.

To enable S3 upload for the current PowerShell session, configure the application environment before starting the server:

```powershell
$env:S3_ENABLED = "true"
$env:S3_BUCKET = "your-private-bucket-name"
$env:AWS_REGION = "your-aws-region"
$env:S3_PREFIX = "outputs"
```

Boto3 uses its standard credential provider chain. Do not put access keys, secret keys, session tokens, or credential files into source code or the public repository. Configure AWS authentication using an appropriate local AWS CLI profile or an IAM role in a supported AWS runtime.

When enabled, successful analyses upload generated artifacts under a run-specific prefix similar to:

```text
s3://your-private-bucket-name/outputs/{run_id}/
```

The bucket used in the recorded integration test is private. An `s3://` URI is an object identifier, not a public browser URL.

### Verified real-S3 test

On 2026-10-23, the local FastAPI application processed `videos/test_synthetic.mp4` (300 frames) in approximately 1.753 seconds and reported approximately 171.13 FPS for that run. A subsequent real S3 `ListObjectsV2` request confirmed five uploaded artifacts:

- `annotated_video.mp4` — 1,534,866 bytes
- `heatmap.png` — 107,793 bytes
- `heatmap_followup_16x16.png` — 103,975 bytes
- `report.json` — 3,563 bytes
- `run_metadata.json` — 430 bytes

These measurements describe one synthetic-video test in the local environment, not a general performance benchmark. The S3 integration was verified, but the processing backend has not been deployed to EC2 and the EC2 instance role has not been tested on an instance.

## Verification utilities

Run these from the repository root with the virtual environment active:

```powershell
python verify_opencv.py
python run_all_tests.py
python verify_gui_and_api.py
python M5_IMPLEMENTATION_REPORT.py
```

`verify_gui_and_api.py` checks the API and GUI-related behavior. `M5_IMPLEMENTATION_REPORT.py` demonstrates both deterministic agent decision branches. Review each script before running it in an environment where real resources or credentials might be configured.

## Security and responsible use

- Do not commit AWS credentials, tokens, `.env` files, or local credential files.
- Keep the S3 bucket private; this project does not require public object ACLs.
- The artifact endpoint uses run-ID validation and an allowlist of generated artifact names.
- Treat heatmaps and recommendations as summaries of foreground motion, not proof of a person's presence, identity, intent, or a threat.
- Inspect the evidence and limitations before making operational decisions from an analysis result.

## Project structure

```text
nexus-spatial-intelligence-opencv/
├── docs/                  # Architecture, decisions, roadmap, status, handoff
├── src/
│   ├── main.py            # Command-line pipeline
│   ├── video_analyzer.py  # Core OpenCV analysis
│   ├── adaptive_analysis.py # M3 adaptive policy and trace
│   ├── api.py             # FastAPI endpoints and GUI serving
│   ├── server.py          # Server entry point
│   ├── s3_storage.py      # Optional S3 artifact storage
│   └── vision_agent.py    # Evidence-grounded recommendations
├── ui/
│   ├── index.html         # Browser interface
│   └── app.js             # Client-side behavior
├── tests/                 # Automated test suites
├── requirements.txt       # Python dependencies
├── run_all_tests.py       # Combined test runner
└── verify_opencv.py       # OpenCV verification script
```

## Technologies

| Component | Technology |
|---|---|
| Computer vision | OpenCV 5 / MOG2 |
| API server | FastAPI, Uvicorn |
| Adaptive orchestration | Python deterministic policy and Vision Agent |
| Artifact storage | Amazon S3 via Boto3 (optional) |
| Interface | HTML, CSS, JavaScript |
| Automated tests | Python `unittest` and mocks |

## Repository and project documentation

- **Source repository:** <https://github.com/Danurendra/nexus-spatial-intelligence-opencv>
- `docs/ARCHITECTURE.md` — system design and data flow
- `docs/DECISIONS.md` — technical decisions and rationale
- `docs/STATUS.md` — verification status
- `docs/ROADMAP.md` — milestone plan
- `docs/SESSION_HANDOFF.md` — current project handoff

Built for the OpenCV AI Competition 2026, powered by AWS.
