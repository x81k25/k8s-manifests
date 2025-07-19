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
│   ├── center-console/
│   ├── dagster/
│   ├── kafka/
│   ├── plex/
│   ├── rear-diff/
│   ├── center-console-dev-appset.yaml
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
  - `center-console`: Streamlit-based UI for media services
  - `dagster`: Data orchestration platform
  - `plex`: Media server (dev/prod only)
  - `rear-diff`: Custom media service
  
- **observability/observability-appset.yaml**: ApplicationSet for monitoring stack
  - `fluent-bit`: Log collector
  - `grafana`: Metrics visualization with Kubernetes monitoring dashboards
  - `loki`: Log aggregation
  - `prometheus`: Metrics collection with automatic pod discovery
  - `kube-state-metrics`: Kubernetes cluster state metrics
  
- **pgsql/pgsql-appset.yaml**: ApplicationSet for database applications
  - `pgsql`: PostgreSQL database instances
  - `wst-flyway`: Database migration service
  - `pgadmin4`: PostgreSQL administration interface
  
- **app.yaml**: Directory-based ApplicationSet (root level)

### Application Components

#### AI/ML Applications (ai-ml/)
- **mlflow**: Machine learning experiment tracking with PostgreSQL backend and MinIO artifact storage
  - `base`: Common configuration including MLflow server with S3-compatible artifact storage
  - `overlays/{dev,stg,prod}`: Environment-specific configurations with terraform-managed ConfigMaps/Secrets
  - **MinIO Integration**: Uses external MinIO endpoint for artifact storage to support both internal and external access
  
- **reel-driver**: Custom ML service
  - `base`: Common configuration
  - `overlays/{dev,stg,prod}`: Environment-specific configurations

#### Media Applications (media/)
- **atd**: Automatic Transmission Daemon with VPN sidecar
  - `base`: Common configuration
  - `overlays/{dev,stg,prod,music}`: Environment-specific configurations
  
- **center-console**: Streamlit-based UI for media services
  - `base`: Common configuration with rear-diff and center-console ConfigMaps
  - `overlays/{dev,stg,prod}`: Environment-specific configurations with NodePort assignments
  
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
- **grafana**: Metrics and log visualization with comprehensive Kubernetes monitoring dashboards
- **loki**: Log aggregation system
- **prometheus**: Metrics collection with kube-state-metrics
- **kube-state-metrics**: Kubernetes object state metrics exporter

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

## MLflow MinIO Configuration

MLflow uses MinIO for S3-compatible artifact storage with dual endpoint support:

### Architecture
- **Metadata Store**: PostgreSQL databases (separate per environment)
- **Artifact Store**: MinIO S3-compatible object storage
- **Configuration**: Terraform-managed ConfigMaps and Secrets

### Endpoint Configuration
Each MLflow environment is configured with both internal and external MinIO endpoints:

- **Internal Endpoint**: `http://minio-{env}.pgsql.svc.cluster.local:9000` (for pod-to-pod communication)
- **External Endpoint**: `<node-ip>:310xx` (for external client access)

### Environment Variables
```yaml
# ConfigMap values
MLFLOW_MINIO_ENDPOINT_INTERNAL: http://minio-dev.pgsql.svc.cluster.local
MLFLOW_MINIO_ENDPOINT_EXTERNAL: 192.168.50.2
MLFLOW_MINIO_PORT_INTERNAL: 9000
MLFLOW_MINIO_PORT_EXTERNAL: 31005  # Dev example
MLFLOW_MINIO_DEFAULT_ARTIFACT_ROOT: s3://mlflow/

# Secret values
MLFLOW_MINIO_AWS_ACCESS_KEY_ID: MinIO access key
MLFLOW_MINIO_AWS_SECRET_ACCESS_KEY: MinIO secret key
```

### External Access
When accessing MLflow externally via NodePort, it generates artifact URLs using the external MinIO endpoint, ensuring artifacts are accessible from outside the cluster.

