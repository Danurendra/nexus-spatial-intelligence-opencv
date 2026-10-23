#!/usr/bin/env python
"""API integration tests for Nexus Spatial Intelligence."""

import unittest
import tempfile
import json
from pathlib import Path
from io import BytesIO

from fastapi.testclient import TestClient
import cv2
import numpy as np
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api import create_app


class TestHealthEndpoint(unittest.TestCase):
    """Tests for GET /health endpoint."""
    
    @classmethod
    def setUpClass(cls):
        """Create test client."""
        cls.app = create_app()
        cls.client = TestClient(cls.app)
    
    def test_health_endpoint_returns_200(self):
        """Health endpoint should return 200."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
    
    def test_health_endpoint_structure(self):
        """Health response should contain required fields."""
        response = self.client.get("/health")
        data = response.json()
        
        self.assertIn("status", data)
        self.assertIn("service", data)
        self.assertIn("api_version", data)
        self.assertIn("opencv_version", data)
        
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "Nexus Spatial Intelligence")


class TestAnalyzeEndpoint(unittest.TestCase):
    """Tests for POST /analyze endpoint."""
    
    @classmethod
    def setUpClass(cls):
        """Create test client and test video."""
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        
        # Create temporary test video
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_video_path = Path(cls.temp_dir.name) / "test.mp4"
        cls.create_test_video(str(cls.test_video_path))
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files."""
        cls.temp_dir.cleanup()
    
    @staticmethod
    def create_test_video(output_path: str, num_frames: int = 30):
        """Create a simple test video."""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, 30, (320, 240))
        
        for i in range(num_frames):
            frame = np.ones((240, 320, 3), dtype=np.uint8) * (50 + i)
            # Add moving object
            x = int(50 + 100 * i / num_frames)
            cv2.rectangle(frame, (x, 50), (x+50, 150), (0, 255, 0), -1)
            writer.write(frame)
        writer.release()
    
    def test_analyze_valid_video_returns_200(self):
        """Valid video upload should return 200."""
        with open(self.test_video_path, "rb") as f:
            response = self.client.post(
                "/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        self.assertEqual(response.status_code, 200)
    
    def test_analyze_response_structure(self):
        """Response should contain required fields."""
        with open(self.test_video_path, "rb") as f:
            response = self.client.post(
                "/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check top-level structure
        self.assertIn("status", data)
        self.assertIn("run_id", data)
        self.assertIn("processing", data)
        self.assertIn("analysis", data)
        self.assertIn("artifacts", data)
        
        self.assertEqual(data["status"], "success")
    
    def test_analyze_includes_metrics(self):
        """Response should include motion metrics."""
        with open(self.test_video_path, "rb") as f:
            response = self.client.post(
                "/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check analysis metrics
        self.assertIn("metrics", data["analysis"])
        metrics = data["analysis"]["metrics"]
        
        self.assertIn("avg_foreground_percentage", metrics)
        self.assertIn("min_foreground_percentage", metrics)
        self.assertIn("max_foreground_percentage", metrics)
        self.assertIn("std_foreground_percentage", metrics)
    
    def test_analyze_includes_processing_info(self):
        """Response should include processing information."""
        with open(self.test_video_path, "rb") as f:
            response = self.client.post(
                "/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check processing info
        processing = data["processing"]
        self.assertIn("frames_processed", processing)
        self.assertIn("duration_seconds", processing)
        self.assertIn("fps_processed", processing)
        
        self.assertEqual(processing["frames_processed"], 30)
        self.assertGreater(processing["duration_seconds"], 0)
    
    def test_analyze_empty_file_rejected(self):
        """Empty file upload should be rejected."""
        response = self.client.post(
            "/analyze",
            files={"file": ("empty.mp4", BytesIO(b""), "video/mp4")}
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_analyze_invalid_file_type_rejected(self):
        """Invalid file type should be rejected."""
        response = self.client.post(
            "/analyze",
            files={"file": ("file.txt", BytesIO(b"not a video"), "text/plain")}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Unsupported", data["detail"])
    
    def test_analyze_empty_filename_rejected(self):
        """Empty filename should be rejected."""
        response = self.client.post(
            "/analyze",
            files={"file": ("", BytesIO(b"data"), "video/mp4")}
        )
        
        # FastAPI returns 422 for validation errors with empty filename
        self.assertIn(response.status_code, [400, 422])
    
    def test_analyze_invalid_video_rejected(self):
        """Invalid video file should be rejected."""
        invalid_video = BytesIO(b"This is not a valid video file")
        response = self.client.post(
            "/analyze",
            files={"file": ("invalid.mp4", invalid_video, "video/mp4")}
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_analyze_artifacts_in_response(self):
        """Response should include artifact references."""
        with open(self.test_video_path, "rb") as f:
            response = self.client.post(
                "/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        artifacts = data["artifacts"]
        self.assertIn("annotated_video", artifacts)
        self.assertIn("heatmap", artifacts)
    
    def test_analyze_run_id_format(self):
        """Run ID should follow expected format."""
        with open(self.test_video_path, "rb") as f:
            response = self.client.post(
                "/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        run_id = data["run_id"]
        
        # Run ID should start with "run_"
        self.assertTrue(run_id.startswith("run_"))


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling and edge cases."""
    
    @classmethod
    def setUpClass(cls):
        """Create test client."""
        cls.app = create_app()
        cls.client = TestClient(cls.app)
    
    def test_analyze_missing_file_parameter(self):
        """Request without file should return 422."""
        response = self.client.post("/analyze")
        self.assertEqual(response.status_code, 422)
    
    def test_api_version_is_semver(self):
        """API version should be semantic version."""
        response = self.client.get("/health")
        version = response.json()["api_version"]
        
        # Should be format x.y.z
        parts = version.split(".")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertTrue(part.isdigit())


class TestFileCleanup(unittest.TestCase):
    """Tests for temporary file cleanup."""
    
    @classmethod
    def setUpClass(cls):
        """Create test client and test video."""
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        
        # Create temporary test video
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_video_path = Path(cls.temp_dir.name) / "test.mp4"
        TestAnalyzeEndpoint.create_test_video(str(cls.test_video_path), num_frames=10)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files."""
        cls.temp_dir.cleanup()
    
    def test_temp_files_cleaned_on_success(self):
        """Temporary files should be cleaned up after successful analysis."""
        # This is difficult to test directly without mocking
        # but we can verify that the API doesn't crash due to cleanup issues
        with open(self.test_video_path, "rb") as f:
            response = self.client.post(
                "/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        self.assertEqual(response.status_code, 200)


class TestS3IntegrationAPI(unittest.TestCase):
    """Tests for S3 storage integration with the API."""
    
    @classmethod
    def setUpClass(cls):
        """Create test client and test video."""
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        
        # Create temporary test video
        cls.test_video_path = Path(tempfile.gettempdir()) / "test_s3_video.mp4"
        if not cls.test_video_path.exists():
            # Create synthetic video (30 frames, 320x240)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(cls.test_video_path), fourcc, 30.0, (320, 240))
            for i in range(30):
                frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
                writer.write(frame)
            writer.release()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test video."""
        if cls.test_video_path.exists():
            cls.test_video_path.unlink()
    
    def test_health_endpoint_includes_s3_status(self):
        """Health endpoint should include S3 storage status."""
        response = self.client.get("/health")
        data = response.json()
        
        self.assertIn("s3_storage_enabled", data)
        # Default is False (S3 disabled)
        self.assertFalse(data["s3_storage_enabled"])
    
    def test_analyze_response_includes_s3_storage_info(self):
        """Analyze response should include S3 storage information."""
        from unittest.mock import patch
        
        with open(self.test_video_path, "rb") as f:
            with patch.dict('os.environ', {'S3_ENABLED': 'false'}):
                response = self.client.post(
                    "/analyze",
                    files={"file": ("test.mp4", f, "video/mp4")}
                )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("s3_storage", data)
        self.assertFalse(data["s3_storage"]["enabled"])
    
    def test_analyze_with_s3_disabled_succeeds(self):
        """Analysis should succeed with S3 disabled (local storage only)."""
        with open(self.test_video_path, "rb") as f:
            response = self.client.post(
                "/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("run_id", data)
    
    def test_analyze_with_s3_upload_failure_returns_500(self):
        """Analysis should fail (500) if S3 upload fails."""
        from unittest.mock import patch, MagicMock
        
        with open(self.test_video_path, "rb") as f:
            # Mock S3 storage to fail on upload
            with patch('src.api.s3_storage') as mock_s3:
                mock_s3.upload_artifacts.return_value = {
                    "success": False,
                    "s3_enabled": True,
                    "uploaded_artifacts": {},
                    "local_artifacts": {},
                    "errors": ["S3 Access Denied"]
                }
                
                response = self.client.post(
                    "/analyze",
                    files={"file": ("test.mp4", f, "video/mp4")}
                )
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("S3 artifact upload failed", data.get("detail", ""))


def run_tests(verbosity=2):
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestHealthEndpoint))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyzeEndpoint))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestFileCleanup))
    suite.addTests(loader.loadTestsFromTestCase(TestS3IntegrationAPI))
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    exit_code = run_tests()
    sys.exit(exit_code)
