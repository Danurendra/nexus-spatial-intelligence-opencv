#!/usr/bin/env python
"""M4 S3 Storage Tests for Nexus Spatial Intelligence.

Tests S3 artifact upload functionality using moto mocks (no real AWS calls).
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.s3_storage import S3StorageConfig, S3StorageClient, create_s3_storage_client


class TestS3StorageConfig(unittest.TestCase):
    """Tests for S3StorageConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = S3StorageConfig()
        self.assertFalse(config.enabled)
        self.assertEqual(config.bucket, "nexus-spatial-intelligence-896567473559")
        self.assertEqual(config.region, "ap-southeast-2")
        self.assertEqual(config.prefix, "outputs")
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = S3StorageConfig(
            enabled=True,
            bucket="test-bucket",
            region="us-east-1",
            prefix="test-prefix"
        )
        self.assertTrue(config.enabled)
        self.assertEqual(config.bucket, "test-bucket")
        self.assertEqual(config.region, "us-east-1")
        self.assertEqual(config.prefix, "test-prefix")
    
    @patch.dict('os.environ', {
        'S3_ENABLED': 'true',
        'S3_BUCKET': 'env-bucket',
        'AWS_REGION': 'eu-west-1',
        'S3_PREFIX': 'env-prefix'
    })
    def test_config_from_env(self):
        """Test configuration from environment variables."""
        config = S3StorageConfig.from_env()
        self.assertTrue(config.enabled)
        self.assertEqual(config.bucket, 'env-bucket')
        self.assertEqual(config.region, 'eu-west-1')
        self.assertEqual(config.prefix, 'env-prefix')
    
    @patch.dict('os.environ', {}, clear=True)
    def test_config_from_env_defaults(self):
        """Test configuration from environment with defaults."""
        config = S3StorageConfig.from_env()
        self.assertFalse(config.enabled)
        self.assertEqual(config.bucket, "nexus-spatial-intelligence-896567473559")
        self.assertEqual(config.region, "ap-southeast-2")


