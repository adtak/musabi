"""Tests for gen_text.handler module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from src.gen_text.handler import (
    handler,
    send_request,
    generate_dish_name,
    generate_recipe,
    main,
)


class TestGenTextHandler:
    """Test cases for gen_text handler functions."""

    def test_handler_calls_main(self):
        """Test that handler function calls main."""
        with patch("src.gen_text.handler.main") as mock_main:
            mock_main.return_value = {"DishName": "test", "Recipe": "test recipe"}
            result = handler({}, None)
            mock_main.assert_called_once()
            assert result == {"DishName": "test", "Recipe": "test recipe"}

    @patch("src.gen_text.handler.OpenAI")
    def test_send_request_success(self, mock_openai_class):
        """Test successful OpenAI API request."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Create mock response
        mock_message = ChatCompletionMessage(role="assistant", content="Test response")
        mock_choice = Choice(index=0, message=mock_message, finish_reason="stop")
        mock_completion = ChatCompletion(
            id="test-id",
            choices=[mock_choice],
            created=1234567890,
            model="gpt-4.1-nano",
            object="chat.completion"
        )
        mock_client.chat.completions.create.return_value = mock_completion

        result = send_request(mock_client, "system content", "user content")

        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "system content"},
                {"role": "user", "content": "user content"},
            ],
        )

    def test_send_request_api_error(self, mock_openai_client):
        """Test OpenAI API error handling."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            send_request(mock_openai_client, "system", "user")

    @patch("src.gen_text.handler.send_request")
    def test_generate_dish_name_success(self, mock_send_request):
        """Test successful dish name generation."""
        mock_send_request.return_value = "これは「トマトとバジルのパスタ」です。"
        mock_client = MagicMock()

        result = generate_dish_name(mock_client)

        assert result == "トマトとバジルのパスタ"
        mock_send_request.assert_called_once()

    @patch("src.gen_text.handler.send_request")
    def test_generate_dish_name_no_match(self, mock_send_request):
        """Test dish name generation when no quotes found."""
        mock_send_request.return_value = "料理名が見つかりません"
        mock_client = MagicMock()

        with pytest.raises(IndexError):
            generate_dish_name(mock_client)

    @patch("src.gen_text.handler.send_request")
    def test_generate_recipe_success(self, mock_send_request):
        """Test successful recipe generation."""
        expected_recipe = "トマトとバジルのパスタのレシピは以下の通りです。"
        mock_send_request.return_value = expected_recipe
        mock_client = MagicMock()

        result = generate_recipe(mock_client, "トマトとバジルのパスタ")

        assert result == expected_recipe
        mock_send_request.assert_called_once()

    @patch("src.gen_text.handler.OpenAIConfig")
    @patch("src.gen_text.handler.OpenAI")
    @patch("src.gen_text.handler.generate_dish_name")
    @patch("src.gen_text.handler.generate_recipe")
    def test_main_success(
        self,
        mock_generate_recipe,
        mock_generate_dish_name,
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
        
        mock_generate_dish_name.return_value = "テストパスタ"
        mock_generate_recipe.return_value = "テストレシピ"

        result = main()

        assert result == {
            "DishName": "テストパスタ",
            "Recipe": "テストレシピ",
        }
        mock_config_class.assert_called_once()
        mock_openai_class.assert_called_once_with(api_key="test-api-key")
        mock_generate_dish_name.assert_called_once_with(mock_client)
        mock_generate_recipe.assert_called_once_with(mock_client, "テストパスタ")

    @patch("src.gen_text.handler.OpenAIConfig")
    def test_main_config_error(self, mock_config_class):
        """Test main function when config fails."""
        mock_config_class.side_effect = Exception("Config error")

        with pytest.raises(Exception, match="Config error"):
            main()

    @patch("src.gen_text.handler.OpenAIConfig")
    @patch("src.gen_text.handler.OpenAI")
    def test_main_openai_client_error(self, mock_openai_class, mock_config_class):
        """Test main function when OpenAI client creation fails."""
        mock_config = MagicMock()
        mock_config.api_key = "test-api-key"
        mock_config_class.return_value = mock_config
        
        mock_openai_class.side_effect = Exception("OpenAI client error")

        with pytest.raises(Exception, match="OpenAI client error"):
            main()