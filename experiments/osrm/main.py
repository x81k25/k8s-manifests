#!/usr/bin/env python3
"""Main entry point for OSRM preprocessing pipeline."""

import argparse
import os
import sys
from datetime import datetime
from loguru import logger
from src.core.download_osm import download_osm
from src.core.transfer import download_from_s3, upload_to_s3
from src.core.process import cleanup_docker


def cleanup_local_data():
    """Remove all local data files but keep directory structure."""
    from pathlib import Path
    import glob
    
    data_dirs = ["data/raw", "data/intermediate", "data/processed"]
    total_removed = 0
    
    for data_dir in data_dirs:
        dir_path = Path(data_dir)
        if dir_path.exists():
            # Remove all files in directory
            files = list(dir_path.glob("*"))
            for file_path in files:
                if file_path.is_file():
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        total_removed += 1
                        logger.info(f"Removed: {file_path} ({file_size:,} bytes)")
                    except Exception as e:
                        logger.warning(f"Could not remove {file_path}: {e}")
            
            # Ensure directory still exists
            dir_path.mkdir(parents=True, exist_ok=True)
    
    logger.success(f"Cleanup completed: {total_removed} files removed, directories preserved")
    return True


def setup_osrm_environment(args):
    """Set up environment variables for OSRM processing based on arguments."""
    # Always set profile, default to car if not specified
    os.environ["OSRM_PROFILE"] = getattr(args, 'profile', 'car') or 'car'


def download_only(storage_type="s3"):
    """
    Download OSM data only (original functionality).
    
    Args:
        storage_type: "local" or "s3" 
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Starting OSM data download...")
    logger.info(f"Storage type: {storage_type}")
    
    if not download_osm(storage_type=storage_type, s3_prefix="osrm/raw"):
        logger.error("Download failed")
        return False
    
    logger.success("Download completed successfully!")
    return True


def complete_pipeline(storage_mode="local"):
    """
    Run complete OSRM preprocessing pipeline.
    
    Args:
        storage_mode: "local" (keep all files local) or "s3" (upload after each step)
    
    Returns:
        True if successful, False otherwise
    """
    start_time = datetime.now()
    logger.info("OSRM COMPLETE PIPELINE STARTED")
    logger.info(f"Storage mode: {storage_mode}")
    logger.info(f"Started: {start_time}")
    
    from src.core.process import run_docker_compose_step, get_compose_file_for_step
    from src.core.transfer import download_from_s3, upload_to_s3
    
    try:
        # Step 1: Download OSM data
        logger.info("\nStep 1: Download OSM Data")
        if not download_osm(storage_type=storage_mode):
            logger.error(f"Failed to download OSM data with {storage_mode} storage")
            return False
        logger.success("Step 1 completed: OSM data ready")
        
        # Step 2: OSRM Extract processing
        logger.info("\nStep 2: OSRM Extract Processing")
        # For S3 storage, always download OSM data from S3 (overwrites local)
        if storage_mode == "s3":
            logger.info("S3 mode: Downloading OSM data from S3 for extraction (overwrites local)")
            if not download_from_s3("osrm/raw", "data/raw", "california-latest.osm.pbf"):
                logger.error("Failed to download OSM data from S3 for extraction")
                return False
        
        if not run_docker_compose_step("extract", timeout=1800):
            logger.error("OSRM extract processing failed")
            return False
        cleanup_docker(get_compose_file_for_step("extract"))
        logger.success("Step 2 completed: OSRM extraction finished")
        
        # Step 3: OSRM Partition processing
        logger.info("\nStep 3: OSRM Partition Processing")
        if not run_docker_compose_step("partition", timeout=1800):
            logger.error("OSRM partition processing failed")
            return False
        cleanup_docker(get_compose_file_for_step("partition"))
        logger.success("Step 3 completed: OSRM partition finished")
        
        # Step 4: OSRM Customize processing
        logger.info("\nStep 4: OSRM Customize Processing")
        if not run_docker_compose_step("customize", timeout=1800):
            logger.error("OSRM customize processing failed")
            return False
        cleanup_docker(get_compose_file_for_step("customize"))
        
        # Upload final processed data to S3 if using S3 storage
        if storage_mode == "s3":
            logger.info("S3 mode: Uploading final processed data to S3")
            if not upload_to_s3("data/processed", "osrm/processed"):
                logger.error("Failed to upload processed files to S3")
                return False
        logger.success("Step 4 completed: OSRM customize finished")
        
        # Pipeline completion
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.success("\nCOMPLETE PIPELINE FINISHED SUCCESSFULLY!")
        logger.info(f"Started:  {start_time}")
        logger.info(f"Finished: {end_time}")
        logger.info(f"Duration: {duration}")
        logger.info("\nResults:")
        logger.info("  - OSM data processed through full OSRM pipeline")
        if storage_mode == "s3":
            logger.info("  - All files uploaded to S3 storage")
        else:
            logger.info("  - Server-ready files available in data/processed/")
        logger.info("\nNext steps:")
        logger.info("  - Deploy OSRM routing server using processed data")
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        return False




def download_server_data():
    """
    Download OSRM processed data from S3 for server deployment.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Downloading OSRM server data from S3...")
    
    # Ensure processed directory exists
    from pathlib import Path
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Download all processed files from S3
    if not download_from_s3("osrm/processed", "data/processed"):
        logger.error("Failed to download processed OSRM data from S3")
        return False
    
    # Verify key files exist by extension (location agnostic)
    required_extensions = [
        ".osrm.mldgr",  # Multi-Level Dijkstra graph
        ".osrm.cells",  # Routing cells
        ".osrm.ebg",    # Edge-based graph
        ".osrm.geometry"  # Geometry data
    ]
    
    # Find all OSRM files in the directory
    import glob
    osrm_files = glob.glob(str(processed_dir / "*.osrm*"))
    
    # Check which required extensions are present
    found_extensions = set()
    for file_path in osrm_files:
        for ext in required_extensions:
            if file_path.endswith(ext):
                found_extensions.add(ext)
    
    missing_extensions = set(required_extensions) - found_extensions
    
    if missing_extensions:
        logger.error(f"Missing required OSRM file extensions: {list(missing_extensions)}")
        return False
    
    # Display downloaded files
    import subprocess
    result = subprocess.run(
        ["ls", "-lah", "data/processed/"],
        capture_output=True,
        text=True
    )
    logger.info("Downloaded OSRM server files:")
    logger.info(result.stdout)
    
    # Show total size
    result = subprocess.run(
        ["du", "-sh", "data/processed/"],
        capture_output=True,
        text=True
    )
    logger.info(f"Total size: {result.stdout.strip()}")
    
    logger.success("OSRM server data downloaded successfully!")
    logger.info("Ready to start server with: docker-compose -f docker-compose.server.yml up -d")
    return True


