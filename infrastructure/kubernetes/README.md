# Aletheia Kubernetes Manifests

This directory contains Kubernetes manifests for deploying Aletheia.

## Structure

```
kubernetes/
├── base/                    # Base configurations
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── api-deployment.yaml
│   ├── api-service.yaml
│   ├── worker-deployment.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── development/         # Dev-specific overrides
│   ├── staging/             # Staging-specific overrides
│   └── production/          # Production-specific overrides
└── README.md
```

## Quick Start

```bash
# Deploy to development
kubectl apply -k overlays/development/

# Deploy to staging
kubectl apply -k overlays/staging/

# Deploy to production
kubectl apply -k overlays/production/
```

## Prerequisites

- Kubernetes 1.28+
- kubectl configured
- NVIDIA GPU Operator (for GPU nodes)
- cert-manager (for TLS)
- NGINX Ingress Controller

## Configuration

1. Create secrets:
```bash
kubectl create secret generic aletheia-secrets \
  --from-literal=SECRET_KEY='your-secret' \
  --from-literal=DATABASE_URL='postgres://...' \
  -n aletheia
```

2. Apply manifests:
```bash
kubectl apply -k base/
```
