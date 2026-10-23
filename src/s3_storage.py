"""Optional S3 artifact storage for Nexus Spatial Intelligence.

Provides configurable S3 upload functionality with fallback to local storage.
Uses boto3 standard credential provider chain (no credentials embedded).
When S3 is disabled, all operations are no-ops (local artifacts retained).
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class S3StorageConfig:
    """Configuration for S3 storage."""
    
    def __init__(
        self,
        enabled: bool = False,
        bucket: str = "nexus-spatial-intelligence-896567473559",
        region: str = "ap-southeast-2",
        prefix: str = "outputs",
    ):
        """
        Initialize S3 storage configuration.
        
        Args:
            enabled: Whether to enable S3 upload (default: False for local storage)
            bucket: S3 bucket name
            region: AWS region
            prefix: S3 prefix for artifacts (e.g., "outputs/{run_id}/")
        """
        self.enabled = enabled
        self.bucket = bucket
        self.region = region
        self.prefix = prefix
    
    @staticmethod
    def from_env() -> "S3StorageConfig":
        """
        Create configuration from environment variables.
        
        Environment variables:
        - S3_ENABLED: "true" to enable S3 uploads (default: "false")
        - S3_BUCKET: S3 bucket name (default: nexus-spatial-intelligence-896567473559)
        - AWS_REGION: AWS region (default: ap-southeast-2)
        - S3_PREFIX: S3 prefix for artifacts (default: outputs)
        
        Returns:
            S3StorageConfig instance
        """
        enabled = os.getenv("S3_ENABLED", "false").lower() == "true"
        bucket = os.getenv("S3_BUCKET", "nexus-spatial-intelligence-896567473559")
        region = os.getenv("AWS_REGION", "ap-southeast-2")
        prefix = os.getenv("S3_PREFIX", "outputs")
        
        return S3StorageConfig(
            enabled=enabled,
            bucket=bucket,
            region=region,
            prefix=prefix,
        )


class S3StorageClient:
    """Handle S3 artifact uploads with fallback to local storage."""
    
    def __init__(self, config: S3StorageConfig):
        """
        Initialize S3 storage client.
        
        Args:
            config: S3StorageConfig instance
        """
        self.config = config
        self.s3_client = None
        self.upload_count = 0
        self.failed_uploads = []
        
        if config.enabled:
            try:
                import boto3
                self.s3_client = boto3.client("s3", region_name=config.region)
                logger.info(f"S3 storage enabled: s3://{config.bucket}/{config.prefix}/")
            except ImportError:
                logger.error("boto3 not installed; S3 uploads disabled. Install with: pip install boto3")
                self.config.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}; S3 uploads disabled")
                self.config.enabled = False
    
    def upload_artifacts(
        self,
        run_id: str,
        output_dir: Path,
        artifact_filenames: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Upload artifacts to S3 or record local paths.
        
        Args:
            run_id: Unique run identifier
            output_dir: Directory containing generated artifacts
            artifact_filenames: Optional list of filenames to upload. If None, uploads all files in output_dir.
        
        Returns:
            Dictionary with:
            - 'success': True if all uploads succeeded (or S3 disabled)
            - 's3_enabled': Whether S3 storage is enabled
            - 'uploaded_artifacts': Dict mapping filename to S3 URI (if S3 enabled and successful)
            - 'local_artifacts': Dict mapping filename to local path
            - 'errors': List of upload errors (if any)
        """
        result = {
            "success": True,
            "s3_enabled": self.config.enabled,
            "uploaded_artifacts": {},
            "local_artifacts": {},
            "errors": [],
        }
        
        # Determine which files to process
        if artifact_filenames is None:
            # Upload all files in output directory
            artifact_filenames = [f.name for f in Path(output_dir).glob("*") if f.is_file()]
        
        # Build local artifact paths
        for filename in artifact_filenames:
            artifact_path = Path(output_dir) / filename
            if artifact_path.exists():
                local_path = str(artifact_path.relative_to(output_dir.parent))
                result["local_artifacts"][filename] = local_path
        
        # If S3 is disabled, return local paths only
        if not self.config.enabled:
            logger.info(f"S3 storage disabled; artifacts retained locally in {output_dir}")
            return result
        
        # Upload to S3
        for filename in artifact_filenames:
            artifact_path = Path(output_dir) / filename
            if not artifact_path.exists():
                logger.warning(f"Artifact file not found: {filename}")
                result["errors"].append(f"File not found: {filename}")
                result["success"] = False
                continue
            
            s3_key = f"{self.config.prefix}/{run_id}/{filename}"
            
            try:
                logger.info(f"Uploading {filename} to s3://{self.config.bucket}/{s3_key}")
                
                # Upload without ACL (bucket uses bucket-owner-enforced ACL mode)
                self.s3_client.upload_file(
                    str(artifact_path),
                    self.config.bucket,
                    s3_key,
                )
                
                s3_uri = f"s3://{self.config.bucket}/{s3_key}"
                result["uploaded_artifacts"][filename] = s3_uri
                self.upload_count += 1
                logger.info(f"Successfully uploaded: {s3_uri}")
                
            except Exception as e:
                error_msg = f"Failed to upload {filename}: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["success"] = False
                self.failed_uploads.append((filename, str(e)))
        
        return result
    
    def get_artifact_s3_uri(self, run_id: str, filename: str) -> str:
        """
        Generate S3 URI for an artifact.
        
        Args:
            run_id: Unique run identifier
            filename: Artifact filename
        
        Returns:
            S3 URI string (or local path if S3 disabled)
        """
        if not self.config.enabled:
            return filename
        
        s3_key = f"{self.config.prefix}/{run_id}/{filename}"
        return f"s3://{self.config.bucket}/{s3_key}"
    
    def is_enabled(self) -> bool:
        """Check if S3 storage is enabled."""
        return self.config.enabled
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get upload statistics.
        
        Returns:
            Dictionary with upload stats
        """
        return {
            "s3_enabled": self.config.enabled,
            "total_uploads": self.upload_count,
            "failed_uploads": len(self.failed_uploads),
            "failed_files": [f[0] for f in self.failed_uploads],
        }


def create_s3_storage_client(config: Optional[S3StorageConfig] = None) -> S3StorageClient:
    """
    Create S3 storage client with optional configuration.
    
    Args:
        config: Optional S3StorageConfig. If None, loads from environment variables.
    
    Returns:
        S3StorageClient instance
    """
    if config is None:
        config = S3StorageConfig.from_env()
    
    return S3StorageClient(config)
