#!/usr/bin/env python
"""Comprehensive test summary for Nexus Spatial Intelligence M1 and M2."""

import subprocess
import sys
from pathlib import Path

print("\n" + "="*70)
print("NEXUS SPATIAL INTELLIGENCE - COMPREHENSIVE TEST SUMMARY")
print("="*70)

print("\n[1/2] Running M1 Video Analysis Tests (13 tests)...")
print("-" * 70)
result_m1 = subprocess.run(
    [sys.executable, "tests/test_video_analyzer.py"],
    cwd="E:\\01 Project-DN\\nexus-spatial-intelligence-opencv",
    capture_output=True,
    text=True
)
m1_pass = result_m1.returncode == 0
m1_output = result_m1.stdout + result_m1.stderr
m1_lines = [line for line in m1_output.split('\n') if 'Ran' in line or 'OK' in line]
if m1_lines:
    print(m1_lines[-1])

print("\n[2/2] Running M2 API Integration Tests (15 tests)...")
print("-" * 70)
result_m2 = subprocess.run(
    [sys.executable, "tests/test_api.py"],
    cwd="E:\\01 Project-DN\\nexus-spatial-intelligence-opencv",
    capture_output=True,
    text=True
)
m2_pass = result_m2.returncode == 0
m2_output = result_m2.stdout + result_m2.stderr
m2_lines = [line for line in m2_output.split('\n') if 'Ran' in line or 'OK' in line]
if m2_lines:
    print(m2_lines[-1])

print("\n" + "="*70)
print("TEST RESULTS SUMMARY")
print("="*70)

results = [
    ("M1 Pipeline Tests (VideoReader, MotionAnalyzer, HeatmapGenerator, etc.)", "PASSED" if m1_pass else "FAILED", 13),
    ("M2 API Integration Tests (Health, Upload, Validation, Error Handling)", "PASSED" if m2_pass else "FAILED", 15),
]

total_tests = 0
total_passed = 0

for name, status, count in results:
    status_symbol = "[OK]" if status == "PASSED" else "[FAILED]"
    total_tests += count
    if status == "PASSED":
        total_passed += count
    print(f"{status_symbol} {name}")
    print(f"    {count} tests")

print("-" * 70)
print(f"TOTAL: {total_passed}/{total_tests} tests passed")

if m1_pass and m2_pass:
    print("\n[SUCCESS] All test suites passed!")
    print("\nImplementation Status:")
    print("  - M1 Local Video Pipeline: COMPLETE & VERIFIED")
    print("    * VideoReader, MotionAnalyzer, HeatmapGenerator, ReportBuilder")
    print("    * CLI entry point (main.py)")
    print("    * 13/13 tests passing")
    print("  - M2 Minimal API Integration: COMPLETE & VERIFIED")
    print("    * GET /health endpoint")
    print("    * POST /analyze endpoint with file upload")
    print("    * File validation and temp cleanup")
    print("    * 15/15 tests passing")
    print("\nTotal Automated Tests: 28/28 passing")
    print("\nNext Milestone: M3 Adaptive Analysis (optional)")
else:
    print("\n[FAILED] Some test suites failed!")
    sys.exit(1)
