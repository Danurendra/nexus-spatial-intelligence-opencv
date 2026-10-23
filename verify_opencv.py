#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify OpenCV 5 installation and required features."""

import cv2
import numpy as np

print(f"OpenCV version: {cv2.__version__}")
print(f"NumPy version: {np.__version__}")

# Check for required CV2 attributes
features = {
    "CAP_PROP_FRAME_COUNT": hasattr(cv2, "CAP_PROP_FRAME_COUNT"),
    "CAP_PROP_FPS": hasattr(cv2, "CAP_PROP_FPS"),
    "CAP_PROP_FRAME_WIDTH": hasattr(cv2, "CAP_PROP_FRAME_WIDTH"),
    "CAP_PROP_FRAME_HEIGHT": hasattr(cv2, "CAP_PROP_FRAME_HEIGHT"),
    "VideoCapture": hasattr(cv2, "VideoCapture"),
    "VideoWriter": hasattr(cv2, "VideoWriter"),
    "createBackgroundSubtractorMOG2": hasattr(cv2, "createBackgroundSubtractorMOG2"),
    "cvtColor": hasattr(cv2, "cvtColor"),
    "applyColorMap": hasattr(cv2, "applyColorMap"),
}

print("\nRequired features:")
for feature, available in features.items():
    status = "[OK]" if available else "[MISSING]"
    print(f"  {status} {feature}")

all_available = all(features.values())
if all_available:
    print("\n[SUCCESS] All required OpenCV 5 features are available.")
else:
    print("\n[FAILED] Some features are missing.")
    exit(1)