def main():
    """Main entry point with multiple operation modes."""
    parser = argparse.ArgumentParser(description="OSRM preprocessing pipeline")
    parser.add_argument(
        "--operation",
        choices=["download", "extract", "partition", "customize", "complete-pipeline", "cleanup", "download-server-data"],
        default="download",
        help="Operation to perform: download OSM data, individual OSRM processing steps, complete pipeline, cleanup, or download server data from S3"
    )
    parser.add_argument(
        "--storage",
        choices=["local", "s3"],
        default="local",
        help="Storage mode: local (all files stay local) or s3 (copy to S3 after each step) (default: local)"
    )
    parser.add_argument(
        "--profile",
        choices=["car", "foot", "bicycle"],
        default="car",
        help="OSRM routing profile (default: car)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout in seconds for Docker operations (default: 3600)"
    )
    parser.add_argument(
        "--clean-up", "-c",
        action="store_true",
        help="Remove all local data files (keeps directories structure)"
    )
    
    args = parser.parse_args()
    
    # Set up OSRM environment variables from arguments
    setup_osrm_environment(args)
    
    if args.operation == "download":
        success = download_only(storage_type=args.storage)
    elif args.operation == "download-server-data":
        success = download_server_data()
    elif args.operation == "complete-pipeline":
        success = complete_pipeline(storage_mode=args.storage)
    elif args.operation in ["extract", "partition", "customize"]:
        # Individual OSRM processing steps with S3 storage logic
        from src.core.process import run_docker_compose_step, get_compose_file_for_step
        from src.core.transfer import download_from_s3, upload_to_s3
        from pathlib import Path
        
        success = True
        
        # Pre-processing: Handle S3 downloads and local file validation
        if args.operation == "extract" and args.storage == "s3":
            # Extract: Read from S3 (overwrite local)
            logger.info("S3 mode: Downloading OSM data from S3 for extraction")
            if not download_from_s3("osrm/raw", "data/raw", "california-latest.osm.pbf"):
                logger.error("Failed to download OSM data from S3 for extraction")
                success = False
        elif args.operation in ["partition", "customize"]:
            # Partition/Customize: Validate local intermediate files exist
            intermediate_dir = Path("data/intermediate")
            required_file = intermediate_dir / "california-latest.osrm.ebg"
            
            if not intermediate_dir.exists() or not required_file.exists():
                logger.error(f"Required intermediate files not found for {args.operation} operation")
                logger.error(f"Expected directory: {intermediate_dir}")
                logger.error(f"Required file: {required_file}")
                logger.error("Run extract operation first to create intermediate files")
                success = False
        
        # Run the processing operation
        if success:
            success = run_docker_compose_step(args.operation, timeout=args.timeout)
        
        # Always cleanup docker containers after processing
        cleanup_docker(get_compose_file_for_step(args.operation))
        
        # Post-processing: Handle S3 uploads for customize step
        if success and args.storage == "s3" and args.operation == "customize":
            logger.info("S3 mode: Uploading processed data to S3")
            if not upload_to_s3("data/processed", "osrm/processed"):
                logger.error("Failed to upload processed data to S3")
                success = False
    elif args.operation == "cleanup":
        # Standalone cleanup operation
        success = cleanup_local_data()
    else:
        logger.error(f"Unknown operation: {args.operation}")
        success = False
    
    # Run cleanup after operation if requested
    if success and args.clean_up and args.operation != "cleanup":
        logger.info("Running post-operation cleanup...")
        cleanup_success = cleanup_local_data()
        if not cleanup_success:
            logger.warning("Main operation succeeded but cleanup failed")
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()