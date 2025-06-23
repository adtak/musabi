from typing import Any, cast

import boto3


def get_ssm_parameter(name: str) -> str:
    ssm = boto3.client("ssm")
    parameter: dict[str, Any] = ssm.get_parameter(Name=name, WithDecryption=True)
    return cast("str", parameter["Parameter"]["Value"])


class OpenAIConfig:
    def __init__(self) -> None:
        self._api_key: str | None = None

    @property
    def api_key(self) -> str:
        if self._api_key is None:
            self._api_key = get_ssm_parameter("/openai/musabi/api-key")
        return self._api_key


class MetaConfig:
    def __init__(self) -> None:
        self._access_token: str | None = None
        self._account_id: str | None = None
        self._version: str | None = None
        self._graph_url: str | None = None

    @property
    def access_token(self) -> str:
        if self._access_token is None:
            self._access_token = get_ssm_parameter("/meta/musabi/access-token")
        return self._access_token

    @property
    def account_id(self) -> str:
        if self._account_id is None:
            self._account_id = get_ssm_parameter("/meta/musabi/account-id")
        return self._account_id

    @property
    def version(self) -> str:
        if self._version is None:
            self._version = get_ssm_parameter("/meta/musabi/version")
        return self._version

    @property
    def graph_url(self) -> str:
        if self._graph_url is None:
            self._graph_url = get_ssm_parameter("/meta/musabi/graph-url")
        return self._graph_url

    @property
    def endpoint_base(self) -> str:
        return f"{self.graph_url}/{self.version}/"
