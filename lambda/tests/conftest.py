"""Shared test fixtures and configuration."""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_ssm_parameter():
    """Mock SSM parameter response."""
    return {
        "Parameter": {
            "Value": "test-api-key"
        }
    }


@pytest.fixture
def sample_gen_text_response():
    """Sample response for gen_text module."""
    return {
        "DishName": "トマトとバジルのパスタ",
        "Recipe": "トマトとバジルのパスタのレシピは以下の通りです。\n\n材料:\n- パスタ 200g\n- トマト 2個\n- バジル 適量"
    }


@pytest.fixture
def sample_gen_img_response():
    """Sample response for gen_img module."""
    return {
        "ImgUrl": "https://example.com/generated-image.png"
    }


@pytest.fixture
def sample_lambda_event():
    """Sample Lambda event."""
    return {
        "DishName": "トマトとバジルのパスタ",
        "Recipe": "サンプルレシピ",
        "ImgUrl": "https://example.com/image.png",
        "ExecName": "test-execution"
    }