# OSRM Preprocessing Pipeline

Complete Python/Docker pipeline for downloading and preprocessing OpenStreetMap data for OSRM (Open Source Routing Machine). Supports both local and S3 storage with automated Docker lifecycle management.

## Setup

```bash
# Create virtual environment
uv venv

# Install dependencies
uv sync
```

## Project Structure

```
osrm/
├── pyproject.toml                       # Python project configuration
├── README.md                           # This file
├── .env                                # Environment configuration
├── main.py                             # Main pipeline entry point
├── .venv/                              # Virtual environment (created by uv)
├── src/                                # Python source code
│   ├── core/
│   │   ├── download_osm.py            # OSM data download with S3 support
│   │   ├── process.py                 # Docker orchestration for OSRM steps
│   │   └── transfer.py                # S3 upload/download operations
│   └── utils/
│       └── s3_utils.py                # S3/MinIO storage utilities
├── tests/                              # Test suite
│   ├── test_s3_connectivity.py        # S3 connection tests
│   └── test_s3_utils.py               # S3 utility tests
├── data/                               # Data directory structure
│   ├── raw/                           # Raw OSM data downloads
│   ├── intermediate/                  # OSRM processing intermediate files
│   └── processed/                     # Final server-ready OSRM files
├── docker-compose.extract.yml         # OSRM extract step
├── docker-compose.partition.yml       # OSRM partition step
├── docker-compose.customize.yml       # OSRM customize step
└── docker-compose.preprocessing.s3.yml # Legacy S3 processing (deprecated)
```

## Environment Configuration

Copy and configure the `.env` file with your settings:

```bash
# OSM Download Configuration
OSM_DOWNLOAD_URL=http://download.geofabrik.de/north-america/us/california-latest.osm.pbf
OSM_FILENAME=california-latest.osm.pbf
OSRM_PROFILE=car
OSRM_REGION=california-latest

# Data Directory Structure  
DATA_RAW_DIR=data/raw
DATA_INTERMEDIATE_DIR=data/intermediate
DATA_PROCESSED_DIR=data/processed

# S3 Storage Configuration
S3_ENDPOINT=your-minio-endpoint:port
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET=dev
```

## Usage

The pipeline provides a single Python entry point with multiple operation modes:

```bash
usage: main.py [-h] [--operation {download,extract,partition,customize,complete-pipeline,cleanup}]
               [--storage {local,s3}] [--profile {car,foot,bicycle}] [--timeout TIMEOUT] [--clean-up]
```

### Quick Start

**Complete pipeline with S3 storage:**
```bash
uv run python main.py --operation complete-pipeline --storage s3 --clean-up
```

**Individual operations:**
```bash
# Download OSM data
uv run python main.py --operation download --storage s3

# Extract processing
uv run python main.py --operation extract --storage local

# Partition processing
uv run python main.py --operation partition --storage local

# Customize processing (final step)
uv run python main.py --operation customize --storage s3
```

### Operation Details

#### 1. Download Operation
Downloads OSM data from web and optionally uploads to S3:

```bash
# Download to local only
uv run python main.py --operation download --storage local

# Download to local AND upload to S3
uv run python main.py --operation download --storage s3
```

#### 2. Extract Operation
Converts raw OSM data to OSRM intermediate files:

```bash
# Process local files
uv run python main.py --operation extract --storage local

# Download from S3, process, keep intermediate files local
uv run python main.py --operation extract --storage s3
```

**Extract processing details:**
- Duration: ~2.5 minutes for California dataset
- Memory: ~12GB peak RAM usage
- Processes 158M+ nodes, 16M+ ways, 7K+ relations
- Creates 20+ intermediate files (~2.7GB total)
- Automatic Docker cleanup after completion

#### 3. Partition Operation
Divides routing graph into cells for efficient queries:

```bash
uv run python main.py --operation partition --storage local
```

- Requires intermediate files from extract step
- Duration: ~1 minute for California dataset
- Creates partition files for Multi-Level Dijkstra (MLD)

#### 4. Customize Operation
Final step that prepares data for routing server:

```bash
# Process locally
uv run python main.py --operation customize --storage local

# Process and upload final data to S3
uv run python main.py --operation customize --storage s3
```

- Duration: ~20 seconds for California dataset
- Creates server-ready files in `data/processed/`
- Generates MLD graph (.mldgr) and routing cells
- In S3 mode: uploads ~4.2GB of processed data to S3

#### 5. Complete Pipeline
Runs all steps in sequence (download → extract → partition → customize):

```bash
# Full pipeline with local storage
uv run python main.py --operation complete-pipeline --storage local

# Full pipeline with S3 storage + cleanup
uv run python main.py --operation complete-pipeline --storage s3 --clean-up
```

