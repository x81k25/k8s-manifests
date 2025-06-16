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