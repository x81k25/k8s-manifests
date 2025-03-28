# kubernetes manifests repository

This repository contains Kubernetes manifests for applications deployed via ArgoCD to a k3s cluster.

## repository structure

- **app.yaml**: top-level app definition
- **atd-overlays.yaml**: app definition for ATD overlays
- **nginx-test-*.yaml**: various nginx test applications
- **postgres**: PostgreSQL StatefulSet deployment
- **postgres-full**: PostgreSQL deployment with additional resources (network policies, etc.)
- **atd**: application with base configuration and environment overlays

## application management

All applications are managed using ApplicationSets at the top level. the repository connects directly to ArgoCD through Terraform, automatically deploying changes to the k3s cluster.

## deployment patterns

### basic applications
standard Kubernetes manifests with app, deployment, and service definitions.

### kustomize applications
applications using Kustomize for configuration management:
- base configurations in `/atd/base`
- environment-specific overlays in `/atd/overlays/{dev,stg}`

### database deployments
- **postgres**: simple StatefulSet-based deployment
- **postgres-full**: comprehensive deployment with persistent volumes, network policies, etc.

## CI/CD pipeline

1. commit changes to this repository
2. terraform connects the repository to ArgoCD
3. argocd automatically syncs manifests to the k3s cluster
4. applications are deployed based on their respective manifests

## adding new applications

1. create a new directory with your application manifests
2. reference the application in an ApplicationSet
3. commit and push changes
4. argocd will automatically deploy the new application

## useful code

- delete stubborn apps

```bash 
kubectl delete applications.argoproj.io <appset> -n argocd --force --grace-period=0
```

- check port usage by kubernetes

```bash
kubectl get svc --all-namespaces | grep <port-number>
```

- get logs
  - applicationset-controller

```bash
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-applicationset-controller
```