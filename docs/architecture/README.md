# Aletheia Architecture

This document describes the architecture of Aletheia, an enterprise-grade deepfake detection platform.

## System Overview

```
                                    ┌─────────────────────────────────────────┐
                                    │            Load Balancer                │
                                    │           (nginx/traefik)               │
                                    └─────────────────┬───────────────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    │                                 │                                 │
                    ▼                                 ▼                                 ▼
          ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
          │   API Server    │             │   API Server    │             │   API Server    │
          │    (Django)     │             │    (Django)     │             │    (Django)     │
          └────────┬────────┘             └────────┬────────┘             └────────┬────────┘
                   │                               │                               │
                   └───────────────────────────────┼───────────────────────────────┘
                                                   │
                   ┌───────────────────────────────┼───────────────────────────────┐
                   │                               │                               │
                   ▼                               ▼                               ▼
          ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
          │   PostgreSQL    │             │     Redis       │             │   S3/MinIO      │
          │   (Database)    │             │  (Cache/Queue)  │             │  (File Store)   │
          └─────────────────┘             └────────┬────────┘             └─────────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Celery Beat    │
                                          │  (Scheduler)    │
                                          └────────┬────────┘
                                                   │
                   ┌───────────────────────────────┼───────────────────────────────┐
                   │                               │                               │
                   ▼                               ▼                               ▼
          ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
          │  Celery Worker  │             │  Celery Worker  │             │  Celery Worker  │
          │   (GPU Node)    │             │   (GPU Node)    │             │   (CPU Node)    │
          └─────────────────┘             └─────────────────┘             └─────────────────┘
```

## Component Details

### Frontend (React + TypeScript)

The frontend is a modern single-page application built with:

- **React 18**: UI framework with concurrent features
- **TypeScript**: Type-safe development
- **TanStack Query**: Server state management
- **Zustand**: Client state management
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tooling

**Key Features:**
- Responsive design (mobile-first)
- Dark/light theme support
- Real-time progress updates via WebSocket
- Drag-and-drop file upload
- Interactive result visualization

### API Server (Django + DRF)

The backend API is built with:

- **Django 5.0**: Web framework
- **Django REST Framework**: API layer
- **Celery**: Distributed task queue
- **PostgreSQL**: Primary database
- **Redis**: Cache and message broker

**Architecture Layers:**

```
┌──────────────────────────────────────────────────────────────┐
│                         API Layer                            │
│  (ViewSets, Serializers, Permissions, Rate Limiting)         │
├──────────────────────────────────────────────────────────────┤
│                       Service Layer                          │
│  (Business Logic, Orchestration, Validation)                 │
├──────────────────────────────────────────────────────────────┤
│                       Domain Layer                           │
│  (Models, Managers, Querysets)                               │
├──────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│  (Database, Cache, File Storage, External APIs)              │
└──────────────────────────────────────────────────────────────┘
```

### ML Module

The machine learning pipeline consists of:

#### Model Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Ensemble Model                                   │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│  │  EfficientNet   │  │   XceptionNet   │  │  Transformer    │          │
│  │     + LSTM      │  │    + CBAM       │  │    Encoder      │          │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘          │
│           │                    │                    │                    │
│           └────────────────────┼────────────────────┘                    │
│                                │                                         │
│                    ┌───────────┴───────────┐                            │
│                    │  Aggregation Layer    │                            │
│                    │  (Weighted Voting)    │                            │
│                    └───────────┬───────────┘                            │
│                                │                                         │
│                    ┌───────────┴───────────┐                            │
│                    │   Calibration Layer   │                            │
│                    │  (Temperature Scaling)│                            │
│                    └───────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Preprocessing Pipeline

```
Video Input
    │
    ▼
┌─────────────────────────────┐
│  Frame Extraction           │
│  - Uniform sampling         │
│  - Keyframe detection       │
│  - Scene change detection   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Face Detection             │
│  - MTCNN (primary)          │
│  - MediaPipe (fallback)     │
│  - OpenCV (last resort)     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Face Alignment             │
│  - Landmark detection       │
│  - Affine transformation    │
│  - Crop and resize          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Normalization              │
│  - ImageNet statistics      │
│  - Float32 conversion       │
│  - Sequence preparation     │
└─────────────────────────────┘
```

#### Inference Engine

```
Frame Sequence
    │
    ▼
┌─────────────────────────────┐
│  Batch Formation            │
│  - Dynamic batching         │
│  - Memory optimization      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Model Inference            │
│  - FP16/FP32 precision      │
│  - GPU acceleration         │
│  - Async execution          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Explainability             │
│  - GradCAM++ heatmaps       │
│  - Attention visualization  │
│  - Frame highlighting       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Result Aggregation         │
│  - Temporal smoothing       │
│  - Confidence calibration   │
│  - Uncertainty estimation   │
└─────────────────────────────┘
```

## Data Flow

### Analysis Request Flow

