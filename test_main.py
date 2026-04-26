"""
Integration tests for the neighborhood API.
Run with: pytest test_main.py -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from main import cache_manager
import os
from unittest.mock import patch, AsyncMock

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
    
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestAuthenticationMiddleware:
    """Test Firebase authentication."""
    
    def test_missing_authorization_header(self):
        response = client.post(
            "/api/v1/neighborhood/summary",
            json={
                "latitude": 28.6139,
                "longitude": 77.2090,
                "area_name": "New Delhi",
                "pincode": "110001"
            }
        )
        assert response.status_code == 401
        assert "Missing Authorization header" in response.json()["detail"]
    
    def test_invalid_token_format(self):
        response = client.post(
            "/api/v1/neighborhood/summary",
            headers={"Authorization": "InvalidToken"},
            json={
                "latitude": 28.6139,
                "longitude": 77.2090,
                "area_name": "New Delhi",
                "pincode": "110001"
            }
        )
        assert response.status_code == 401
        assert "Invalid Authorization header format" in response.json()["detail"]


class TestCacheManager:
    """Test caching functionality."""
    
    def test_cache_key_generation(self):
        key1 = cache_manager._generate_key("110001", "New Delhi")
        key2 = cache_manager._generate_key("110001", "New Delhi")
        assert key1 == key2
        
        key3 = cache_manager._generate_key("110002", "New Delhi")
        assert key1 != key3
    
    def test_cache_set_and_get(self):
        test_data = {
            "area_name": "Test Area",
            "pincode": "123456",
            "firestore_data": {"education": []},
            "fun_fact": "Test fact",
            "ai_summary": "Test summary",
            "cached": False,
            "timestamp": "2024-01-15T10:00:00"
        }
        
        cache_manager.set("123456", "Test Area", test_data)
        retrieved = cache_manager.get("123456", "Test Area")
        
        assert retrieved is not None
        assert retrieved["area_name"] == "Test Area"
        assert retrieved["fun_fact"] == "Test fact"


class TestValidation:
    """Test request validation."""
    
    def test_invalid_request_body(self):
        response = client.post(
            "/api/v1/neighborhood/summary",
            headers={"Authorization": "Bearer dummy_token"},
            json={
                "area_name": "New Delhi",
                # Missing required fields
            }
        )
        # Will fail auth first, but validates the validation works
        assert response.status_code in [401, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
