# Kubernetes Manifests Repository

This repository contains Kubernetes manifests for applications deployed via ArgoCD to a k3s cluster.

## Repository Structure

### ApplicationSets by Namespace

- **argocd**
  - `app.yaml`: ApplicationSet for directory-based applications
  
- **media-dev**
  - `media-dev-appset.yaml`: ApplicationSet for dev media applications
    - `atd/overlays/dev`: Automatic Transmission Daemon (dev)
    - `plex/overlays/dev`: Plex Media Server (dev)
  
- **media-stg**
  - `media-stg-appset.yaml`: ApplicationSet for staging media applications
    - `atd/overlays/stg`: Automatic Transmission Daemon (stg)
  
- **media-prod**
  - `media-prod-appset.yaml`: ApplicationSet for production media applications
    - `atd/overlays/prod`: Automatic Transmission Daemon (prod)
    - `atd/overlays/music`: Automatic Transmission Daemon (music variant)
    - `plex/overlays/prod`: Plex Media Server (prod)
  
- **ai-ml**
  - `ai-ml-appset.yaml`: ApplicationSet for AI/ML applications
    - `mlflow/overlays/dev`: MLflow tracking server (dev)
    - `mlflow/overlays/stg`: MLflow tracking server (stg)
    - `mlflow/overlays/prod`: MLflow tracking server (prod)
  
- **pgsql**
  - `pgsql-appset.yaml`: ApplicationSet for PostgreSQL applications
    - `pgsql/overlays/dev`: PostgreSQL database (dev)
    - `pgsql/overlays/stg`: PostgreSQL database (stg)
    - `pgsql/overlays/prod`: PostgreSQL database (prod)
    - `pgadmin4`: PgAdmin interface

### Application Components

- **atd**: Automatic Transmission Daemon with base/overlay pattern
  - `base`: Common configuration
  - `overlays`: Environment-specific configurations
    - `dev`: Development environment
    - `stg`: Staging environment
    - `prod`: Production environment
    - `music`: Specialized music configuration

- **plex**: Media server deployment
  - `base`: Common configuration
  - `overlays`: Environment-specific configurations
    - `dev`: Development environment
    - `prod`: Production environment

- **mlflow**: Machine learning experiment tracking
  - `base`: Common configuration including MLflow server and MinIO for artifact storage
  - `overlays`: Environment-specific configurations
    - `dev`: Development environment
    - `stg`: Staging environment
    - `prod`: Production environment

- **pgsql**: PostgreSQL database deployment
  - `base`: Common configuration
  - `overlays`: Environment-specific configurations
    - `dev`: Development environment
    - `stg`: Staging environment
    - `prod`: Production environment

- **pgadmin4**: PostgreSQL administration interface

- **nginx-test-***: Various Nginx test applications

### Future Services (Stubs)

The following directories are currently empty stubs for future services:
- `airflow`: Workflow automation platform (to be implemented)
- `grafana`: Monitoring and visualization platform (to be implemented)
- `kafka`: Message streaming platform (to be implemented)
- `prometheus`: Monitoring system (to be implemented)

## Deployment Patterns

### ApplicationSet Deployments
Applications are managed using ApplicationSets which automatically sync and deploy to the k3s cluster:

- **Directory-based**: Automatically discovers and deploys applications from directories ending with `-app`
- **List-based**: Explicitly defined applications with specific configurations for different environments

### Kustomize Overlay Pattern
Used for managing environment-specific configurations:

- Base configuration in application's `/base` directory
- Environment overlays in application's `/overlays/{dev,stg,prod}` directories
- Each environment has specialized paths, ports, and image tags

## Application Management

### Deployment Commands

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

### Pod Management

```bash
# Apply kustomize configuration
kubectl apply -k <overlay-dir>

# Execute into pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Get pod configuration
kubectl describe pod <pod-name> -n <namespace> -o yaml

# Get pod logs
kubectl logs <pod-name> -n <namespace>

# Delete pod
kubectl delete pod <pod-name> -n <namespace>
```

### Namespace Operations

```bash
# List pods in namespace
kubectl get pods -n <namespace>

# Check port usage
kubectl get svc --all-namespaces | grep <port-number>

# get namespace events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### ArgoCD Operations

```bash
# Remove application finalizers
kubectl patch application <app_name> -n <namespace> -p '{"metadata":{"finalizers":[]}}' --type=merge

# View ApplicationSet controller logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-applicationset-controller
```

## Adding New Applications

1. Create a new directory with your application manifests
2. Either:
   - Add directory to an existing ApplicationSet
   - Create a new ApplicationSet referencing your application
3. Commit and push changes
4. ArgoCD will automatically deploy the application

## Environment Structure

The repository supports multiple environments:
- `dev`: Development testing
- `stg`: Staging environment
- `prod`: Production environment
- Specialized environments (e.g., `music`)

Each environment uses:
- Distinct namespaces (e.g., `media-prod`, `media-stg`, `ai-ml`)
- Environment-specific image tags
- Custom storage paths and port configurations