```
1. User uploads video via frontend
          │
          ▼
2. Frontend sends multipart POST to API
          │
          ▼
3. API validates file (size, type, format)
          │
          ▼
4. File stored in S3/MinIO
          │
          ▼
5. Analysis record created in PostgreSQL
          │
          ▼
6. Celery task queued to Redis
          │
          ▼
7. Worker picks up task
          │
          ▼
8. Preprocessing: frames extracted, faces detected
          │
          ▼
9. ML inference: ensemble prediction
          │
          ▼
10. Results stored in PostgreSQL
          │
          ▼
11. WebSocket notification sent to frontend
          │
          ▼
12. Frontend displays results
```

### Batch Processing Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   File 1    │    │   File 2    │    │   File N    │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                          ▼
                ┌─────────────────┐
                │   Batch Job     │
                │   (Created)     │
                └────────┬────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ Worker 1│      │ Worker 2│      │ Worker 3│
   └────┬────┘      └────┬────┘      └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   Batch Job     │
                │   (Completed)   │
                └─────────────────┘
```

## Security Architecture

### Authentication Flow

```
┌──────────┐         ┌───────────┐         ┌──────────┐
│  Client  │         │    API    │         │   DB     │
└────┬─────┘         └─────┬─────┘         └────┬─────┘
     │                     │                    │
     │  POST /auth/token/  │                    │
     │  (credentials)      │                    │
     │────────────────────▶│                    │
     │                     │  Verify password   │
     │                     │───────────────────▶│
     │                     │                    │
     │                     │  User record       │
     │                     │◀───────────────────│
     │                     │                    │
     │  JWT tokens         │                    │
     │◀────────────────────│                    │
     │                     │                    │
     │  GET /analysis/     │                    │
     │  (with JWT)         │                    │
     │────────────────────▶│                    │
     │                     │  Verify JWT        │
     │                     │  Check permissions │
     │                     │                    │
     │  Response           │                    │
     │◀────────────────────│                    │
```

### Security Layers

1. **Network Layer**
   - TLS 1.3 for all traffic
   - Web Application Firewall (WAF)
   - DDoS protection

2. **Application Layer**
   - JWT authentication
   - Role-based access control
   - Rate limiting
   - Input validation

3. **Data Layer**
   - Encryption at rest (AES-256)
   - Database connection encryption
   - Secrets management (Vault)

## Scalability

### Horizontal Scaling

```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ API Pod │     │ API Pod │     │ API Pod │
    │  (3 CPU)│     │  (3 CPU)│     │  (3 CPU)│
    └─────────┘     └─────────┘     └─────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ Worker  │     │ Worker  │     │ Worker  │
    │ (1 GPU) │     │ (1 GPU) │     │ (1 GPU) │
    └─────────┘     └─────────┘     └─────────┘
```

### Resource Recommendations

| Environment | API Nodes | Workers | Database | Redis |
|-------------|-----------|---------|----------|-------|
| Development | 1 | 1 | 1 (shared) | 1 |
| Staging | 2 | 2 | 1 | 1 |
| Production | 3+ | 3+ | Primary + Replica | Cluster |

## Monitoring & Observability

### Metrics Collection

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   App       │────▶│ Prometheus  │────▶│  Grafana    │
│   Metrics   │     │             │     │  Dashboard  │
└─────────────┘     └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   App       │────▶│   Loki      │────▶│  Grafana    │
│   Logs      │     │             │     │  Explore    │
└─────────────┘     └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   App       │────▶│   Jaeger    │────▶│   Trace     │
│   Traces    │     │             │     │   Viewer    │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Key Metrics

**Application Metrics:**
- Request latency (p50, p95, p99)
- Request rate (RPS)
- Error rate
- Active connections

**ML Metrics:**
- Inference latency
- GPU utilization
- Model accuracy
- Batch queue depth

**Infrastructure Metrics:**
- CPU/Memory usage
- Disk I/O
- Network throughput
- Container health

## Disaster Recovery

### Backup Strategy

| Component | Backup Frequency | Retention | RPO | RTO |
|-----------|------------------|-----------|-----|-----|
| Database | Continuous | 30 days | 5 min | 1 hour |
| File Storage | Daily | 90 days | 24 hours | 4 hours |
| Configurations | On change | Indefinite | Immediate | 30 min |

### Failover Procedure

1. Health check detects primary failure
2. Load balancer routes traffic to healthy nodes
3. Database failover to replica
4. Alert sent to operations team
5. Root cause analysis initiated

## Future Considerations

### Planned Improvements

1. **GraphQL API**: For flexible queries
2. **Real-time Streaming**: Video stream analysis
3. **Federated Learning**: Privacy-preserving model updates
4. **Edge Deployment**: On-device inference
5. **Multi-region**: Global deployment for latency

### Technical Debt

1. Migrate to async Django (Django 5.0+ with ASGI)
2. Implement circuit breaker patterns
3. Add comprehensive integration tests
4. Performance optimization for large videos
