#!/usr/bin/env python3
"""Download OSM data for OSRM processing with local or S3 storage."""

import os
import sys
import argparse
import tempfile
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError
from dotenv import load_dotenv
from loguru import logger
from src.utils.s3_utils import S3Storage


def download_osm(storage_type="local", s3_prefix="osrm/raw"):
    """
    Download OSM data with option to store locally or in S3.
    
    Args:
        storage_type: "local" or "s3" 
        s3_prefix: S3 prefix for uploaded files (used if storage_type="s3")
    
    Returns:
        True if successful, False otherwise
    """
    
    # Load environment variables
    load_dotenv()
    
    # Configuration from environment
    osm_url = os.getenv("OSM_DOWNLOAD_URL", "http://download.geofabrik.de/north-america/us/california-latest.osm.pbf")
    osm_filename = os.getenv("OSM_FILENAME", "california-latest.osm.pbf")
    
    # Determine download location
    if storage_type == "s3":
        # Use temp directory for S3 uploads
        temp_dir = tempfile.mkdtemp(prefix="osm_download_")
        data_dir = Path(temp_dir)
        logger.info(f"Using temporary directory for S3 upload: {data_dir}")
    else:
        # Use local data directory
        data_dir = Path("data/raw")
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using local directory: {data_dir}")
    
    output_file = data_dir / osm_filename
    
    # Download file
    logger.info(f"Downloading: {osm_url}")
    logger.info(f"Temporary target: {output_file}")
    
    try:
        urlretrieve(osm_url, output_file)
    except URLError as e:
        logger.error(f"Download failed: {e}")
        return False
    
    # Verify download
    if not output_file.exists():
        logger.error("File not found after download")
        return False
    
    size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.success(f"Downloaded {size_mb:.2f} MB")
    
    # Handle storage
    if storage_type == "s3":
        logger.info("Uploading to S3")
        try:
            storage = S3Storage()
            s3_key = f"{s3_prefix}/{osm_filename}"
            
            # Check if file already exists
            if storage.file_exists(s3_key):
                logger.info(f"File already exists in S3: {s3_key}, will overwrite")
            
            # Upload to S3
            success = storage.upload_file(str(output_file), s3_key)
            
            # Clean up temp file
            output_file.unlink()
            if output_file.parent.name.startswith("osm_download_"):
                output_file.parent.rmdir()
            
            if success:
                logger.success(f"Uploaded to S3: {s3_key}")
                
                # List files in the prefix to confirm
                files = storage.list_files(s3_prefix)
                logger.info(f"Files in s3://{storage.bucket}/{s3_prefix}:")
                for file in files:
                    if file.startswith(s3_prefix):
                        logger.info(f"  - {file}")
            
            return success
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            # Clean up temp file
            if output_file.exists():
                output_file.unlink()
            return False
    else:
        logger.success(f"File saved locally: {output_file}")
        return True


def download_california_osm():
    """Legacy wrapper for backward compatibility."""
    return download_osm()


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="Download OSM data for OSRM processing")
    parser.add_argument(
        "--storage",
        choices=["local", "s3"],
        default="local",
        help="Storage destination: local filesystem or S3 (default: local)"
    )
    parser.add_argument(
        "--s3-prefix",
        default="osrm/raw",
        help="S3 prefix for uploaded files (default: osrm/raw)"
    )
    
    args = parser.parse_args()
    
    logger.info("=== OSM Data Download ===")
    logger.info(f"Storage type: {args.storage}")
    if args.storage == "s3":
        logger.info(f"S3 prefix: {args.s3_prefix}")
    
    if not download_osm(storage_type=args.storage, s3_prefix=args.s3_prefix):
        sys.exit(1)


if __name__ == "__main__":
    main()