## Monitoring and Observability

The observability stack provides comprehensive monitoring and logging for the Kubernetes cluster and all deployed applications.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │────│   Grafana       │    │   Loki          │
│   (Metrics)     │    │   (Dashboards)  │────│   (Logs)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ kube-state-     │    │   Application   │    │   Fluent-bit    │
│ metrics         │    │   Metrics       │    │   (DaemonSet)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Metrics Collection (Prometheus)

**Prometheus Configuration:**
- **Automatic Service Discovery**: Discovers pods with `prometheus.io/scrape: "true"` annotations
- **Scrape Targets**: 
  - Kubernetes API server, nodes, pods, endpoints
  - kube-state-metrics for cluster state information
  - Application-specific metrics from annotated pods
- **Retention**: Configurable retention policy for historical data
- **Storage**: Persistent volume for metrics storage

**Monitored Applications:**
All major applications are configured with Prometheus scraping annotations:
- **MLflow** (port 5000): ML experiment tracking metrics
- **Dagster** (port 3000): Data pipeline orchestration metrics  
- **ATD** (port 9091): Automatic transmission daemon metrics
- **rear-diff** (port 8000): Custom media service metrics
- **reel-driver** (port 8000): ML service metrics

### Cluster State Metrics (kube-state-metrics)

**Exposed Metrics:**
- Pod resource requests and limits vs actual usage
- Node allocatable resources and capacity
- Deployment/ReplicaSet/DaemonSet states and health
- PersistentVolume usage and availability
- Resource quotas and limit ranges
- Pod restart counts and failure reasons

### Grafana Dashboards

**Pre-configured Dashboards:**

1. **Kubernetes Resource Overview** (`k8s-resources`)
   - Cluster-wide CPU and memory usage gauges
   - Resource usage trends by namespace
   - High-level cluster health metrics

2. **Kubernetes Pod Monitoring** (`k8s-pod-monitoring`)
   - Pod-level CPU and memory usage by namespace
   - Pod information table with status and metadata
   - Pod restart counts and failure analysis
   - Template variables for namespace and pod filtering

3. **Kubernetes Namespace Overview** (`k8s-namespace-overview`)
   - Namespace statistics: active namespaces, pod counts by status
   - Resource usage trends by namespace
   - Resource requests vs limits analysis
   - Namespace-focused filtering and analysis

4. **Kubernetes Node Overview** (`k8s-node-overview`)
   - Node health statistics and capacity utilization
   - Node-level resource usage: CPU, memory, disk
   - Node status table with health indicators
   - Hardware and capacity planning insights

**Dashboard Features:**
- **Template Variables**: Dynamic filtering by namespace, pod, node
- **Auto-refresh**: 30-second intervals for real-time monitoring
- **Prometheus Integration**: Direct queries to Prometheus datasource
- **Threshold Alerting**: Color-coded metrics with configurable thresholds

### Log Aggregation (Loki + Fluent-bit)

**Fluent-bit Configuration:**
- **DaemonSet Deployment**: Runs on every node for comprehensive log collection
- **Log Sources**: Container logs, system logs, Kubernetes events
- **Output**: Forwards all logs to Loki for centralized storage
- **Filtering**: Configurable log filtering and enrichment

**Loki Storage:**
- **Centralized Logging**: All application and system logs
- **Log Retention**: Configurable retention policies
- **Integration**: Seamless integration with Grafana for log exploration

### Monitoring Best Practices

**Resource Monitoring:**
- Monitor CPU and memory at container, pod, and node levels
- Track resource requests vs limits vs actual usage
- Monitor disk usage and network I/O across nodes

**Application Health:**
- Track pod restart counts and failure patterns
- Monitor application-specific metrics via Prometheus annotations
- Correlate metrics with logs for comprehensive troubleshooting

**Alerting Strategy:**
- Set up threshold-based alerts for resource exhaustion
- Monitor pod restart rates and failure patterns
- Alert on node health and capacity issues