class TestS3StorageClientDisabled(unittest.TestCase):
    """Tests for S3StorageClient with S3 disabled."""
    
    @classmethod
    def setUpClass(cls):
        """Create disabled S3 client."""
        config = S3StorageConfig(enabled=False)
        cls.client = S3StorageClient(config)
    
    def test_s3_disabled_initialization(self):
        """Test that client initializes with S3 disabled."""
        self.assertFalse(self.client.is_enabled())
        self.assertIsNone(self.client.s3_client)
    
    def test_upload_with_s3_disabled(self):
        """Test upload returns local paths when S3 is disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test artifacts
            (temp_path / "test_artifact.txt").write_text("test content")
            (temp_path / "test_video.mp4").write_text("mock video")
            
            result = self.client.upload_artifacts(
                run_id="test_run_123",
                output_dir=temp_path,
                artifact_filenames=["test_artifact.txt", "test_video.mp4"]
            )
            
            self.assertTrue(result["success"])
            self.assertFalse(result["s3_enabled"])
            self.assertEqual(len(result["uploaded_artifacts"]), 0)
            self.assertEqual(len(result["local_artifacts"]), 2)
            self.assertEqual(len(result["errors"]), 0)
    
    def test_s3_disabled_stats(self):
        """Test stats when S3 is disabled."""
        stats = self.client.get_stats()
        self.assertFalse(stats["s3_enabled"])
        self.assertEqual(stats["total_uploads"], 0)


class TestS3StorageClientEnabled(unittest.TestCase):
    """Tests for S3StorageClient with S3 enabled (using mocks)."""
    
    def test_s3_client_initialization_with_boto3(self):
        """Test client initializes successfully with boto3 available."""
        config = S3StorageConfig(enabled=True)
        # boto3 is already installed, so this should work
        client = S3StorageClient(config)
        self.assertTrue(client.config.enabled)
        self.assertIsNotNone(client.s3_client)
    
    def test_s3_client_initialization_success(self):
        """Test client initialization with boto3 available."""
        config = S3StorageConfig(enabled=True)
        client = S3StorageClient(config)
        self.assertTrue(client.config.enabled)
        self.assertIsNotNone(client.s3_client)
    
    def test_upload_artifacts_success(self):
        """Test successful artifact upload."""
        config = S3StorageConfig(
            enabled=True,
            bucket="test-bucket",
            region="ap-southeast-2",
            prefix="outputs"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test artifacts
            (temp_path / "heatmap.png").write_text("mock image data")
            (temp_path / "report.json").write_text('{"status": "complete"}')
            
            # Create real client (boto3 is installed)
            client = S3StorageClient(config)
            
            # Mock the S3 upload method
            with patch.object(client.s3_client, 'upload_file') as mock_upload:
                result = client.upload_artifacts(
                    run_id="run_12345",
                    output_dir=temp_path,
                    artifact_filenames=["heatmap.png", "report.json"]
                )
                
                self.assertTrue(result["success"])
                self.assertTrue(result["s3_enabled"])
                self.assertEqual(len(result["uploaded_artifacts"]), 2)
                self.assertIn("heatmap.png", result["uploaded_artifacts"])
                self.assertIn("report.json", result["uploaded_artifacts"])
                self.assertEqual(len(result["errors"]), 0)
                
                # Verify S3 upload was called for each artifact
                self.assertEqual(mock_upload.call_count, 2)
    
    def test_upload_artifacts_with_s3_error(self):
        """Test upload failure handling."""
        config = S3StorageConfig(enabled=True, bucket="test-bucket")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "artifact.txt").write_text("data")
            
            client = S3StorageClient(config)
            
            # Mock S3 upload to fail
            with patch.object(client.s3_client, 'upload_file', side_effect=Exception("Access Denied")):
                result = client.upload_artifacts(
                    run_id="run_456",
                    output_dir=temp_path,
                    artifact_filenames=["artifact.txt"]
                )
                
                self.assertFalse(result["success"])
                self.assertTrue(result["s3_enabled"])
                self.assertEqual(len(result["uploaded_artifacts"]), 0)
                self.assertGreater(len(result["errors"]), 0)
    
    def test_upload_missing_artifact(self):
        """Test upload with missing artifact file."""
        config = S3StorageConfig(enabled=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            client = S3StorageClient(config)
            
            result = client.upload_artifacts(
                run_id="run_789",
                output_dir=temp_path,
                artifact_filenames=["nonexistent.txt"]
            )
            
            self.assertFalse(result["success"])
            self.assertGreater(len(result["errors"]), 0)
    
    def test_get_artifact_s3_uri(self):
        """Test S3 URI generation."""
        config = S3StorageConfig(
            enabled=True,
            bucket="my-bucket",
            prefix="outputs"
        )
        
        client = S3StorageClient(config)
        
        uri = client.get_artifact_s3_uri("run_123", "heatmap.png")
        self.assertEqual(uri, "s3://my-bucket/outputs/run_123/heatmap.png")
    
    def test_get_artifact_uri_when_disabled(self):
        """Test URI generation when S3 is disabled."""
        config = S3StorageConfig(enabled=False)
        client = S3StorageClient(config)
        
        uri = client.get_artifact_s3_uri("run_123", "heatmap.png")
        self.assertEqual(uri, "heatmap.png")


class TestS3StorageClientFactory(unittest.TestCase):
    """Tests for S3 storage client factory."""
    
    @patch.dict('os.environ', {}, clear=True)
    def test_create_client_from_env_disabled(self):
        """Test factory creates disabled client by default."""
        client = create_s3_storage_client()
        self.assertFalse(client.is_enabled())
    
    @patch.dict('os.environ', {'S3_ENABLED': 'true'})
    def test_create_client_from_env_enabled(self):
        """Test factory creates enabled client from env."""
        client = create_s3_storage_client()
        self.assertTrue(client.is_enabled())
    
    def test_create_client_with_custom_config(self):
        """Test factory accepts custom config."""
        config = S3StorageConfig(enabled=False, bucket="custom-bucket")
        client = create_s3_storage_client(config)
        self.assertFalse(client.is_enabled())
        self.assertEqual(client.config.bucket, "custom-bucket")


class TestS3StorageStats(unittest.TestCase):
    """Tests for S3 storage statistics."""
    
    def test_stats_tracking(self):
        """Test upload statistics are tracked."""
        config = S3StorageConfig(enabled=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "file1.txt").write_text("data1")
            
            client = S3StorageClient(config)
            
            # Mock S3 upload
            with patch.object(client.s3_client, 'upload_file') as mock_upload:
                # Successful upload
                client.upload_artifacts("run_1", temp_path, ["file1.txt"])
                
                stats = client.get_stats()
                self.assertTrue(stats["s3_enabled"])
                self.assertEqual(stats["total_uploads"], 1)
                self.assertEqual(stats["failed_uploads"], 0)


def run_tests():
    """Run M4 S3 storage tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestS3StorageConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestS3StorageClientDisabled))
    suite.addTests(loader.loadTestsFromTestCase(TestS3StorageClientEnabled))
    suite.addTests(loader.loadTestsFromTestCase(TestS3StorageClientFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestS3StorageStats))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
