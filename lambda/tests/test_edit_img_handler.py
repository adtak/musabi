"""Tests for edit_img.handler module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from PIL import Image
import io

from src.edit_img.handler import (
    handler,
    main,
    create_title,
    put_image,
    _calc_fontsize,
)


class TestEditImgHandler:
    """Test cases for edit_img handler functions."""

    def test_handler_calls_main_with_event_data(self):
        """Test that handler function calls main with event data."""
        event = {
            "ImgUrl": "https://example.com/image.png",
            "DishName": "テストパスタ",
            "ExecName": "test-exec"
        }
        
        with patch("src.edit_img.handler.main") as mock_main, \
             patch.dict("os.environ", {"BUCKET_NAME": "test-bucket"}):
            
            mock_main.return_value = {
                "EditImgUri": "s3://test-bucket/test-exec/0.png",
                "OriginImgUri": "s3://test-bucket/test-exec/1.png"
            }
            result = handler(event, None)
            
            mock_main.assert_called_once_with(
                "https://example.com/image.png",
                "テストパスタ",
                "test-bucket",
                "test-exec"
            )

    def test_handler_with_missing_event_data(self):
        """Test handler with missing event data."""
        event = {}
        
        with patch("src.edit_img.handler.main") as mock_main, \
             patch.dict("os.environ", {"BUCKET_NAME": "test-bucket"}):
            
            handler(event, None)
            
            mock_main.assert_called_once_with("", "", "test-bucket", "")

    @patch("src.edit_img.handler.requests.get")
    @patch("src.edit_img.handler.Image.open")
    @patch("src.edit_img.handler.create_title")
    @patch("src.edit_img.handler.put_image")
    def test_main_success(self, mock_put_image, mock_create_title, mock_image_open, mock_requests_get):
        """Test successful main function execution."""
        # Setup mock image
        mock_image = MagicMock()
        mock_image.size = (1024, 1024)
        mock_image.convert.return_value = mock_image
        mock_image.filter.return_value = mock_image
        mock_image_open.return_value = mock_image
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(b"fake image data")
        mock_requests_get.return_value = mock_response
        
        # Setup mock title image
        mock_title_image = MagicMock()
        mock_create_title.return_value = mock_title_image
        
        # Setup composite image
        mock_composite = MagicMock()
        with patch("src.edit_img.handler.Image.alpha_composite") as mock_alpha_composite:
            mock_alpha_composite.return_value = mock_composite
            
            mock_put_image.side_effect = [
                "s3://test-bucket/test-exec/0.png",
                "s3://test-bucket/test-exec/1.png"
            ]
            
            result = main(
                "https://example.com/image.png",
                "テストタイトル",
                "test-bucket",
                "test-exec"
            )
            
            assert result == {
                "EditImgUri": "s3://test-bucket/test-exec/0.png",
                "OriginImgUri": "s3://test-bucket/test-exec/1.png"
            }
            
            mock_requests_get.assert_called_once_with(
                "https://example.com/image.png",
                timeout=10,
                stream=True
            )
            mock_create_title.assert_called_once_with(
                1024, 1024, "テストタイトル", "src/edit_img/fonts/Bold.ttf"
            )
            assert mock_put_image.call_count == 2

    @patch("src.edit_img.handler.requests.get")
    def test_main_request_error(self, mock_requests_get):
        """Test main function when image request fails."""
        mock_requests_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception, match="Network error"):
            main("https://example.com/image.png", "title", "bucket", "exec")

    @patch("src.edit_img.handler.Image.new")
    @patch("src.edit_img.handler.ImageDraw.Draw")
    @patch("src.edit_img.handler.ImageFont.truetype")
    @patch("src.edit_img.handler._calc_fontsize")
    def test_create_title_success(self, mock_calc_fontsize, mock_truetype, mock_draw_class, mock_image_new):
        """Test successful title image creation."""
        # Setup mocks
        mock_title_image = MagicMock()
        mock_image_new.return_value = mock_title_image
        
        mock_draw = MagicMock()
        mock_draw.textbbox.side_effect = [(0, 100, 500, 150), (0, 80, 300, 100)]
        mock_draw_class.return_value = mock_draw
        
        mock_font = MagicMock()
        mock_truetype.return_value = mock_font
        
        mock_calc_fontsize.return_value = 60
        
        result = create_title(1024, 768, "テストタイトル", "/path/to/font.ttf")
        
        assert result == mock_title_image
        mock_calc_fontsize.assert_called_once()
        mock_draw.rounded_rectangle.assert_called_once()
        assert mock_draw.text.call_count == 2  # Title and subtitle

    @patch("src.edit_img.handler.ImageFont.truetype")
    def test_calc_fontsize(self, mock_truetype):
        """Test font size calculation."""
        mock_draw = MagicMock()
        mock_font = MagicMock()
        mock_truetype.return_value = mock_font
        
        # Mock textlength to return decreasing values
        mock_draw.textlength.side_effect = [900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 410]
        
        result = _calc_fontsize(mock_draw, "テストテキスト", 400, "/path/to/font.ttf")
        
        assert result == 10  # Should stop at font size 10 when text width < 400

    @patch("src.edit_img.handler.boto3.client")
    def test_put_image_success(self, mock_boto3_client):
        """Test successful image upload to S3."""
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client
        
        mock_image = MagicMock()
        # Mock the save method to write to the buffer
        def mock_save(buffer, format):
            buffer.write(b"fake image data")
        mock_image.save.side_effect = mock_save
        
        result = put_image(mock_image, "test-bucket", "test-key.png")
        
        assert result == "s3://test-bucket/test-key.png"
        mock_boto3_client.assert_called_once_with("s3")
        mock_s3_client.put_object.assert_called_once()

    @patch("src.edit_img.handler.boto3.client")
    def test_put_image_s3_error(self, mock_boto3_client):
        """Test S3 upload error handling."""
        mock_s3_client = MagicMock()
        mock_s3_client.put_object.side_effect = Exception("S3 error")
        mock_boto3_client.return_value = mock_s3_client
        
        mock_image = MagicMock()
        def mock_save(buffer, format):
            buffer.write(b"fake image data")
        mock_image.save.side_effect = mock_save
        
        with pytest.raises(Exception, match="S3 error"):
            put_image(mock_image, "test-bucket", "test-key.png")

    def test_main_with_invalid_arguments(self):
        """Test main function with invalid arguments."""
        with pytest.raises(Exception):
            main(None, "title", "bucket", "exec")

    @patch("src.edit_img.handler.requests.get")
    @patch("src.edit_img.handler.Image.open")
    def test_main_image_processing_error(self, mock_image_open, mock_requests_get):
        """Test main function when image processing fails."""
        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(b"fake image data")
        mock_requests_get.return_value = mock_response
        
        mock_image_open.side_effect = Exception("Image processing error")
        
        with pytest.raises(Exception, match="Image processing error"):
            main("https://example.com/image.png", "title", "bucket", "exec")