**S3 Pipeline Flow:**
1. Download OSM data → upload to S3
2. Download from S3 → extract processing → keep intermediate local
3. Partition processing (uses local intermediate)
4. Customize processing → upload processed data to S3
5. Optional: cleanup all local files

#### 6. Cleanup Operation
Removes all local data files while preserving directory structure:

```bash
# Standalone cleanup
uv run python main.py --operation cleanup

# Auto-cleanup after any operation
uv run python main.py --operation extract --clean-up
```

### Storage Modes

**Local Storage (`--storage local`):**
- All files remain on local filesystem
- Fastest processing (no network transfers)
- Requires local disk space (~8GB for California)

**S3 Storage (`--storage s3`):**
- Efficient S3 interaction (download for extract, upload final data)
- Suitable for production/cloud deployments  
- Requires S3/MinIO credentials in `.env`

### Additional Options

```bash
# Routing profiles
--profile car          # Car routing (default)  
--profile foot         # Walking/hiking routes
--profile bicycle      # Cycling routes

# Processing timeout
--timeout 3600         # Seconds to wait for Docker operations (default: 3600)

# Post-operation cleanup
--clean-up            # Remove local files after operation completes
```

## Data Flow & File Structure

The pipeline processes data through three distinct phases:

```
Raw OSM Data (1.2GB)
       ↓
Intermediate Files (2.7GB) 
       ↓
Processed Files (4.2GB)
```

**Directory Structure:**
```
data/
├── raw/                           # Downloaded OSM data  
│   └── california-latest.osm.pbf  # Raw OpenStreetMap file (1.2GB)
├── intermediate/                   # OSRM processing intermediate files (2.7GB)
│   ├── california-latest.osrm.ebg        # Edge-based graph (489MB)
│   ├── california-latest.osrm.geometry   # Route geometry (703MB)
│   ├── california-latest.osrm.cnbg       # Contracted node-based graph (90MB)
│   ├── california-latest.osrm.nbg_nodes  # Node-based graph nodes (230MB) 
│   ├── california-latest.osrm.edges      # Graph edges (142MB)
│   ├── california-latest.osrm.enw        # Edge node weights (127MB)
│   ├── california-latest.osrm.partition  # Partition data (85MB)
│   └── [15+ other processing files]      # Various intermediate files
└── processed/                     # Server-ready files (4.2GB)
    ├── california-latest.osrm.mldgr      # Multi-Level Dijkstra graph (510MB)
    ├── california-latest.osrm.cell_metrics # Cell metrics (1GB)
    ├── california-latest.osrm.geometry   # Route geometry (703MB)
    ├── california-latest.osrm.ebg        # Edge-based graph (489MB)
    ├── california-latest.osrm.nbg_nodes  # Node-based graph nodes (230MB)
    └── [20+ other server files]          # All files needed by osrm-routed
```

## Testing

Run the test suite to verify S3 connectivity:
```bash
# Test S3 connectivity
uv run pytest tests/test_s3_connectivity.py -v

# Test S3 utilities  
uv run pytest tests/test_s3_utils.py -v

# Run all tests
uv run pytest -v
```

## Architecture

**Hybrid Python/Docker Pipeline:**
- **Python**: Fast OSM downloads, S3 transfers, and Docker orchestration
- **Docker**: OSRM preprocessing using official `ghcr.io/project-osrm/osrm-backend:latest`
- **Storage**: Flexible local/S3 modes with automatic lifecycle management
- **Processing**: Complete Multi-Level Dijkstra (MLD) pipeline

**Key Features:**
- Consolidated single-command interface
- Automatic Docker container lifecycle management  
- Efficient S3 interaction (download for extract, upload final data)
- Error handling and validation for missing dependencies
- Post-operation cleanup with directory preservation
- Support for car/foot/bicycle routing profiles
- Configurable timeouts and processing parameters

**Performance (California Dataset):**
- Download: ~1.5 minutes (1.2GB OSM data)
- Extract: ~2.5 minutes (12GB peak RAM, creates 2.7GB intermediate files)
- Partition: ~1 minute (creates routing cells)
- Customize: ~20 seconds (creates 4.2GB server-ready files)
- **Total pipeline**: ~6 minutes + S3 transfer time

## Production Deployment

The processed files are ready for OSRM routing server deployment:

```bash
# Start OSRM routing server (example)
docker run -t -i -p 5000:5000 -v "${PWD}/data/processed:/data" \
  ghcr.io/project-osrm/osrm-backend:latest osrm-routed \
  --algorithm mld /data/california-latest.osrm
```

**S3 Deployment:**
- Raw data: `s3://dev/osrm/raw/california-latest.osm.pbf`
- Processed data: `s3://dev/osrm/processed/` (25 files, 4.2GB total)

