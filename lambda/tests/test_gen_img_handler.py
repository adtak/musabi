"""Tests for gen_img.handler module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from openai.types import Image
from openai.types.images_response import ImagesResponse

from src.gen_img.handler import (
    handler,
    send_request,
    generate_dish_img,
    main,
)


class TestGenImgHandler:
    """Test cases for gen_img handler functions."""

    def test_handler_calls_main_with_event_data(self):
        """Test that handler function calls main with event data."""
        event = {
            "DishName": "テストパスタ",
            "Recipe": "テストレシピ"
        }
        
        with patch("src.gen_img.handler.main") as mock_main:
            mock_main.return_value = {"ImgUrl": "https://example.com/image.png"}
            result = handler(event, None)
            
            mock_main.assert_called_once_with(
                dish_name="テストパスタ",
                recipe="テストレシピ"
            )
            assert result == {"ImgUrl": "https://example.com/image.png"}

    def test_handler_with_missing_event_data(self):
        """Test handler with missing event data."""
        event = {}
        
        with patch("src.gen_img.handler.main") as mock_main:
            mock_main.return_value = {"ImgUrl": "https://example.com/image.png"}
            handler(event, None)
            
            mock_main.assert_called_once_with(
                dish_name="",
                recipe=""
            )

    @patch("src.gen_img.handler.OpenAI")
    def test_send_request_success(self, mock_openai_class):
        """Test successful DALL-E API request."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Create mock response
        mock_image = Image(url="https://example.com/generated-image.png")
        mock_response = ImagesResponse(
            created=1234567890,
            data=[mock_image]
        )
        mock_client.images.generate.return_value = mock_response

        result = send_request(mock_client, "Generate pasta image")

        assert result == "https://example.com/generated-image.png"
        mock_client.images.generate.assert_called_once_with(
            model="dall-e-3",
            prompt="Generate pasta image",
            size="1024x1024",
            quality="standard",
            n=1,
        )

    def test_send_request_api_error(self, mock_openai_client):
        """Test DALL-E API error handling."""
        mock_openai_client.images.generate.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            send_request(mock_openai_client, "test prompt")

    @patch("src.gen_img.handler.send_request")
    def test_generate_dish_img_success(self, mock_send_request):
        """Test successful dish image generation."""
        mock_send_request.return_value = "https://example.com/dish-image.png"
        mock_client = MagicMock()

        result = generate_dish_img(mock_client, "Generate pasta image")

        assert result == "https://example.com/dish-image.png"
        mock_send_request.assert_called_once_with(mock_client, "Generate pasta image")

    @patch("src.gen_img.handler.OpenAIConfig")
    @patch("src.gen_img.handler.OpenAI")
    @patch("src.gen_img.handler.generate_dish_img")
    def test_main_success(
        self,
        mock_generate_dish_img,
        mock_openai_class,
        mock_config_class,
    ):
        """Test successful main function execution."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.api_key = "test-api-key"
        mock_config_class.return_value = mock_config
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_generate_dish_img.return_value = "https://example.com/generated.png"

        dish_name = "トマトパスタ"
        recipe = "美味しいパスタのレシピ"
        result = main(dish_name, recipe)

        expected_prompt = f"""
{dish_name}という料理の画像を生成してください。レシピは次のとおりです。
{recipe}
"""

        assert result == {"ImgUrl": "https://example.com/generated.png"}
        mock_config_class.assert_called_once()
        mock_openai_class.assert_called_once_with(api_key="test-api-key")
        mock_generate_dish_img.assert_called_once_with(mock_client, expected_prompt)

    @patch("src.gen_img.handler.OpenAIConfig")
    def test_main_config_error(self, mock_config_class):
        """Test main function when config fails."""
        mock_config_class.side_effect = Exception("Config error")

        with pytest.raises(Exception, match="Config error"):
            main("dish", "recipe")

    @patch("src.gen_img.handler.OpenAIConfig")
    @patch("src.gen_img.handler.OpenAI")
    def test_main_openai_client_error(self, mock_openai_class, mock_config_class):
        """Test main function when OpenAI client creation fails."""
        mock_config = MagicMock()
        mock_config.api_key = "test-api-key"
        mock_config_class.return_value = mock_config
        
        mock_openai_class.side_effect = Exception("OpenAI client error")

        with pytest.raises(Exception, match="OpenAI client error"):
            main("dish", "recipe")

    def test_main_with_empty_inputs(self):
        """Test main function with empty inputs."""
        with patch("src.gen_img.handler.OpenAIConfig") as mock_config_class, \
             patch("src.gen_img.handler.OpenAI") as mock_openai_class, \
             patch("src.gen_img.handler.generate_dish_img") as mock_generate_dish_img:
            
            mock_config = MagicMock()
            mock_config.api_key = "test-api-key"
            mock_config_class.return_value = mock_config
            
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            mock_generate_dish_img.return_value = "https://example.com/empty.png"

            result = main("", "")

            expected_prompt = """
という料理の画像を生成してください。レシピは次のとおりです。

"""

            assert result == {"ImgUrl": "https://example.com/empty.png"}
            mock_generate_dish_img.assert_called_once_with(mock_client, expected_prompt)