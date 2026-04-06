# API Documentation

## Overview

Aletheia provides a RESTful API for deepfake detection analysis. This document covers all available endpoints, authentication, and usage examples.

## Base URL

```
Production: https://api.aletheia.io/v1
Development: http://localhost:8000/api/v1
```

## Authentication

The API uses JWT (JSON Web Token) authentication.

### Obtaining a Token

```http
POST /auth/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using the Token

Include the token in the `Authorization` header:

```http
Authorization: Bearer <your_access_token>
```

### Refreshing Tokens

```http
POST /auth/token/refresh/
Content-Type: application/json

{
  "refresh": "<your_refresh_token>"
}
```

## Rate Limiting

| Plan | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | 10 | 100 |
| Pro | 60 | 5,000 |
| Enterprise | 300 | Unlimited |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time until reset (Unix timestamp)

---

## Endpoints

### Health Check

#### GET /health/

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "services": {
    "database": "up",
    "redis": "up",
    "ml_models": "loaded"
  }
}
```

---

### Analysis

#### POST /analysis/

Submit a file for deepfake analysis.

**Request:**
```http
POST /analysis/
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <binary>
options: {"use_ensemble": true, "generate_heatmaps": true}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | Video or image file |
| options | JSON | No | Analysis options |

**Options Object:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| use_ensemble | boolean | true | Use all models |
| generate_heatmaps | boolean | true | Generate visual explanations |
| extract_frames | boolean | true | Return frame-level results |
| webhook_url | string | null | URL for completion notification |

**Response (202 Accepted):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "media_file": {
    "id": "media-123",
    "file_name": "video.mp4",
    "file_size": 5242880,
    "mime_type": "video/mp4"
  }
}
```

---

#### GET /analysis/{id}/

Get analysis details by ID.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "prediction": "fake",
  "confidence": 0.95,
  "confidence_level": "very_high",
  "progress": 100,
  "model_results": [
    {
      "model_name": "EfficientNet-LSTM",
      "model_version": "1.0.0",
      "prediction": "fake",
      "confidence": 0.97,
      "fake_score": 0.97,
      "real_score": 0.03,
      "processing_time": 1.234
    },
    {
      "model_name": "XceptionNet",
      "model_version": "1.0.0",
      "prediction": "fake",
      "confidence": 0.93,
      "fake_score": 0.93,
      "real_score": 0.07,
      "processing_time": 0.876
    }
  ],
  "frames": [
    {
      "frame_number": 0,
      "timestamp": 0.0,
      "prediction": "fake",
      "confidence": 0.94,
      "image_url": "/media/frames/frame_0.jpg",
      "heatmap_url": "/media/heatmaps/heatmap_0.jpg",
      "face_detected": true
    }
  ],
  "media_file": {
    "id": "media-123",
    "file_name": "video.mp4",
    "duration": 10.5,
    "width": 1920,
    "height": 1080
  },
  "processing_time": 2.5,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:02Z"
}
```

---

#### GET /analysis/

List all analyses with pagination.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |
| status | string | null | Filter by status |
| prediction | string | null | Filter by prediction |
| ordering | string | -created_at | Sort field |

**Response:**
```json
{
  "count": 150,
  "next": "/api/v1/analysis/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "prediction": "fake",
      "confidence": 0.95,
      "thumbnail_url": "/media/thumbs/thumb.jpg",
      "file_name": "video.mp4",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### POST /analysis/{id}/cancel/

Cancel a pending or processing analysis.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Analysis cancelled successfully"
}
```

---

#### DELETE /analysis/{id}/

Delete an analysis and associated files.

**Response (204 No Content)**

---

### Batch Analysis

#### POST /batch/

Submit multiple files for batch analysis.

**Request:**
```http
POST /batch/
Content-Type: multipart/form-data
Authorization: Bearer <token>

