"""S3/MinIO utility functions for file storage operations."""

import os
from pathlib import Path
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from loguru import logger


class S3Storage:
    """S3-compatible storage client for file operations."""
    
    def __init__(self):
        """Initialize S3 client with credentials from environment."""
        load_dotenv()
        
        self.endpoint = os.getenv("S3_ENDPOINT")
        self.access_key = os.getenv("S3_ACCESS_KEY")
        self.secret_key = os.getenv("S3_SECRET_KEY")
        self.bucket = os.getenv("S3_BUCKET", "dev")
        self.region = os.getenv("S3_REGION", "us-east-1")
        
        if not all([self.endpoint, self.access_key, self.secret_key]):
            raise ValueError("Missing required S3 credentials in environment")
        
        # Ensure endpoint has protocol
        if not self.endpoint.startswith(("http://", "https://")):
            self.endpoint = f"http://{self.endpoint}"
        
        # Create S3 client
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            use_ssl=False if self.endpoint.startswith("http://") else True,
            verify=False
        )
    
    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """
        Upload a file to S3.
        
        Args:
            local_path: Path to local file
            s3_key: S3 object key (path in bucket)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            local_file = Path(local_path)
            if not local_file.exists():
                logger.error(f"File not found: {local_path}")
                return False
            
            logger.info(f"Uploading {local_file} to s3://{self.bucket}/{s3_key}")
            self.client.upload_file(str(local_file), self.bucket, s3_key)
            logger.success("Upload successful")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return False
    
    def upload_directory(self, local_dir: str, s3_prefix: str) -> int:
        """
        Upload entire directory to S3.
        
        Args:
            local_dir: Path to local directory
            s3_prefix: S3 prefix for uploaded files
        
        Returns:
            Number of files uploaded successfully
        """
        local_path = Path(local_dir)
        if not local_path.exists() or not local_path.is_dir():
            logger.error(f"Directory not found: {local_dir}")
            return 0
        
        uploaded = 0
        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_path)
                s3_key = f"{s3_prefix}/{relative_path}".replace("\\", "/")
                if self.upload_file(str(file_path), s3_key):
                    uploaded += 1
        
        logger.info(f"Uploaded {uploaded} files from {local_dir}")
        return uploaded
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3.
        
        Args:
            s3_key: S3 object key
            local_path: Path to save file locally
        
        Returns:
            True if successful, False otherwise
        """
        try:
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Downloading s3://{self.bucket}/{s3_key} to {local_file}")
            self.client.download_file(self.bucket, s3_key, str(local_file))
            logger.success("Download successful")
            return True
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.error(f"Object not found: {s3_key}")
            else:
                logger.error(f"Failed to download file: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in S3 bucket with optional prefix.
        
        Args:
            prefix: S3 prefix to filter objects
        
        Returns:
            List of S3 object keys
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            if "Contents" not in response:
                return []
            
            return [obj["Key"] for obj in response["Contents"]]
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError:
            return False
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"Deleted s3://{self.bucket}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def create_folder(self, folder_path: str) -> bool:
        """
        Create a folder in S3 (creates empty object with trailing slash).
        
        Args:
            folder_path: Folder path in S3
        
        Returns:
            True if successful, False otherwise
        """
        if not folder_path.endswith("/"):
            folder_path += "/"
        
        try:
            self.client.put_object(Bucket=self.bucket, Key=folder_path, Body=b"")
            logger.info(f"Created folder: s3://{self.bucket}/{folder_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create folder: {e}")
            return False
    
    def get_file_info(self, s3_key: str) -> Optional[dict]:
        """
        Get metadata for S3 object.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Dict with file metadata or None if not found
        """
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return {
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "etag": response["ETag"],
                "content_type": response.get("ContentType", "unknown")
            }
        except ClientError:
            return None


# Convenience functions for direct use
def upload_to_s3(local_path: str, s3_key: str) -> bool:
    """Upload a file to S3."""
    storage = S3Storage()
    return storage.upload_file(local_path, s3_key)


def download_from_s3(s3_key: str, local_path: str) -> bool:
    """Download a file from S3."""
    storage = S3Storage()
    return storage.download_file(s3_key, local_path)


def list_s3_files(prefix: str = "") -> List[str]:
    """List files in S3 bucket."""
    storage = S3Storage()
    return storage.list_files(prefix)