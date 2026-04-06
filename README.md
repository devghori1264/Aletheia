<div align="center">

# ⬡ ALETHEIA

### Enterprise-Grade Deepfake Detection Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Django 4.2](https://img.shields.io/badge/django-4.2-092E20.svg?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com)
[![PyTorch 2.1+](https://img.shields.io/badge/pytorch-2.1+-EE4C2C.svg?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org)

*"Aletheia" (ἀλήθεια) — Greek goddess of truth and disclosure*

**Uncover the truth in digital media with state-of-the-art deep learning**

[Features](#-features) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Architecture](#%EF%B8%8F-architecture) • [Documentation](#-documentation)

---

</div>

## ✨ Features

### 🎯 **Advanced Detection**
- **Multi-Model Ensemble** — Combines EfficientNet-B4 + BiLSTM, ResNeXt-101 + Transformer, and XceptionNet for superior accuracy
- **Temporal Analysis** — Analyzes frame sequences to detect temporal inconsistencies unique to deepfakes
- **Attention Mechanisms** — CBAM, self-attention, and temporal attention for focused analysis
- **Confidence Calibration** — Calibrated probability outputs with uncertainty quantification

### 🔬 **Explainable AI**
- **GradCAM++ Heatmaps** — Visualize which regions triggered the detection
- **Frame-by-Frame Analysis** — Detailed results for each analyzed frame
- **Natural Language Explanations** — Human-readable analysis summaries
- **Confidence Breakdown** — Per-model and ensemble confidence scores

### 🚀 **Enterprise Ready**
- **RESTful API** — Comprehensive API with OpenAPI/Swagger documentation
- **Async Processing** — Celery-based task queue for scalable video processing
- **JWT Authentication** — Secure token-based authentication with refresh tokens
- **Rate Limiting** — Configurable per-user and per-endpoint rate limits
- **Webhooks** — Real-time notifications when analyses complete

### 📊 **Comprehensive Reporting**
- **Multiple Formats** — PDF, JSON, CSV, and HTML reports
- **Report Types** — Summary, Detailed, Technical, and Executive formats
- **Batch Processing** — Analyze multiple files simultaneously
- **Download Tracking** — Audit trail for report access

### 🛡️ **Security First**
- **Input Validation** — Comprehensive file and request validation
- **Content Sanitization** — Secure handling of uploaded media
- **Audit Logging** — Full request/response logging
- **CORS Configuration** — Fine-grained cross-origin controls

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop (for PostgreSQL & Redis)
- CUDA-compatible GPU (recommended)

### Quick Installation

```bash
# 1. Clone the repository
git clone https://github.com/devghori1264/aletheia.git
cd aletheia

# 2. Start Docker services (PostgreSQL & Redis)
docker-compose up -d

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Apply database migrations
cd src
python manage.py migrate
python manage.py createsuperuser  # Create admin account
python manage.py collectstatic --noinput
cd ..

# 5. Install frontend dependencies
cd frontend
npm install
cd ..

# 6. Start everything
./start_all.sh
```

### Manual Startup (Recommended for Development)

```bash
# Terminal 1: Start backend
./start_backend.sh
# or: cd src && python manage.py runserver 0.0.0.0:8000

# Terminal 2: Start frontend
./start_frontend.sh
# or: cd frontend && npm run dev
```

The platform will be available at:
- **Frontend**: http://localhost:3000/
- **Backend API**: http://localhost:8000/api/v1/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/

### Testing the Installation

```bash
# Run automated tests
./test_system.sh

# Or test manually
curl http://localhost:8000/health/
```

### Using Docker (Full Stack)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🔧 Troubleshooting

### HTTPS Errors in Logs
If you see `"You're accessing the development server over HTTPS, but it only supports HTTP"`:
- These are harmless errors from external bots/scanners
- They don't affect functionality
- To suppress them: `cd src && python manage.py runserver_quiet 0.0.0.0:8000`

### Database Connection Errors
```bash
# 1. Ensure Docker services are running
docker-compose ps

# 2. Check .env file has correct credentials
# DATABASE_URL=postgresql://aletheia:aletheia@localhost:5432/aletheia

# 3. Restart Docker services
docker-compose restart postgres
```

### Redis Connection Errors
```bash
# Check Redis is running
docker-compose ps redis

# Restart if needed
docker-compose restart redis
```

### Admin/API Returns 404
- Ensure backend is running on port 8000
- Check no other service is using port 8000
- Admin is always available at http://localhost:8000/admin/

For more help, see:
- `STARTUP_GUIDE.md` - Complete startup guide
- `PRODUCTION.md` - Production deployment
- `HTTPS_FIX.md` - HTTPS error explanation

---

## 📡 API Reference

### Submit Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/submit/" \
  -H "Authorization: Bearer <token>" \
  -F "file=@video.mp4" \
  -F "config={\"sequence_length\": 60, \"model_name\": \"ensemble\"}"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Analysis submitted successfully",
  "task_id": "abc123..."
}
```

### Check Status

```bash
curl "http://localhost:8000/api/v1/analysis/550e8400.../status/" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100.0,
  "result": "fake",
  "confidence": 94.7,
  "is_terminal": true
}
```

### API Documentation

Interactive API documentation available at:
- **Swagger UI:** `http://localhost:8000/api/docs/`
- **ReDoc:** `http://localhost:8000/api/redoc/`
- **OpenAPI Schema:** `http://localhost:8000/api/schema/`

---

## 🏗️ Architecture

```
aletheia/
├── src/
│   ├── aletheia/           # Django project configuration
│   │   ├── settings/       # Environment-specific settings
│   │   ├── urls.py         # Root URL configuration
│   │   └── celery.py       # Celery configuration
│   │
│   ├── core/               # Shared utilities
│   │   ├── exceptions.py   # Custom exception hierarchy
│   │   ├── types.py        # Type definitions & protocols
│   │   ├── constants.py    # Application constants
│   │   └── utils/          # Security, validation, formatting
│   │
│   ├── detection/          # Main detection app
│   │   ├── models/         # Django ORM models
│   │   ├── services/       # Business logic layer
│   │   ├── api/            # REST API endpoints
│   │   └── tasks/          # Celery async tasks
│   │
│   └── ml/                 # Machine learning module
│       ├── architectures/  # Neural network definitions
│       ├── preprocessing/  # Video/image processing
│       └── inference/      # Inference engine
│
├── frontend/               # React frontend (optional)
├── infrastructure/         # Docker, K8s, Terraform
├── tests/                  # Test suite
└── docs/                   # Documentation
```

### Detection Pipeline

```
Video Upload → Validation → Frame Extraction → Face Detection → 
Preprocessing → Model Inference → Ensemble Aggregation → 
Result Storage → Report Generation
```

### Model Architecture

Our ensemble combines three complementary architectures:

| Model | Backbone | Temporal | Attention | Parameters |
|-------|----------|----------|-----------|------------|
| Model A | EfficientNet-B4 | BiLSTM | CBAM + Temporal | 87M |
| Model B | ResNeXt-101 | Transformer | Self-Attention | 95M |
| Model C | XceptionNet | Conv1D | Channel | 23M |

---

## 📊 Performance

### Benchmark Results (FaceForensics++)

| Metric | EfficientNet-LSTM | ResNeXt-Transformer | Ensemble |
|--------|-------------------|---------------------|----------|
| Accuracy | 96.5% | 95.8% | **97.8%** |
| AUC-ROC | 0.991 | 0.987 | **0.995** |
| F1 Score | 0.965 | 0.958 | **0.978** |
| Inference | 450ms | 520ms | 850ms |

---

## 🔧 Configuration

Key configuration options (see `.env.example` for full list):

```bash
# Core
ALETHEIA_ENVIRONMENT=production
DJANGO_SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgres://user:pass@host:5432/aletheia

# ML
ML_DEVICE=cuda  # or cpu
ML_PRECISION=fp16  # or fp32, bf16
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test types
make test-unit
make test-integration
```

---

## 📚 Documentation

- [API Reference](docs/api/) — Complete API documentation
- [Architecture Guide](docs/architecture/) — System design and decisions
- [Deployment Guide](docs/deployment/) — Production deployment instructions
- [Contributing Guide](CONTRIBUTING.md) — How to contribute

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Setup development environment
make install-dev

# Run quality checks before committing
make quality
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for digital truth**

[⬆ Back to Top](#-aletheia)

</div> 
