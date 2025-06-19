import boto3


def get_ssm_parameter(name: str) -> str:
    """Get parameter from AWS Systems Manager Parameter Store."""
    ssm = boto3.client("ssm")
    return ssm.get_parameter(Name=name, WithDecryption=False)["Parameter"]["Value"]


class OpenAIConfig:
    """Configuration for OpenAI API."""
    
    def __init__(self) -> None:
        self._api_key = None
    
    @property
    def api_key(self) -> str:
        """Get OpenAI API key from SSM (lazy loaded)."""
        if self._api_key is None:
            self._api_key = get_ssm_parameter("/openai/musabi/api-key")
        return self._api_key


class MetaConfig:
    """Configuration for Meta (Instagram) API."""
    
    def __init__(self) -> None:
        self._access_token = None
        self._account_id = None
        self._version = None
        self._graph_url = None
    
    @property
    def access_token(self) -> str:
        """Get Meta access token from SSM (lazy loaded)."""
        if self._access_token is None:
            self._access_token = get_ssm_parameter("/meta/musabi/access-token")
        return self._access_token
    
    @property
    def account_id(self) -> str:
        """Get Meta account ID from SSM (lazy loaded)."""
        if self._account_id is None:
            self._account_id = get_ssm_parameter("/meta/musabi/account-id")
        return self._account_id
    
    @property
    def version(self) -> str:
        """Get Meta API version from SSM (lazy loaded)."""
        if self._version is None:
            self._version = get_ssm_parameter("/meta/musabi/version")
        return self._version
    
    @property
    def graph_url(self) -> str:
        """Get Meta Graph API URL from SSM (lazy loaded)."""
        if self._graph_url is None:
            self._graph_url = get_ssm_parameter("/meta/musabi/graph-url")
        return self._graph_url

    @property
    def endpoint_base(self) -> str:
        return f"{self.graph_url}/{self.version}/"