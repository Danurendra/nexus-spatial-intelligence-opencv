#!/usr/bin/env python
"""Manual test of API endpoints using requests."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from src.api import create_app

print("Creating test client...")
app = create_app()
client = TestClient(app)

print("\n" + "="*60)
print("TEST 1: Health Endpoint")
print("="*60)

response = client.get("/health")
print(f"Status: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")

assert response.status_code == 200
assert response.json()["status"] == "healthy"
print("[OK] PASSED")

print("\n" + "="*60)
print("TEST 2: Analyze Endpoint with Synthetic Video")
print("="*60)

# Create test video first
import tempfile
import cv2
import numpy as np

temp_dir = tempfile.mkdtemp()
test_video_path = Path(temp_dir) / "test.mp4"

# Generate test video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
writer = cv2.VideoWriter(str(test_video_path), fourcc, 30, (320, 240))
for i in range(30):
    frame = np.ones((240, 320, 3), dtype=np.uint8) * (50 + i)
    x = int(50 + 100 * i / 30)
    cv2.rectangle(frame, (x, 50), (x+50, 150), (0, 255, 0), -1)
    writer.write(frame)
writer.release()

print(f"Created test video: {test_video_path}")

# Upload and analyze
with open(test_video_path, "rb") as f:
    response = client.post(
        "/analyze",
        files={"file": ("test.mp4", f, "video/mp4")}
    )

print(f"Status: {response.status_code}")
data = response.json()
print(f"Response:\n{json.dumps(data, indent=2)}")

assert response.status_code == 200
assert data["status"] == "success"
assert "run_id" in data
assert "processing" in data
assert "analysis" in data
print("[OK] PASSED")

print("\n" + "="*60)
print("TEST 3: Invalid File Type Rejection")
print("="*60)

response = client.post(
    "/analyze",
    files={"file": ("test.txt", b"not a video", "text/plain")}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

assert response.status_code == 400
print("[OK] PASSED")

print("\n" + "="*60)
print("TEST 4: Invalid Video File Rejection")
print("="*60)

response = client.post(
    "/analyze",
    files={"file": ("invalid.mp4", b"not really a video", "video/mp4")}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

assert response.status_code == 400
print("[OK] PASSED")

# Cleanup
import shutil
shutil.rmtree(temp_dir)

print("\n" + "="*60)
print("ALL TESTS PASSED [OK]")
print("="*60)
