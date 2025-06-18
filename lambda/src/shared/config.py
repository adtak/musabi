import boto3


def get_ssm_parameter(name: str) -> str:
    """Get parameter from AWS Systems Manager Parameter Store."""
    ssm = boto3.client("ssm")
    return ssm.get_parameter(Name=name, WithDecryption=False)["Parameter"]["Value"]


class OpenAIConfig:
    """Configuration for OpenAI API."""
    
    def __init__(self) -> None:
        self.api_key = get_ssm_parameter("/openai/musabi/api-key")


class MetaConfig:
    """Configuration for Meta (Instagram) API."""
    
    def __init__(self) -> None:
        self.access_token = get_ssm_parameter("/meta/musabi/access-token")
        self.account_id = get_ssm_parameter("/meta/musabi/account-id")
        self.version = get_ssm_parameter("/meta/musabi/version")
        self.graph_url = get_ssm_parameter("/meta/musabi/graph-url")

    @property
    def endpoint_base(self) -> str:
        return f"{self.graph_url}/{self.version}/"