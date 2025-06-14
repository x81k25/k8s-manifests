# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Kubernetes manifests repository for applications deployed via ArgoCD to a k3s cluster. Applications are organized by namespaces and use the Kustomize overlay pattern for environment-specific configurations.

## Key Commands

### ApplicationSet Management
```bash
# Deploy ApplicationSet
kubectl apply -f <appset.yaml>

# Verify ApplicationSet
kubectl get applicationset <appset_name> -n argocd -o yaml

# Delete ApplicationSet
kubectl delete applicationset <appset_name> -n argocd

# Force delete application
kubectl delete applications.argoproj.io <appname> -n argocd --force --grace-period=0
```

### Application Deployment
```bash
# Apply kustomize configuration
kubectl apply -k <overlay-dir>

# Remove application finalizers
kubectl patch application <app_name> -n <namespace> -p '{"metadata":{"finalizers":[]}}' --type=merge
```

### Pod Operations
```bash
# Execute into pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Get pod logs
kubectl logs <pod-name> -n <namespace>

# List pods in namespace
kubectl get pods -n <namespace>

# Check namespace events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

## Architecture

### ApplicationSet Pattern
- **Directory-based**: `app.yaml` automatically discovers applications in directories ending with `-app`
- **List-based**: Named ApplicationSets (e.g., `media-dev-appset.yaml`) explicitly define applications and environments

### Kustomize Structure
Each application follows this pattern:
- `base/`: Common configuration with `kustomization.yaml`, `deployment.yaml`, `service.yaml`
- `overlays/{dev,stg,prod}/`: Environment-specific configurations that patch the base

### Environment Mapping
- `dev`: Development testing
- `stg`: Staging environment  
- `prod`: Production environment
- Special variants (e.g., `music` for ATD)

### Namespace Organization
- `argocd`: ApplicationSets and ArgoCD applications
- `media-{dev,stg,prod}`: Media applications (ATD, Plex)
- `ai-ml`: Machine learning applications (MLflow)
- `pgsql`: Database applications (PostgreSQL, PgAdmin)
- `orchestration`: Workflow applications (Dagster)

## Application Services

### Current Applications
- **atd**: Automatic Transmission Daemon with VPN sidecar
- **plex**: Media server
- **mlflow**: ML experiment tracking with MinIO artifact storage
- **pgsql**: PostgreSQL database
- **dagster**: Data orchestration platform
- **rear-diff**: Custom service
- **reel-driver**: Custom service

### Image Tagging Convention
Images use environment-specific tags (e.g., `:dev`, `:stg`, `:prod`) and are hosted on `ghcr.io/x81k25/`

## Repository URL
All ApplicationSets reference: `https://github.com/x81k25/k8s-manifests`

## Dagster GitHub Integration Status

### Current Work In Progress
**Objective**: Configure Dagster dev environment to load DAGs directly from GitHub repository `https://github.com/x81k25/dagstributor` using the `dev` branch.

### Progress Made
1. ✅ **GitOps Configuration**: Successfully configured Dagster dev overlay to use GitHub repository
2. ✅ **Version Compatibility**: Discovered Dagster 1.5.5 doesn't support `git:` workspace syntax - implemented git clone + python_module approach
3. ✅ **Path Resolution**: Fixed multiple path resolution issues with working directories and PYTHONPATH
4. ✅ **Repository Structure**: Identified repository structure with `repositories/main.py` as entry point and `dags/` directory containing DAG files

### Current Configuration
- **Location**: `/infra/k8s-manifests/dagster/overlays/dev/`
- **Deployment**: `dagster-custom-dev` (renamed to avoid conflicts)
- **Approach**: Git clone + PYTHONPATH + python_module loading
- **Repository**: `https://github.com/x81k25/dagstributor` (dev branch)
- **Entry Point**: `repositories.main.dagstributor_repository`

### Current Status
- Dagster web server is running at `http://192.168.50.2:30302`
- Git clone and repository setup working correctly
- Workspace.yaml configured with `python_module` approach
- PYTHONPATH environment variable set for module discovery
- **Next Step**: Verify if DAGs are now loading successfully

### Key Implementation Details
1. **Git Clone**: Repository cloned to `/opt/dagster/dagster_workspace/dagstributor`
2. **PYTHONPATH**: Set to repository root for module imports
3. **Workspace Config**:
   ```yaml
   load_from:
     - python_module:
         module_name: "repositories.main"
         attribute: "dagstributor_repository"
         working_directory: "/opt/dagster/dagster_workspace/dagstributor"
   ```

### Troubleshooting Commands
```bash
# Check if Dagster is loading DAGs
kubectl logs -n media-dev -l app=dagster -c dagster-dagit --tail=20

# Verify workspace configuration
kubectl exec -n media-dev -c dagster-dagit $(kubectl get pods -n media-dev -l app=dagster -o jsonpath='{.items[0].metadata.name}') -- cat /opt/dagster/dagster_home/workspace.yaml

# Check repository files
kubectl exec -n media-dev -c dagster-dagit $(kubectl get pods -n media-dev -l app=dagster -o jsonpath='{.items[0].metadata.name}') -- ls -la /opt/dagster/dagster_workspace/dagstributor/

# Force ArgoCD sync if needed
kubectl delete application dagster-dev -n argocd

# Check current deployment revision
kubectl get application dagster-dev -n argocd -o jsonpath='{.status.sync.revision}'
```

### Known Issues & Solutions
1. **ArgoCD Sync Delays**: May need to delete/recreate application to force sync of latest changes
2. **Path Resolution**: Dagster 1.5.5 has quirks with working_directory - use PYTHONPATH approach
3. **Module Imports**: Repository structure requires working_directory to be set to repo root for relative imports

### Next Session Tasks
1. Check final logs to confirm DAG loading success
2. Verify DAGs appear in Dagster web UI
3. Test DAG execution
4. Document final working configuration
5. Apply similar configuration to `stg` and `prod` environments if successful