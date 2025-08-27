#!/usr/bin/env python3
"""Docker processing operations for OSRM pipeline steps."""

import argparse
import subprocess
import sys
from pathlib import Path
from loguru import logger


def get_compose_file_for_step(step: str) -> str:
    """Get the appropriate compose file for a given step."""
    step_files = {
        "extract": "docker-compose.extract.yml",
        "partition": "docker-compose.partition.yml", 
        "customize": "docker-compose.customize.yml"
    }
    return step_files.get(step, f"docker-compose.{step}.yml")


def run_docker_compose_step(step: str, timeout: int = 1800) -> bool:
    """Run a specific OSRM processing step."""
    compose_file = get_compose_file_for_step(step)
    service = f"osrm-{step}"
    return run_docker_compose(compose_file, service, timeout)


def run_docker_compose(compose_file: str, service: str, timeout: int = 1800) -> bool:
    """Run a specific service from docker-compose file."""
    try:
        cmd = [
            "docker-compose",
            "-f", compose_file,
            "up", service
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        logger.info(f"Timeout: {timeout} seconds")
        
        # Run the command with timeout
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Log output
        if result.stdout:
            logger.info("Docker output:")
            for line in result.stdout.splitlines()[-20:]:  # Last 20 lines
                logger.info(f"  {line}")
        
        if result.stderr:
            logger.warning("Docker errors:")
            for line in result.stderr.splitlines()[-10:]:  # Last 10 error lines
                logger.warning(f"  {line}")
        
        # Check result
        if result.returncode == 0:
            logger.success(f"Docker service '{service}' completed successfully")
            return True
        else:
            logger.error(f"Docker service '{service}' failed with exit code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Docker operation timed out after {timeout} seconds")
        return False
    except FileNotFoundError:
        logger.error("docker-compose command not found. Please install Docker Compose.")
        return False
    except Exception as e:
        logger.error(f"Docker operation failed: {e}")
        return False


def cleanup_docker(compose_file: str) -> bool:
    """Clean up docker-compose containers and networks."""
    try:
        cmd = ["docker-compose", "-f", compose_file, "down"]
        logger.info(f"Cleaning up: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Docker cleanup completed")
            return True
        else:
            logger.warning(f"Docker cleanup had issues: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Docker cleanup failed: {e}")
        return False


def main():
    """Main entry point for processing operations."""
    parser = argparse.ArgumentParser(
        description="Docker processing operations for OSRM pipeline"
    )
    parser.add_argument(
        "--step",
        choices=["extract", "partition", "customize", "all"],
        required=True,
        help="OSRM processing step to run"
    )
    parser.add_argument(
        "--compose-file",
        default="docker-compose.preprocessing.local.yml",
        help="Docker compose file to use (default: docker-compose.preprocessing.local.yml)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for Docker operations (default: 1800)"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip Docker cleanup after processing"
    )
    
    args = parser.parse_args()
    
    logger.info("OSRM Processing Step")
    logger.info(f"Step: {args.step}")
    logger.info(f"Compose file: {args.compose_file}")
    logger.info(f"Timeout: {args.timeout}s")
    
    # Check if compose file exists
    compose_path = Path(args.compose_file)
    if not compose_path.exists():
        logger.error(f"Docker compose file not found: {compose_path}")
        return False
    
    try:
        success = True
        
        # Run the requested processing steps
        if args.step in ["extract", "partition", "customize"]:
            success = run_docker_compose_step(args.step, args.timeout)
            
        elif args.step == "all":
            # Run all steps in sequence using their specific compose files
            steps = ["extract", "partition", "customize"]
            for step in steps:
                logger.info(f"\nRunning {step} step")
                if not run_docker_compose_step(step, args.timeout):
                    success = False
                    break
        
        # Clean up Docker containers
        if not args.no_cleanup:
            if args.step == "all":
                # Clean up all compose files
                for step in ["extract", "partition", "customize"]:
                    cleanup_docker(get_compose_file_for_step(step))
            else:
                cleanup_docker(get_compose_file_for_step(args.step))
        
        if success:
            logger.success(f"Processing step '{args.step}' completed successfully")
            return True
        else:
            logger.error(f"Processing step '{args.step}' failed")
            return False
            
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        if not args.no_cleanup:
            cleanup_docker(args.compose_file)
        return False
    except Exception as e:
        logger.error(f"Processing operation failed: {e}")
        return False


if __name__ == "__main__":
    if not main():
        sys.exit(1)