The pipeline is designed for easy portability to AWS EC2 or other containerized environments.

## OSRM Server Deployment

After preprocessing, the OSRM routing server can be deployed using either Docker Compose (local development) or Kubernetes (production).

### ArgoCD Deployment (Recommended)

Deploy OSRM using GitOps with ArgoCD for better visibility and management:

```bash
# Deploy via ArgoCD ApplicationSet
kubectl apply -f osrm-appset.yaml

# Check ArgoCD application status
kubectl get application osrm-server -n argocd
kubectl get applicationset osrm-appset -n argocd

# View application in ArgoCD UI for container status and health
# ArgoCD provides real-time pod status, sync state, and deployment history

# Delete ArgoCD deployment
kubectl delete applicationset osrm-appset -n argocd
```

**ArgoCD Features:**
- **GitOps Workflow**: Automatic sync from git repository changes
- **Container Visibility**: Real-time pod status and health monitoring in ArgoCD UI
- **Image Updates**: Automatic image digest updates via ArgoCD Image Updater
- **Self-Healing**: Automatic correction of configuration drift

### Direct Kubernetes Deployment (Alternative)

```bash
# Direct kubectl deployment (without ArgoCD)
kubectl apply -f k8s-deployment.yaml
kubectl apply -f service.yaml

# Check deployment status
kubectl get pods -n experiments -l app=osrm-server
kubectl get service osrm-server-nodeport -n experiments

# View server logs
kubectl logs -l app=osrm-server -n experiments

# Delete deployment
kubectl delete -f k8s-deployment.yaml -f service.yaml
```

**Access URLs:**
- **External**: `http://192.168.50.2:32050` (NodePort for client access)
- **Internal**: `osrm-server.experiments.svc.cluster.local:5000` (ClusterIP for internal services)

### Docker Compose Deployment (Development)

```bash
# Start OSRM server with docker-compose
docker-compose -f docker-compose.server.yml up -d

# Check server status
docker-compose -f docker-compose.server.yml logs

# Stop server
docker-compose -f docker-compose.server.yml down
```

### Server Configuration

The server uses environment variables from `.env`:

```bash
# Server Configuration
OSRM_PORT=5000                    # Server port
OSRM_THREADS=4                    # Processing threads
OSRM_MAX_LOCATIONS_TRIP=100       # Max locations for trip service
OSRM_MAX_LOCATIONS_VIAROUTE=100   # Max locations for route service
OSRM_ALGORITHM=mld                # Routing algorithm (Multi-Level Dijkstra)
```

### API Endpoints

The OSRM server provides a comprehensive HTTP API for routing and navigation services:

#### Base URLs
```bash
# Kubernetes (external access)
http://192.168.50.2:32050

# Docker Compose (local development) 
http://localhost:5000
```

#### Available Services

**1. Route Service - `/route/v1/driving/{coordinates}`**

The route service calculates the fastest route between coordinates with detailed navigation information.

```bash
# Basic route between two points (SF to Oakland)
curl "http://192.168.50.2:32050/route/v1/driving/-122.4194,37.7749;-122.2711,37.8044"
# Returns: Route geometry, duration (1174.2s ≈ 19.6min), distance (18.1km)

# Route with turn-by-turn navigation steps
curl "http://192.168.50.2:32050/route/v1/driving/-122.4194,37.7749;-122.2711,37.8044?steps=true"
# Returns: Detailed turn-by-turn instructions with intersections and maneuvers

# Route with alternative paths
curl "http://192.168.50.2:32050/route/v1/driving/-122.4194,37.7749;-122.2711,37.8044?alternatives=true"
# Returns: Multiple route options with different paths

# Route without geometry overview (faster response)
curl "http://192.168.50.2:32050/route/v1/driving/-122.4194,37.7749;-122.2711,37.8044?overview=false"
# Returns: Route info without detailed geometry polyline

# Multi-waypoint route (SF → Oakland → San Jose)
curl "http://192.168.50.2:32050/route/v1/driving/-122.4194,37.7749;-122.2711,37.8044;-121.8863,37.3382"
# Returns: Route through multiple waypoints with leg-by-leg breakdown
```

**2. Nearest Service - `/nearest/v1/driving/{coordinates}`**

Finds the nearest road network point to given coordinates.

```bash
# Find nearest road point to SF coordinates
curl "http://192.168.50.2:32050/nearest/v1/driving/-122.4194,37.7749"
# Returns: Nearest routable point with node IDs and distance offset

# Find 3 nearest road points
curl "http://192.168.50.2:32050/nearest/v1/driving/-122.4194,37.7749?number=3"
# Returns: Array of 3 closest routable points
```

