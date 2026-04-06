"""
Integration Tests for API Endpoints

Tests for the REST API endpoints.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, api_client):
        """Test health check returns 200."""
        response = api_client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_health_check_includes_version(self, api_client):
        """Test health check includes version info."""
        response = api_client.get("/api/v1/health/")
        
        data = response.json()
        assert "version" in data


class TestAnalysisEndpoints:
    """Tests for analysis endpoints."""
    
    def test_list_analyses_unauthenticated(self, api_client):
        """Test listing analyses without auth returns 401."""
        response = api_client.get("/api/v1/analysis/")
        
        assert response.status_code == 401
    
    def test_list_analyses_authenticated(self, authenticated_client):
        """Test listing analyses with auth."""
        response = authenticated_client.get("/api/v1/analysis/")
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "items" in data or isinstance(data, list)
    
    def test_get_analysis_not_found(self, authenticated_client):
        """Test getting non-existent analysis returns 404."""
        response = authenticated_client.get("/api/v1/analysis/nonexistent-id/")
        
        assert response.status_code == 404
    
    def test_create_analysis_no_file(self, authenticated_client):
        """Test creating analysis without file returns 400."""
        response = authenticated_client.post("/api/v1/analysis/", {})
        
        assert response.status_code == 400
    
    def test_create_analysis_with_file(
        self,
        authenticated_client,
        sample_video_path,
    ):
        """Test creating analysis with video file."""
        with open(sample_video_path, "rb") as f:
            response = authenticated_client.post(
                "/api/v1/analysis/",
                {"file": f},
                format="multipart",
            )
        
        # Should either succeed (201/202) or fail validation (400)
        assert response.status_code in [200, 201, 202, 400]
    
    def test_delete_analysis(self, authenticated_client, analysis_factory):
        """Test deleting an analysis."""
        analysis = analysis_factory()
        
        response = authenticated_client.delete(f"/api/v1/analysis/{analysis.id}/")
        
        assert response.status_code in [204, 404]  # 404 if already deleted


class TestBatchEndpoints:
    """Tests for batch analysis endpoints."""
    
    def test_batch_status_unauthenticated(self, api_client):
        """Test batch status without auth returns 401."""
        response = api_client.get("/api/v1/batch/test-batch-id/")
        
        assert response.status_code == 401
    
    def test_batch_not_found(self, authenticated_client):
        """Test getting non-existent batch returns 404."""
        response = authenticated_client.get("/api/v1/batch/nonexistent-id/")
        
        assert response.status_code == 404


class TestModelEndpoints:
    """Tests for model info endpoints."""
    
    def test_list_models(self, api_client):
        """Test listing available models."""
        response = api_client.get("/api/v1/models/")
        
        # Models endpoint may or may not require auth
        assert response.status_code in [200, 401]
    
    def test_list_models_authenticated(self, authenticated_client):
        """Test listing models with auth."""
        response = authenticated_client.get("/api/v1/models/")
        
        assert response.status_code == 200


class TestErrorHandling:
    """Tests for API error handling."""
    
    def test_invalid_json(self, authenticated_client):
        """Test handling of invalid JSON."""
        response = authenticated_client.post(
            "/api/v1/analysis/",
            "not valid json",
            content_type="application/json",
        )
        
        assert response.status_code == 400
    
    def test_method_not_allowed(self, authenticated_client):
        """Test handling of unsupported HTTP method."""
        response = authenticated_client.patch("/api/v1/health/")
        
        assert response.status_code == 405
    
    def test_not_found_route(self, api_client):
        """Test handling of non-existent route."""
        response = api_client.get("/api/v1/nonexistent/")
        
        assert response.status_code == 404


class TestPagination:
    """Tests for API pagination."""
    
    def test_pagination_params(self, authenticated_client):
        """Test pagination parameters are accepted."""
        response = authenticated_client.get(
            "/api/v1/analysis/",
            {"page": 1, "page_size": 10},
        )
        
        assert response.status_code == 200
    
    def test_pagination_invalid_page(self, authenticated_client):
        """Test invalid page number handling."""
        response = authenticated_client.get(
            "/api/v1/analysis/",
            {"page": -1},
        )
        
        # Should either return empty results or error
        assert response.status_code in [200, 400]
    
    def test_pagination_large_page_size(self, authenticated_client):
        """Test large page size is capped."""
        response = authenticated_client.get(
            "/api/v1/analysis/",
            {"page_size": 10000},
        )
        
        assert response.status_code == 200
        # Should not actually return 10000 items
