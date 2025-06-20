"""Tests for pub_img.mod module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.pub_img.mod import (
    upload_images,
    upload_image,
    wait_container_finish,
    create_presigned_url,
)


class TestPubImgMod:
    """Test cases for pub_img mod functions."""

    @pytest.fixture
    def mock_client(self):
        """Mock Client for testing."""
        client = MagicMock()
        return client

    @patch("src.pub_img.mod.wait_container_finish")
    def test_upload_images_success(self, mock_wait_container_finish, mock_client):
        """Test successful multiple image upload."""
        # Setup mock responses
        mock_client.create_image_media.side_effect = [
            {"id": "container1"},
            {"id": "container2"}
        ]
        mock_client.create_carousel_media.return_value = {"id": "carousel-container"}
        mock_client.publish_media.return_value = {"id": "published-media"}
        mock_client.get_media.return_value = {"id": "published-media", "permalink": "https://example.com"}

        image_urls = ["https://example.com/image1.png", "https://example.com/image2.png"]
        caption = "Test caption"

        upload_images(mock_client, image_urls, caption)

        # Verify image media creation
        assert mock_client.create_image_media.call_count == 2
        mock_client.create_image_media.assert_any_call(
            image_url="https://example.com/image1.png",
            caption=caption,
            is_carousel_item=True
        )
        mock_client.create_image_media.assert_any_call(
            image_url="https://example.com/image2.png",
            caption=caption,
            is_carousel_item=True
        )

        # Verify carousel creation
        mock_client.create_carousel_media.assert_called_once_with(
            caption=caption,
            media_type="CAROUSEL",
            children=["container1", "container2"]
        )

        # Verify waiting and publishing
        assert mock_wait_container_finish.call_count == 3  # 2 images + 1 carousel
        mock_client.publish_media.assert_called_once_with(creation_id="carousel-container")
        mock_client.get_media.assert_called_once_with(media_id="published-media")

    def test_upload_images_create_media_error(self, mock_client):
        """Test upload_images when create_image_media fails."""
        mock_client.create_image_media.side_effect = Exception("Create media error")

        with pytest.raises(Exception, match="Create media error"):
            upload_images(mock_client, ["https://example.com/image.png"], "caption")

    @patch("src.pub_img.mod.wait_container_finish")
    def test_upload_images_carousel_error(self, mock_wait_container_finish, mock_client):
        """Test upload_images when carousel creation fails."""
        mock_client.create_image_media.return_value = {"id": "container1"}
        mock_client.create_carousel_media.side_effect = Exception("Carousel error")

        with pytest.raises(Exception, match="Carousel error"):
            upload_images(mock_client, ["https://example.com/image.png"], "caption")

    @patch("src.pub_img.mod.wait_container_finish")
    def test_upload_image_success(self, mock_wait_container_finish, mock_client):
        """Test successful single image upload."""
        mock_client.create_image_media.return_value = {"id": "container1"}
        mock_client.publish_media.return_value = {"id": "published-media"}
        mock_client.get_media.return_value = {"id": "published-media"}

        upload_image(mock_client, "https://example.com/image.png", "Test caption")

        mock_client.create_image_media.assert_called_once_with(
            image_url="https://example.com/image.png",
            caption="Test caption",
            is_carousel_item=False
        )
        mock_wait_container_finish.assert_called_once_with(mock_client, "container1")
        mock_client.publish_media.assert_called_once_with(creation_id="container1")
        mock_client.get_media.assert_called_once_with(media_id="published-media")

    def test_upload_image_create_error(self, mock_client):
        """Test upload_image when image creation fails."""
        mock_client.create_image_media.side_effect = Exception("Create error")

        with pytest.raises(Exception, match="Create error"):
            upload_image(mock_client, "https://example.com/image.png", "caption")

    @patch("src.pub_img.mod.time.sleep")
    def test_wait_container_finish_success(self, mock_sleep, mock_client):
        """Test successful container status waiting."""
        mock_client.get_container_status.side_effect = [
            {"status_code": "IN_PROGRESS"},
            {"status_code": "IN_PROGRESS"},
            {"status_code": "FINISHED"}
        ]

        wait_container_finish(mock_client, "container123")

        assert mock_client.get_container_status.call_count == 3
        assert mock_sleep.call_count == 2  # Should sleep 2 times before finished

    @patch("src.pub_img.mod.time.sleep")
    def test_wait_container_finish_immediate(self, mock_sleep, mock_client):
        """Test container already finished."""
        mock_client.get_container_status.return_value = {"status_code": "FINISHED"}

        wait_container_finish(mock_client, "container123")

        mock_client.get_container_status.assert_called_once()
        mock_sleep.assert_not_called()

    def test_wait_container_finish_status_error(self, mock_client):
        """Test wait_container_finish when status check fails."""
        mock_client.get_container_status.side_effect = Exception("Status error")

        with pytest.raises(Exception, match="Status error"):
            wait_container_finish(mock_client, "container123")

    @patch("src.pub_img.mod.boto3.client")
    def test_create_presigned_url_success(self, mock_boto3_client):
        """Test successful presigned URL creation."""
        mock_s3_client = MagicMock()
        mock_s3_client.generate_presigned_url.return_value = "https://presigned-url.com"
        mock_boto3_client.return_value = mock_s3_client

        result = create_presigned_url("test-bucket", "test-key.png", 600)

        assert result == "https://presigned-url.com"
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test-key.png"},
            ExpiresIn=600
        )

    @patch("src.pub_img.mod.boto3.client")
    def test_create_presigned_url_default_expiration(self, mock_boto3_client):
        """Test presigned URL creation with default expiration."""
        mock_s3_client = MagicMock()
        mock_s3_client.generate_presigned_url.return_value = "https://presigned-url.com"
        mock_boto3_client.return_value = mock_s3_client

        result = create_presigned_url("test-bucket", "test-key.png")

        assert result == "https://presigned-url.com"
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test-key.png"},
            ExpiresIn=300  # default
        )

    @patch("src.pub_img.mod.boto3.client")
    def test_create_presigned_url_client_error(self, mock_boto3_client):
        """Test presigned URL creation with ClientError."""
        mock_s3_client = MagicMock()
        mock_s3_client.generate_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket"}}, "get_object"
        )
        mock_boto3_client.return_value = mock_s3_client

        with pytest.raises(ClientError):
            create_presigned_url("nonexistent-bucket", "test-key.png")

    @patch("src.pub_img.mod.boto3.client")
    def test_create_presigned_url_boto3_config(self, mock_boto3_client):
        """Test that boto3 client is created with correct config."""
        mock_s3_client = MagicMock()
        mock_s3_client.generate_presigned_url.return_value = "https://presigned-url.com"
        mock_boto3_client.return_value = mock_s3_client

        create_presigned_url("test-bucket", "test-key.png")

        # Verify boto3.client was called with s3 service and proper config
        mock_boto3_client.assert_called_once()
        args, kwargs = mock_boto3_client.call_args
        assert args[0] == "s3"
        assert "config" in kwargs
        # The config should have signature_version set to s3v4