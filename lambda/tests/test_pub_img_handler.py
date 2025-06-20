"""Tests for pub_img.handler module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.pub_img.handler import handler, main


class TestPubImgHandler:
    """Test cases for pub_img handler functions."""

    def test_handler_dry_run(self):
        """Test handler with dry run mode."""
        event = {"DryRun": True}
        
        result = handler(event, None)
        
        assert result == {}

    def test_handler_calls_main_with_event_data(self):
        """Test that handler function calls main with event data."""
        event = {
            "TitleImageKey": "test-exec/0.png",
            "ImageKey": "test-exec/1.png",
            "DishName": "テストパスタ",
            "Recipe": "テストレシピ"
        }
        
        with patch("src.pub_img.handler.main") as mock_main, \
             patch.dict("os.environ", {"IMAGE_BUCKET": "test-image-bucket"}):
            
            mock_main.return_value = {}
            result = handler(event, None)
            
            mock_main.assert_called_once_with(
                "test-image-bucket",
                "test-exec/0.png",
                "test-exec/1.png",
                "テストパスタ",
                "テストレシピ"
            )
            assert result == {}

    def test_handler_with_missing_event_data(self):
        """Test handler with missing event data."""
        event = {}
        
        with patch("src.pub_img.handler.main") as mock_main, \
             patch.dict("os.environ", {"IMAGE_BUCKET": "test-bucket"}):
            
            handler(event, None)
            
            mock_main.assert_called_once_with(
                "test-bucket", None, None, None, None
            )

    @patch("src.pub_img.handler.Client")
    @patch("src.pub_img.handler.MetaConfig")
    @patch("src.pub_img.handler.mod.create_presigned_url")
    @patch("src.pub_img.handler.mod.upload_images")
    def test_main_success(
        self,
        mock_upload_images,
        mock_create_presigned_url,
        mock_meta_config_class,
        mock_client_class,
    ):
        """Test successful main function execution."""
        # Setup mocks
        mock_config = MagicMock()
        mock_meta_config_class.return_value = mock_config
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_create_presigned_url.side_effect = [
            "https://presigned-url-1.com",
            "https://presigned-url-2.com"
        ]

        result = main(
            "test-bucket",
            "test-exec/0.png",
            "test-exec/1.png",
            "テストパスタ",
            "テストレシピ"
        )

        assert result == {}
        
        # Verify config and client creation
        mock_meta_config_class.assert_called_once()
        mock_client_class.assert_called_once_with(mock_config)
        
        # Verify presigned URL creation
        assert mock_create_presigned_url.call_count == 2
        mock_create_presigned_url.assert_any_call("test-bucket", "test-exec/0.png")
        mock_create_presigned_url.assert_any_call("test-bucket", "test-exec/1.png")
        
        # Verify upload_images call
        expected_caption = """
テストパスタ

※このレシピと写真はAIによって自動で作成されたものです。
レシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。

テストレシピ

#レシピ #料理 #お菓子 #クッキング #AI #AIレシピ"""
        
        mock_upload_images.assert_called_once_with(
            mock_client,
            image_urls=["https://presigned-url-1.com", "https://presigned-url-2.com"],
            caption=expected_caption
        )

    @patch("src.pub_img.handler.MetaConfig")
    def test_main_config_error(self, mock_meta_config_class):
        """Test main function when config fails."""
        mock_meta_config_class.side_effect = Exception("Config error")

        with pytest.raises(Exception, match="Config error"):
            main("bucket", "key1", "key2", "dish", "recipe")

    @patch("src.pub_img.handler.Client")
    @patch("src.pub_img.handler.MetaConfig")
    def test_main_client_error(self, mock_meta_config_class, mock_client_class):
        """Test main function when client creation fails."""
        mock_config = MagicMock()
        mock_meta_config_class.return_value = mock_config
        
        mock_client_class.side_effect = Exception("Client error")

        with pytest.raises(Exception, match="Client error"):
            main("bucket", "key1", "key2", "dish", "recipe")

    @patch("src.pub_img.handler.Client")
    @patch("src.pub_img.handler.MetaConfig") 
    @patch("src.pub_img.handler.mod.create_presigned_url")
    def test_main_presigned_url_error(
        self, mock_create_presigned_url, mock_meta_config_class, mock_client_class
    ):
        """Test main function when presigned URL creation fails."""
        mock_config = MagicMock()
        mock_meta_config_class.return_value = mock_config
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_create_presigned_url.side_effect = Exception("S3 error")

        with pytest.raises(Exception, match="S3 error"):
            main("bucket", "key1", "key2", "dish", "recipe")

    @patch("src.pub_img.handler.Client")
    @patch("src.pub_img.handler.MetaConfig")
    @patch("src.pub_img.handler.mod.create_presigned_url")
    @patch("src.pub_img.handler.mod.upload_images")
    def test_main_upload_error(
        self,
        mock_upload_images,
        mock_create_presigned_url,
        mock_meta_config_class,
        mock_client_class,
    ):
        """Test main function when upload fails."""
        # Setup mocks
        mock_config = MagicMock()
        mock_meta_config_class.return_value = mock_config
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_create_presigned_url.side_effect = [
            "https://presigned-url-1.com",
            "https://presigned-url-2.com"
        ]
        
        mock_upload_images.side_effect = Exception("Upload error")

        with pytest.raises(Exception, match="Upload error"):
            main("bucket", "key1", "key2", "dish", "recipe")

    def test_main_with_none_parameters(self):
        """Test main function with None parameters."""
        with patch("src.pub_img.handler.Client") as mock_client_class, \
             patch("src.pub_img.handler.MetaConfig") as mock_meta_config_class, \
             patch("src.pub_img.handler.mod.create_presigned_url") as mock_create_presigned_url, \
             patch("src.pub_img.handler.mod.upload_images") as mock_upload_images:
            
            mock_config = MagicMock()
            mock_meta_config_class.return_value = mock_config
            
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            mock_create_presigned_url.side_effect = [
                "https://presigned-url-1.com",
                "https://presigned-url-2.com"
            ]

            result = main("bucket", None, None, None, None)

            assert result == {}
            mock_create_presigned_url.assert_any_call("bucket", None)
            
            expected_caption = """
None

※このレシピと写真はAIによって自動で作成されたものです。
レシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。

None

#レシピ #料理 #お菓子 #クッキング #AI #AIレシピ"""
            
            mock_upload_images.assert_called_once_with(
                mock_client,
                image_urls=["https://presigned-url-1.com", "https://presigned-url-2.com"],
                caption=expected_caption
            )