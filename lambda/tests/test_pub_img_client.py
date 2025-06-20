"""Tests for pub_img.client module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.pub_img.client import Client, create_fields, call_api


class TestPubImgClient:
    """Test cases for pub_img client functions."""

    def test_create_fields(self):
        """Test field creation function."""
        fields = ["id", "name", "description"]
        result = create_fields(fields)
        assert result == "id,name,description"

    def test_create_fields_empty(self):
        """Test field creation with empty list."""
        result = create_fields([])
        assert result == ""

    @patch("src.pub_img.client.requests.get")
    def test_call_api_get_success(self, mock_get):
        """Test successful GET API call."""
        mock_response = MagicMock()
        mock_response.content = b'{"success": true}'
        mock_get.return_value = mock_response

        result = call_api("https://example.com", "GET", {"param": "value"})

        assert result == {"success": True}
        mock_get.assert_called_once_with("https://example.com", {"param": "value"}, timeout=10)

    @patch("src.pub_img.client.requests.post")
    def test_call_api_post_success(self, mock_post):
        """Test successful POST API call."""
        mock_response = MagicMock()
        mock_response.content = b'{"created": "success"}'
        mock_post.return_value = mock_response

        result = call_api("https://example.com", "POST", {"data": "test"})

        assert result == {"created": "success"}
        mock_post.assert_called_once_with("https://example.com", json={"data": "test"}, timeout=10)

    def test_call_api_unsupported_method(self):
        """Test unsupported HTTP method."""
        with pytest.raises(ValueError, match="Method not supported."):
            call_api("https://example.com", "PUT", {})

    @patch("src.pub_img.client.requests.get")
    def test_call_api_json_decode_error(self, mock_get):
        """Test API call with invalid JSON response."""
        mock_response = MagicMock()
        mock_response.content = b'invalid json'
        mock_get.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            call_api("https://example.com", "GET", {})

    @pytest.fixture
    def mock_config(self):
        """Mock MetaConfig for testing."""
        config = MagicMock()
        config.access_token = "test-token"
        config.account_id = "test-account"
        config.version = "v1.0"
        config.graph_url = "https://graph.facebook.com"
        config.endpoint_base = "https://graph.facebook.com/v1.0/"
        return config

    @pytest.fixture
    def client(self, mock_config):
        """Create Client instance with mock config."""
        return Client(mock_config)

    @patch("src.pub_img.client.call_api")
    def test_get_user_media(self, mock_call_api, client):
        """Test get_user_media method."""
        mock_call_api.return_value = {"data": [{"id": "123"}]}
        
        result = client.get_user_media()
        
        expected_url = "https://graph.facebook.com/v1.0/test-account/media"
        expected_request = {
            "access_token": "test-token",
            "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username"
        }
        
        mock_call_api.assert_called_once_with(expected_url, "GET", expected_request)
        assert result == {"data": [{"id": "123"}]}

    @patch("src.pub_img.client.call_api")
    def test_get_media(self, mock_call_api, client):
        """Test get_media method."""
        mock_call_api.return_value = {"id": "123", "caption": "test"}
        
        result = client.get_media("123")
        
        expected_url = "https://graph.facebook.com/v1.0/123"
        expected_request = {
            "access_token": "test-token",
            "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username"
        }
        
        mock_call_api.assert_called_once_with(expected_url, "GET", expected_request)
        assert result == {"id": "123", "caption": "test"}

    @patch("src.pub_img.client.call_api")
    def test_create_image_media(self, mock_call_api, client):
        """Test create_image_media method."""
        mock_call_api.return_value = {"id": "new-media-123"}
        
        result = client.create_image_media(
            "https://example.com/image.png",
            "Test caption",
            is_carousel_item=True
        )
        
        expected_url = "https://graph.facebook.com/v1.0/test-account/media"
        expected_request = {
            "access_token": "test-token",
            "image_url": "https://example.com/image.png",
            "caption": "Test caption",
            "is_carousel_item": True
        }
        
        mock_call_api.assert_called_once_with(expected_url, "POST", expected_request)
        assert result == {"id": "new-media-123"}

    @patch("src.pub_img.client.call_api")
    def test_create_carousel_media(self, mock_call_api, client):
        """Test create_carousel_media method."""
        mock_call_api.return_value = {"id": "carousel-123"}
        
        result = client.create_carousel_media(
            "Carousel caption",
            "CAROUSEL",
            ["child1", "child2"]
        )
        
        expected_url = "https://graph.facebook.com/v1.0/test-account/media"
        expected_request = {
            "access_token": "test-token",
            "caption": "Carousel caption",
            "media_type": "CAROUSEL",
            "children": ["child1", "child2"]
        }
        
        mock_call_api.assert_called_once_with(expected_url, "POST", expected_request)
        assert result == {"id": "carousel-123"}

    @patch("src.pub_img.client.call_api")
    def test_get_container_status(self, mock_call_api, client):
        """Test get_container_status method."""
        mock_call_api.return_value = {"id": "123", "status": "FINISHED"}
        
        result = client.get_container_status("123")
        
        expected_url = "https://graph.facebook.com/v1.0/123"
        expected_request = {
            "access_token": "test-token",
            "fields": "id,status,status_code"
        }
        
        mock_call_api.assert_called_once_with(expected_url, "GET", expected_request)
        assert result == {"id": "123", "status": "FINISHED"}

    @patch("src.pub_img.client.call_api")
    def test_publish_media(self, mock_call_api, client):
        """Test publish_media method."""
        mock_call_api.return_value = {"id": "published-123"}
        
        result = client.publish_media("creation-123")
        
        expected_url = "https://graph.facebook.com/v1.0/test-account/media_publish"
        expected_request = {
            "access_token": "test-token",
            "creation_id": "creation-123"
        }
        
        mock_call_api.assert_called_once_with(expected_url, "POST", expected_request)
        assert result == {"id": "published-123"}

    @patch("src.pub_img.client.call_api")
    def test_get_content_publishing_limit(self, mock_call_api, client):
        """Test get_content_publishing_limit method."""
        mock_call_api.return_value = {"config": {"quota_total": 25}}
        
        result = client.get_content_publishing_limit()
        
        expected_url = "https://graph.facebook.com/v1.0/test-account/content_publishing_limit"
        expected_request = {
            "access_token": "test-token",
            "fields": "config,quota_usage"
        }
        
        mock_call_api.assert_called_once_with(expected_url, "GET", expected_request)
        assert result == {"config": {"quota_total": 25}}

    @patch("src.pub_img.client.call_api")
    def test_api_error_handling(self, mock_call_api, client):
        """Test API error handling."""
        mock_call_api.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            client.get_user_media()