files[]: <binary>
files[]: <binary>
options: {"use_ensemble": true}
```

**Response (202 Accepted):**
```json
{
  "batch_id": "batch-123",
  "status": "pending",
  "total_items": 5,
  "completed_items": 0,
  "items": [
    {
      "id": "item-1",
      "file_name": "video1.mp4",
      "status": "pending"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### GET /batch/{batch_id}/

Get batch analysis status.

**Response:**
```json
{
  "batch_id": "batch-123",
  "status": "processing",
  "total_items": 5,
  "completed_items": 3,
  "failed_items": 0,
  "items": [
    {
      "id": "item-1",
      "analysis_id": "analysis-1",
      "file_name": "video1.mp4",
      "status": "completed",
      "prediction": "fake",
      "confidence": 0.95
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Reports

#### POST /analysis/{id}/report/

Generate a downloadable report.

**Request:**
```json
{
  "format": "pdf",
  "include_frames": true,
  "include_heatmaps": true,
  "include_metadata": true
}
```

**Response:**
```json
{
  "id": "report-123",
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "format": "pdf",
  "download_url": "/media/reports/report-123.pdf",
  "expires_at": "2024-01-16T10:30:00Z"
}
```

---

### Models

#### GET /models/

List available detection models.

**Response:**
```json
{
  "models": [
    {
      "name": "efficientnet_lstm",
      "display_name": "EfficientNet-LSTM",
      "version": "1.0.0",
      "description": "EfficientNet-B4 backbone with bidirectional LSTM",
      "architecture": "efficientnet_b4_lstm",
      "parameters": 87000000,
      "accuracy": 0.972,
      "latency_ms": 1200,
      "is_default": true,
      "is_available": true
    }
  ]
}
```

---

### Webhooks

#### POST /webhooks/

Register a webhook for analysis completion.

**Request:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["analysis.completed", "analysis.failed"],
  "secret": "your-webhook-secret"
}
```

**Response:**
```json
{
  "id": "webhook-123",
  "url": "https://your-server.com/webhook",
  "events": ["analysis.completed", "analysis.failed"],
  "active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Webhook Payload

When an analysis completes, your webhook receives:

```json
{
  "event": "analysis.completed",
  "timestamp": "2024-01-15T10:30:02Z",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "prediction": "fake",
    "confidence": 0.95,
    "status": "completed"
  },
  "signature": "sha256=..."
}
```

Verify the signature using your webhook secret.

---

## Error Responses

### Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File size exceeds maximum allowed (500MB)",
    "details": {
      "field": "file",
      "max_size": 524288000,
      "actual_size": 600000000
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request data |
| AUTHENTICATION_ERROR | 401 | Missing or invalid token |
| AUTHORIZATION_ERROR | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| PROCESSING_ERROR | 500 | Internal processing error |
| MODEL_ERROR | 500 | ML model error |

---

## SDKs & Examples

### Python SDK

```python
from aletheia import AletheiaClient

client = AletheiaClient(api_key="your_api_key")

# Analyze a video
result = client.analyze("path/to/video.mp4")

print(f"Prediction: {result.prediction}")
print(f"Confidence: {result.confidence:.2%}")

# Async analysis
analysis = client.analyze_async("path/to/video.mp4")
result = analysis.wait()
```

### JavaScript/TypeScript

```typescript
import { AletheiaClient } from 'aletheia-js';

const client = new AletheiaClient({ apiKey: 'your_api_key' });

// Analyze a file
const result = await client.analyze(file);

console.log(`Prediction: ${result.prediction}`);
console.log(`Confidence: ${(result.confidence * 100).toFixed(1)}%`);
```

### cURL Examples

```bash
# Analyze a video
curl -X POST https://api.aletheia.io/v1/analysis/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@video.mp4"

# Get analysis result
curl https://api.aletheia.io/v1/analysis/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## Changelog

### v1.0.0 (2024-01-15)

- Initial API release
- Analysis endpoints
- Batch processing
- Webhook support
- PDF/JSON reports
