#!/usr/bin/env python3
"""Generic S3 transfer operations for OSRM pipeline steps."""

import argparse
import sys
from pathlib import Path
from loguru import logger
from src.utils.s3_utils import S3Storage


def download_from_s3(s3_path: str, local_path: str, filename: str = None):
    """Download from S3 to local filesystem."""
    storage = S3Storage()
    local_dir = Path(local_path)
    local_dir.mkdir(parents=True, exist_ok=True)
    
    if filename:
        # Download specific file
        s3_key = f"{s3_path}/{filename}"
        local_file = local_dir / filename
        logger.info(f"Downloading {s3_key} to {local_file}")
        return storage.download_file(s3_key, str(local_file))
    else:
        # Download entire directory
        logger.info(f"Downloading directory from s3://{storage.bucket}/{s3_path}/ to {local_dir}/")
        files = storage.list_files(s3_path)
        success_count = 0
        
        for s3_key in files:
            if s3_key.startswith(s3_path + "/"):
                relative_path = s3_key[len(s3_path) + 1:]
                local_file = local_dir / relative_path
                local_file.parent.mkdir(parents=True, exist_ok=True)
                
                if storage.download_file(s3_key, str(local_file)):
                    success_count += 1
                else:
                    logger.error(f"Failed to download {s3_key}")
        
        logger.info(f"Downloaded {success_count} files")
        return success_count > 0


def upload_to_s3(local_path: str, s3_path: str, filename: str = None):
    """Upload from local filesystem to S3."""
    storage = S3Storage()
    local_dir = Path(local_path)
    
    if not local_dir.exists():
        logger.error(f"Local path does not exist: {local_path}")
        return False
    
    if filename:
        # Upload specific file
        local_file = local_dir / filename
        if not local_file.exists():
            logger.error(f"File not found: {local_file}")
            return False
        
        s3_key = f"{s3_path}/{filename}"
        logger.info(f"Uploading {local_file} to {s3_key}")
        return storage.upload_file(str(local_file), s3_key)
    else:
        # Upload entire directory
        logger.info(f"Uploading directory from {local_dir}/ to s3://{storage.bucket}/{s3_path}/")
        return storage.upload_directory(str(local_dir), s3_path) > 0


def main():
    """Main entry point for transfer operations."""
    parser = argparse.ArgumentParser(
        description="Generic S3 transfer operations for OSRM pipeline"
    )
    parser.add_argument(
        "--operation",
        choices=["download", "upload"],
        required=True,
        help="Transfer operation to perform"
    )
    parser.add_argument(
        "--s3-path",
        required=True,
        help="S3 path (e.g., osrm/raw, osrm/intermediate, osrm/processed)"
    )
    parser.add_argument(
        "--local-path",
        required=True,
        help="Local path (e.g., data/raw, data/intermediate, data/processed)"
    )
    parser.add_argument(
        "--filename",
        help="Specific filename (optional, otherwise transfers entire directory)"
    )
    parser.add_argument(
        "--create-dirs",
        action="store_true",
        help="Create S3 directory structure if it doesn't exist"
    )
    
    args = parser.parse_args()
    
    logger.info(f"=== S3 Transfer Operation ===")
    logger.info(f"Operation: {args.operation}")
    logger.info(f"S3 path: {args.s3_path}")
    logger.info(f"Local path: {args.local_path}")
    if args.filename:
        logger.info(f"Filename: {args.filename}")
    
    try:
        if args.operation == "download":
            success = download_from_s3(args.s3_path, args.local_path, args.filename)
        else:  # upload
            # Create S3 directory structure if requested
            if args.create_dirs and not args.filename:
                storage = S3Storage()
                storage.create_folder(args.s3_path)
            
            success = upload_to_s3(args.local_path, args.s3_path, args.filename)
        
        if success:
            logger.success(f"{args.operation.title()} operation completed successfully")
            return True
        else:
            logger.error(f"{args.operation.title()} operation failed")
            return False
            
    except Exception as e:
        logger.error(f"Transfer operation failed: {e}")
        return False


if __name__ == "__main__":
    if not main():
        sys.exit(1)