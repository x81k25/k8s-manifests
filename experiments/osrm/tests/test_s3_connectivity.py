"""Test S3/MinIO connectivity using credentials from .env file."""

import os
import pytest
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError


def test_s3_connection():
    """Test connection to S3-compatible storage (MinIO)."""
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    endpoint = os.getenv("S3_ENDPOINT")
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    bucket = os.getenv("S3_BUCKET", "dev")
    region = os.getenv("S3_REGION", "us-east-1")
    
    # Validate credentials exist
    assert endpoint, "S3_ENDPOINT not found in .env"
    assert access_key, "S3_ACCESS_KEY not found in .env"
    assert secret_key, "S3_SECRET_KEY not found in .env"
    
    # Ensure endpoint has protocol
    if not endpoint.startswith(("http://", "https://")):
        endpoint = f"http://{endpoint}"
    
    print(f"\nTesting connection to: {endpoint}")
    print(f"Bucket: {bucket}")
    
    # Create S3 client
    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        use_ssl=False if endpoint.startswith("http://") else True,
        verify=False
    )
    
    # Test connection by listing buckets
    try:
        response = s3_client.list_buckets()
        buckets = [b["Name"] for b in response["Buckets"]]
        print(f"Available buckets: {buckets}")
        assert len(buckets) > 0, "No buckets found"
        
        # Check if dev bucket exists
        if bucket in buckets:
            print(f"✓ Target bucket '{bucket}' exists")
        else:
            print(f"⚠ Target bucket '{bucket}' not found, available: {buckets}")
            
    except ClientError as e:
        pytest.fail(f"Failed to connect to S3: {e}")
    except NoCredentialsError:
        pytest.fail("No credentials found")


def test_bucket_operations():
    """Test basic bucket operations."""
    load_dotenv()
    
    endpoint = os.getenv("S3_ENDPOINT")
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    bucket = os.getenv("S3_BUCKET", "dev")
    region = os.getenv("S3_REGION", "us-east-1")
    
    if not endpoint.startswith(("http://", "https://")):
        endpoint = f"http://{endpoint}"
    
    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        use_ssl=False if endpoint.startswith("http://") else True,
        verify=False
    )
    
    # Test listing objects in bucket
    try:
        response = s3_client.list_objects_v2(Bucket=bucket)
        object_count = response.get("KeyCount", 0)
        print(f"\nBucket '{bucket}' contains {object_count} objects")
        
        # List first few objects if any exist
        if object_count > 0:
            objects = response.get("Contents", [])[:5]
            print("Sample objects:")
            for obj in objects:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
                
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            pytest.fail(f"Bucket '{bucket}' does not exist")
        else:
            pytest.fail(f"Failed to list objects: {e}")


if __name__ == "__main__":
    # Allow running directly for debugging
    test_s3_connection()
    test_bucket_operations()