**Performance Optimization:**
- Use recording rules in Prometheus for complex queries
- Optimize dashboard refresh rates based on monitoring needs
- Implement log retention policies to manage storage costs

### Access and Usage

**Grafana Access:**
- **URL**: `http://<node-ip>:30303`
- **Authentication**: Admin credentials stored in Kubernetes secrets
- **Datasources**: Pre-configured Prometheus and Loki connections

**Prometheus Access:**
- **URL**: `http://<node-ip>:9090` (internal cluster access)
- **Query Interface**: Built-in PromQL query interface
- **Targets**: View all discovered scrape targets at `/targets`

**Dashboard Navigation:**
1. Access Grafana via NodePort
2. Navigate to Dashboards → Browse
3. Select from available Kubernetes monitoring dashboards
4. Use template variables to filter by namespace/pod/node
5. Correlate metrics with logs using Loki integration

## Automated Image Updates

All applications use ArgoCD Image Updater for automated image updates:

### How It Works
1. Image Updater monitors ghcr.io for new image digests matching configured tags
2. When changes are detected, updates are written to `.argocd-source-<app-name>.yaml` files
3. Changes are committed and pushed to the git repository automatically
4. ArgoCD syncs the changes and updates running pods

### Configuration Requirements
- ApplicationSets must use SSH URL: `git@github.com:x81k25/k8s-manifests.git`
- Image tags follow environment conventions: `:dev`, `:stg`, `:prod` or `:main`
- Pull secrets configured via `pullsecret:argocd/ghcr-pull-image-secret`
- All applications use `imagePullPolicy: Always`

### Generated Files
`.argocd-source-*.yaml` files are auto-generated by Image Updater and should not be edited manually.

## Service Access

### External Access Ports (NodePort)
- default k8s nodeport-range: `30000`-`32767`

- **ATD (Transmission)**:
  - Dev:  `http://<node-ip>:30093`
  - Stg:  `http://<node-ip>:30092`
  - Prod: `http://<node-ip>:30091`
  - Music: `http://<node-ip>:30094`

- **Center Console**:
  - Dev:  `http://<node-ip>:30852`
  - Stg:  `http://<node-ip>:30851`
  - Prod: `http://<node-ip>:30850`

- **Dagster**:
  - Dev:  `http://<node-ip>:30302`
  - Stg:  `http://<node-ip>:30301`
  - Prod: `http://<node-ip>:30300`

- **Grafana**: `http://<node-ip>:30303`

- **Loki**: `http://<node-ip>:30310`

- **MLflow**:
  - Dev:  `http://<node-ip>:30502`
  - Stg:  `http://<node-ip>:30501`
  - Prod: `http://<node-ip>:30500`

- **PgAdmin**: `http://<node-ip>:30052`

- **Plex**:
  - Dev:  `http://<node-ip>:30400` (+ UDP ports 30900, 30410-30414)
  - Prod: `http://<node-ip>:30132` (+ multiple TCP/UDP ports for media streaming)

- **PostgreSQL**:
  - Dev:  `<node-ip>:31434`
  - Stg:  `<node-ip>:31433`
  - Prod: `<node-ip>:31432`

- **Rear-Diff**:
  - Dev:  `http://<node-ip>:30812`
  - Stg:  `http://<node-ip>:30811`
  - Prod: `http://<node-ip>:30810`

- **Reel-Driver**:
  - Dev:  `http://<node-ip>:30802`
  - Stg:  `http://<node-ip>:30801`
  - Prod: `http://<node-ip>:30800`

- **MinIO (S3-compatible storage)**:
  - Dev:  `<node-ip>:31005` (API), `<node-ip>:31002` (Console)
  - Stg:  `<node-ip>:31004` (API), `<node-ip>:31001` (Console)
  - Prod: `<node-ip>:31003` (API), `<node-ip>:31000` (Console)