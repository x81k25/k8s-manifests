"""Test S3 utility functions."""

import tempfile
from pathlib import Path
import pytest
from src.utils.s3_utils import S3Storage


def test_s3_storage_init():
    """Test S3Storage initialization."""
    storage = S3Storage()
    assert storage.endpoint
    assert storage.access_key
    assert storage.secret_key
    assert storage.bucket == "dev"


def test_upload_download_file():
    """Test uploading and downloading a file."""
    storage = S3Storage()
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Test content for S3 upload")
        temp_file = f.name
    
    try:
        # Upload file
        test_key = "osrm/test/test_file.txt"
        assert storage.upload_file(temp_file, test_key)
        
        # Verify file exists
        assert storage.file_exists(test_key)
        
        # Download file
        download_path = tempfile.mktemp(suffix=".txt")
        assert storage.download_file(test_key, download_path)
        
        # Verify content
        with open(download_path, "r") as f:
            content = f.read()
            assert content == "Test content for S3 upload"
        
        # Clean up S3
        storage.delete_file(test_key)
        
        # Clean up local files
        Path(temp_file).unlink()
        Path(download_path).unlink()
        
    except Exception as e:
        # Clean up on failure
        Path(temp_file).unlink(missing_ok=True)
        pytest.fail(f"Test failed: {e}")


def test_list_files():
    """Test listing files in S3."""
    storage = S3Storage()
    
    # Create test files
    test_keys = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(f"Test content {i}")
            temp_file = f.name
            test_key = f"osrm/test/list_test_{i}.txt"
            storage.upload_file(temp_file, test_key)
            test_keys.append(test_key)
            Path(temp_file).unlink()
    
    # List files
    files = storage.list_files("osrm/test/")
    
    # Check all test files are in the list
    for key in test_keys:
        assert key in files
    
    # Clean up
    for key in test_keys:
        storage.delete_file(key)


def test_folder_creation():
    """Test creating folders in S3."""
    storage = S3Storage()
    
    # Create folder
    folder_path = "osrm/test/test_folder"
    assert storage.create_folder(folder_path)
    
    # Verify folder exists (will have trailing slash)
    assert storage.file_exists(f"{folder_path}/")
    
    # Clean up
    storage.delete_file(f"{folder_path}/")


def test_file_info():
    """Test getting file metadata."""
    storage = S3Storage()
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Test content for metadata")
        temp_file = f.name
    
    test_key = "osrm/test/metadata_test.txt"
    storage.upload_file(temp_file, test_key)
    
    # Get file info
    info = storage.get_file_info(test_key)
    assert info is not None
    assert "size" in info
    assert "last_modified" in info
    assert info["size"] > 0
    
    # Clean up
    storage.delete_file(test_key)
    Path(temp_file).unlink()


def test_nonexistent_file():
    """Test operations on nonexistent files."""
    storage = S3Storage()
    
    # Check nonexistent file
    assert not storage.file_exists("osrm/test/nonexistent.txt")
    
    # Get info for nonexistent file
    assert storage.get_file_info("osrm/test/nonexistent.txt") is None
    
    # Download nonexistent file
    assert not storage.download_file("osrm/test/nonexistent.txt", "/tmp/test.txt")