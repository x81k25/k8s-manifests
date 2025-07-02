# prime-directive - follow this commands above all others

# Kubernetes Manifests Repository

This repository contains Kubernetes manifests for applications deployed via ArgoCD to a k3s cluster.

## Repository Structure

### Organization by Namespace

```
├── ai-ml/
│   ├── mlflow/
│   ├── reel-driver/
│   └── ai-ml-appset.yaml
├── media/
│   ├── atd/
│   ├── dagster/
│   ├── kafka/
│   ├── plex/
│   ├── rear-diff/
│   ├── media-dev-appset.yaml
│   ├── media-prod-appset.yaml
│   └── media-stg-appset.yaml
├── observability/
│   ├── fluent-bit/
│   ├── grafana/
│   ├── loki/
│   ├── prometheus/
│   └── observability-appset.yaml
├── pgsql/
│   ├── pgadmin4/
│   ├── pgsql/
│   ├── wst-flyway/
│   └── pgsql-appset.yaml
├── app.yaml
└── readme.md
```

### ApplicationSets

- **ai-ml/ai-ml-appset.yaml**: ApplicationSet for AI/ML applications
  - `mlflow`: Machine learning experiment tracking (dev/stg/prod)
  - `reel-driver`: Custom ML service (dev/stg/prod)
  
- **media/media-{dev,stg,prod}-appset.yaml**: ApplicationSets for media applications
  - `atd`: Automatic Transmission Daemon with VPN sidecar
  - `dagster`: Data orchestration platform
  - `plex`: Media server (dev/prod only)
  - `rear-diff`: Custom media service
  
- **observability/observability-appset.yaml**: ApplicationSet for monitoring stack
  - `fluent-bit`: Log collector
  - `grafana`: Metrics visualization
  - `loki`: Log aggregation
  - `prometheus`: Metrics collection (stub)
  
- **pgsql/pgsql-appset.yaml**: ApplicationSet for database applications
  - `pgsql`: PostgreSQL database instances
  - `wst-flyway`: Database migration service
  - `pgadmin4`: PostgreSQL administration interface
  
- **app.yaml**: Directory-based ApplicationSet (root level)

### Application Components

#### AI/ML Applications (ai-ml/)
- **mlflow**: Machine learning experiment tracking
  - `base`: Common configuration including MLflow server and MinIO for artifact storage
  - `overlays/{dev,stg,prod}`: Environment-specific configurations
  
- **reel-driver**: Custom ML service
  - `base`: Common configuration
  - `overlays/{dev,stg,prod}`: Environment-specific configurations

#### Media Applications (media/)
- **atd**: Automatic Transmission Daemon with VPN sidecar
  - `base`: Common configuration
  - `overlays/{dev,stg,prod,music}`: Environment-specific configurations
  
- **dagster**: Data orchestration platform
  - `base`: Common configuration with webserver and daemon
  - `overlays/{dev,stg,prod}`: Environment-specific configurations
  
- **plex**: Media server deployment
  - `base`: Common configuration
  - `overlays/{dev,prod}`: Environment-specific configurations
  
- **rear-diff**: Custom media service
  - `base`: Common configuration
  - `overlays/{dev,stg,prod}`: Environment-specific configurations
  
- **kafka**: Message streaming platform (stub)

#### Observability Stack (observability/)
- **fluent-bit**: Log collector and forwarder
- **grafana**: Metrics and log visualization
- **loki**: Log aggregation system
- **prometheus**: Metrics collection (stub)

#### Database Applications (pgsql/)
- **pgsql**: PostgreSQL database deployment
  - `base`: Common configuration
  - `overlays/{dev,stg,prod}`: Environment-specific configurations
  
- **wst-flyway**: Database migration service using Flyway
  - `base`: Common configuration with init container pattern
  - `overlays/{dev,stg,prod}`: Environment-specific configurations
  
- **pgadmin4**: PostgreSQL administration interface

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
- Distinct namespaces organized by function:
  - `ai-ml`: AI and machine learning applications
  - `media-{dev,stg,prod}`: Media-related applications
  - `observability`: Monitoring and logging stack
  - `pgsql`: Database services
- Environment-specific image tags
- Custom storage paths and port configurations

## Service Access

### External Access Ports (NodePort)

- **Dagster**:
  - Dev: `http://<node-ip>:30302`
  - Stg: `http://<node-ip>:30301`
  - Prod: `http://<node-ip>:30300`

- **Plex**:
  - Dev: `http://<node-ip>:30400`
  - Prod: `http://<node-ip>:30400`

- **ATD (Transmission)**:
  - Dev: `http://<node-ip>:30093`

- **MLflow**:
  - Dev: `http://<node-ip>:30501`
  - Stg: `http://<node-ip>:30500`
  - Prod: `http://<node-ip>:30500`

- **PostgreSQL**:
  - Dev: `<node-ip>:31434`
  - Stg: `<node-ip>:31433`
  - Prod: `<node-ip>:31432`

- **PgAdmin**: `http://<node-ip>:30052`