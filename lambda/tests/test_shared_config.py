"""Tests for shared.config module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.shared.config import get_ssm_parameter, OpenAIConfig, MetaConfig


class TestSharedConfig:
    """Test cases for shared config functions and classes."""

    @patch("src.shared.config.boto3.client")
    def test_get_ssm_parameter_success(self, mock_boto3_client):
        """Test successful SSM parameter retrieval."""
        mock_ssm_client = MagicMock()
        mock_ssm_client.get_parameter.return_value = {
            "Parameter": {"Value": "test-secret-value"}
        }
        mock_boto3_client.return_value = mock_ssm_client

        result = get_ssm_parameter("/test/parameter")

        assert result == "test-secret-value"
        mock_boto3_client.assert_called_once_with("ssm")
        mock_ssm_client.get_parameter.assert_called_once_with(
            Name="/test/parameter", WithDecryption=True
        )

    @patch("src.shared.config.boto3.client")
    def test_get_ssm_parameter_error(self, mock_boto3_client):
        """Test SSM parameter retrieval error."""
        mock_ssm_client = MagicMock()
        mock_ssm_client.get_parameter.side_effect = Exception("Parameter not found")
        mock_boto3_client.return_value = mock_ssm_client

        with pytest.raises(Exception, match="Parameter not found"):
            get_ssm_parameter("/nonexistent/parameter")

    @patch("src.shared.config.get_ssm_parameter")
    def test_openai_config_api_key_cached(self, mock_get_ssm_parameter):
        """Test OpenAI config API key caching."""
        mock_get_ssm_parameter.return_value = "openai-api-key"
        
        config = OpenAIConfig()
        
        # First access should call SSM
        api_key1 = config.api_key
        assert api_key1 == "openai-api-key"
        mock_get_ssm_parameter.assert_called_once_with("/openai/musabi/api-key")
        
        # Second access should use cached value
        api_key2 = config.api_key
        assert api_key2 == "openai-api-key"
        assert mock_get_ssm_parameter.call_count == 1  # Should not be called again

    @patch("src.shared.config.get_ssm_parameter")
    def test_openai_config_api_key_error(self, mock_get_ssm_parameter):
        """Test OpenAI config API key retrieval error."""
        mock_get_ssm_parameter.side_effect = Exception("SSM error")
        
        config = OpenAIConfig()
        
        with pytest.raises(Exception, match="SSM error"):
            _ = config.api_key

    @patch("src.shared.config.get_ssm_parameter")
    def test_meta_config_properties_cached(self, mock_get_ssm_parameter):
        """Test Meta config properties caching."""
        mock_get_ssm_parameter.side_effect = [
            "meta-access-token",
            "meta-account-id", 
            "meta-version",
            "meta-graph-url"
        ]
        
        config = MetaConfig()
        
        # First access should call SSM for each property
        access_token1 = config.access_token
        account_id1 = config.account_id
        version1 = config.version
        graph_url1 = config.graph_url
        
        assert access_token1 == "meta-access-token"
        assert account_id1 == "meta-account-id"
        assert version1 == "meta-version"
        assert graph_url1 == "meta-graph-url"
        
        # Second access should use cached values
        access_token2 = config.access_token
        account_id2 = config.account_id
        version2 = config.version
        graph_url2 = config.graph_url
        
        assert access_token2 == "meta-access-token"
        assert account_id2 == "meta-account-id"
        assert version2 == "meta-version"
        assert graph_url2 == "meta-graph-url"
        
        # Should only call SSM once per property
        assert mock_get_ssm_parameter.call_count == 4

    @patch("src.shared.config.get_ssm_parameter")
    def test_meta_config_endpoint_base(self, mock_get_ssm_parameter):
        """Test Meta config endpoint_base property."""
        mock_get_ssm_parameter.side_effect = [
            "https://graph.facebook.com",
            "v1.0"
        ]
        
        config = MetaConfig()
        endpoint_base = config.endpoint_base
        
        assert endpoint_base == "https://graph.facebook.com/v1.0/"

    @patch("src.shared.config.get_ssm_parameter")
    def test_meta_config_access_token_error(self, mock_get_ssm_parameter):
        """Test Meta config access token retrieval error."""
        mock_get_ssm_parameter.side_effect = Exception("Access token error")
        
        config = MetaConfig()
        
        with pytest.raises(Exception, match="Access token error"):
            _ = config.access_token

    @patch("src.shared.config.get_ssm_parameter")
    def test_meta_config_account_id_error(self, mock_get_ssm_parameter):
        """Test Meta config account ID retrieval error."""
        mock_get_ssm_parameter.side_effect = Exception("Account ID error")
        
        config = MetaConfig()
        
        with pytest.raises(Exception, match="Account ID error"):
            _ = config.account_id

    @patch("src.shared.config.get_ssm_parameter")
    def test_meta_config_version_error(self, mock_get_ssm_parameter):
        """Test Meta config version retrieval error."""
        mock_get_ssm_parameter.side_effect = Exception("Version error")
        
        config = MetaConfig()
        
        with pytest.raises(Exception, match="Version error"):
            _ = config.version

    @patch("src.shared.config.get_ssm_parameter")
    def test_meta_config_graph_url_error(self, mock_get_ssm_parameter):
        """Test Meta config graph URL retrieval error."""
        mock_get_ssm_parameter.side_effect = Exception("Graph URL error")
        
        config = MetaConfig()
        
        with pytest.raises(Exception, match="Graph URL error"):
            _ = config.graph_url

    def test_openai_config_initialization(self):
        """Test OpenAI config initialization."""
        config = OpenAIConfig()
        assert config._api_key is None

    def test_meta_config_initialization(self):
        """Test Meta config initialization."""
        config = MetaConfig()
        assert config._access_token is None
        assert config._account_id is None
        assert config._version is None
        assert config._graph_url is None