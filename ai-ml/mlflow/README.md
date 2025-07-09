# MLflow Deployment

## Overview
MLflow deployment with PostgreSQL backend for metadata storage and MinIO S3-compatible object storage for artifacts. All configurations are managed through Terraform-provided ConfigMaps and Secrets.

## Architecture
- **Metadata Storage**: PostgreSQL databases (separate per environment)
- **Artifact Storage**: MinIO S3-compatible object storage
- **Authentication**: Basic auth with environment-specific credentials
- **Configuration**: Centralized in terraform.tfvars

## Environment Details

### Dev Environment
- **URL**: http://localhost:30502
- **Database**: dev-postgres.pgsql.svc.cluster.local:5434
- **MinIO**: http://minio-dev.pgsql.svc.cluster.local:9000
- **Artifact Root**: s3://mlflow/

### Staging Environment
- **URL**: http://localhost:30501
- **Database**: stg-postgres.pgsql.svc.cluster.local:5433
- **MinIO**: http://minio-stg.pgsql.svc.cluster.local:9000
- **Artifact Root**: s3://mlflow/

### Production Environment
- **URL**: http://localhost:30500
- **Database**: prod-postgres.pgsql.svc.cluster.local:5432
- **MinIO**: http://minio-prod.pgsql.svc.cluster.local:9000
- **Artifact Root**: s3://mlflow/

## Configuration Resources

### ConfigMaps
- `mlflow-config-dev`: Development configuration
- `mlflow-config-stg`: Staging configuration
- `mlflow-config-prod`: Production configuration

### Secrets
- `mlflow-secrets-dev`: Development credentials
- `mlflow-secrets-stg`: Staging credentials
- `mlflow-secrets-prod`: Production credentials

## Key Features
- **Automatic Database Migration**: MLflow server automatically upgrades database schema on startup
- **S3-Compatible Storage**: MinIO provides S3 API compatibility for artifact storage
- **Environment Isolation**: Each environment has separate databases and storage buckets
- **GitOps Ready**: All configurations deployed through ArgoCD ApplicationSets

## Client Configuration
When using MLflow client to log experiments:

```python
import mlflow
import os

# Set tracking URI
mlflow.set_tracking_uri('http://localhost:30502')  # Dev example

# Set MinIO credentials (required for artifact upload)
os.environ['AWS_ACCESS_KEY_ID'] = 'your-minio-access-key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'your-minio-secret-key'
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://minio-dev.pgsql.svc.cluster.local:9000'

# Log experiments
with mlflow.start_run():
    mlflow.log_param("alpha", 0.5)
    mlflow.log_metric("rmse", 0.1)
    mlflow.log_artifact("model.pkl")
```

## Troubleshooting

### Database Schema Errors
If you encounter database schema version mismatch errors:
1. The MLflow server will automatically attempt to upgrade the schema
2. If manual intervention is needed: `mlflow db upgrade <postgresql-uri>`

### Artifact Storage Issues
- Ensure MinIO credentials are correctly set in the client environment
- Verify MinIO service is accessible from the MLflow server pod
- Check that the S3 bucket exists (MLflow creates it automatically)

## Dependencies
- PostgreSQL database instance (managed separately)
- MinIO object storage instance (managed separately)
- Terraform-managed ConfigMaps and Secrets