**3. Table Service - `/table/v1/driving/{coordinates}` (Origin-Destination Matrix)**

Computes distance and duration matrices between multiple points. This service generates **origin-destination matrices** that show travel times and distances from every origin to every destination - perfect for logistics, route optimization, fleet management, and delivery planning.

```bash
# Distance/duration matrix for 3 points (SF, Oakland, San Jose)
curl "http://192.168.50.2:32050/table/v1/driving/-122.4194,37.7749;-122.2711,37.8044;-121.8863,37.3382"
# Returns: Full 3x3 origin-destination matrix of distances and durations between all point pairs

# Matrix with specific source (from SF to all destinations)
curl "http://192.168.50.2:32050/table/v1/driving/-122.4194,37.7749;-122.2711,37.8044;-121.8863,37.3382?sources=0"
# Returns: 1x3 matrix from SF to all other points

# Matrix with distance and duration annotations
curl "http://192.168.50.2:32050/table/v1/driving/-122.4194,37.7749;-122.2711,37.8044?annotations=distance,duration"
# Returns: Separate distance and duration arrays for analysis
```

**4. Match Service - `/match/v1/driving/{coordinates}` (GPS Trace Matching)**

Matches GPS traces to road network - essential for cleaning noisy GPS data.

```bash
# GPS trace matching with noisy coordinates
curl "http://192.168.50.2:32050/match/v1/driving/-122.4194,37.7749;-122.4190,37.7750;-122.4185,37.7751;-122.2711,37.8044"
# Returns: Cleaned route snapped to road network with confidence scores

# Match with full overview and turn-by-turn steps
curl "http://192.168.50.2:32050/match/v1/driving/-122.4194,37.7749;-122.4190,37.7750;-122.4185,37.7751;-122.2711,37.8044?overview=full&steps=true"
# Returns: Full route geometry and detailed navigation instructions
```

**5. Trip Service - `/trip/v1/driving/{coordinates}` (Traveling Salesman Optimization)**

Solves traveling salesman problem to find optimal visit order for multiple locations.

```bash
# Trip optimization for 4 cities (finds optimal order)
curl "http://192.168.50.2:32050/trip/v1/driving/-122.4194,37.7749;-122.2711,37.8044;-121.8863,37.3382;-122.2585,37.8716"
# Returns: Optimized route visiting all points with minimal total distance

# Trip with fixed start and end points
curl "http://192.168.50.2:32050/trip/v1/driving/-122.4194,37.7749;-122.2711,37.8044;-121.8863,37.3382?source=first&destination=last"
# Returns: Optimized route starting at first point, ending at last point
```

#### Common Parameters

- `overview`: Geometry overview (`full`, `simplified`, `false`)
- `steps`: Include turn-by-turn navigation (`true`, `false`)
- `alternatives`: Return alternative routes (`true`, `false`)
- `annotations`: Additional metadata (`duration`, `distance`, `speed`)
- `geometries`: Response geometry format (`polyline`, `polyline6`, `geojson`)

#### Response Format

All endpoints return JSON responses with this structure:
```json
{
  "code": "Ok",
  "routes": [...],
  "waypoints": [...]
}
```

### Testing the Server

Run the comprehensive test suite to verify all endpoints:

```bash
# Run all endpoint tests (Kubernetes)
bash tests/test_osrm_endpoints.sh

# Run all endpoint tests (Docker Compose - update script port first)
# Edit tests/test_osrm_endpoints.sh: change OSRM_PORT="32050" to OSRM_PORT="5000"
bash tests/test_osrm_endpoints.sh

# The test covers:
# Route service (basic, alternatives, steps, multi-waypoint)
# Nearest service (single/multiple points)  
# Table service (distance/duration matrix)
# Match service (GPS trace matching)
# Trip service (traveling salesman optimization)
# Tile service (vector tiles)
# Error handling (invalid coordinates/profiles)
```

### Example Coordinates (California)

The test suite and examples use these California coordinates:
- **San Francisco**: `-122.4194,37.7749`
- **Oakland**: `-122.2711,37.8044`
- **San Jose**: `-121.8863,37.3382`
- **Berkeley**: `-122.2585,37.8716`

### Performance & Resources

- **Memory Usage**: Server loads ~4.2GB dataset into memory
- **Startup Time**: ~30-45 seconds to fully load California dataset
- **Concurrent Requests**: Supports multiple simultaneous routing requests
- **Algorithm**: Multi-Level Dijkstra (MLD) for optimal performance

### API Documentation

For detailed API documentation and additional parameters:
- **Official OSRM API Docs**: https://project-osrm.org/docs/v5.24.0/api/
- **GitHub Documentation**: https://github.com/Project-OSRM/osrm-backend/blob/master/docs/http.md