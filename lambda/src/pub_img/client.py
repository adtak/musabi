import json
from typing import Any

import requests
from loguru import logger

from src.shared.config import MetaConfig


def create_fields(fields: list[str]) -> str:
    return ",".join(fields)


def call_api(url: str, method: str, request: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Request: ({method}) {url}")
    if method == "GET":
        response = requests.get(url, request, timeout=10)
    elif method == "POST":
        response = requests.post(url, json=request, timeout=10)
    else:
        msg = "Method not supported."
        raise ValueError(msg)
    results = json.loads(response.content)
    logger.info(f"Response: {results}")
    return results


class Client:
    def __init__(self, config: MetaConfig) -> None:
        self.config = config

    def get_user_media(self) -> dict[str, Any]:
        url = self.config.endpoint_base + self.config.account_id + "/media"
        request = {
            "access_token": self.config.access_token,
            "fields": create_fields(
                [
                    "id",
                    "caption",
                    "media_type",
                    "media_url",
                    "permalink",
                    "thumbnail_url",
                    "timestamp",
                    "username",
                ],
            ),
        }
        return call_api(url, "GET", request)

    def get_media(self, media_id: str) -> dict[str, Any]:
        url = self.config.endpoint_base + media_id
        request = {
            "access_token": self.config.access_token,
            "fields": create_fields(
                [
                    "id",
                    "caption",
                    "media_type",
                    "media_url",
                    "permalink",
                    "thumbnail_url",
                    "timestamp",
                    "username",
                ],
            ),
        }
        return call_api(url, "GET", request)

    def create_image_media(
        self,
        image_url: str,
        caption: str,
        *,
        is_carousel_item: bool,
    ) -> dict[str, Any]:
        url = self.config.endpoint_base + self.config.account_id + "/media"
        request = {
            "access_token": self.config.access_token,
            "image_url": image_url,
            "caption": caption,
            "is_carousel_item": is_carousel_item,
        }
        return call_api(url, "POST", request)

    def create_carousel_media(
        self,
        caption: str,
        media_type: str,
        children: list[str],
    ) -> dict[str, Any]:
        url = self.config.endpoint_base + self.config.account_id + "/media"
        request = {
            "access_token": self.config.access_token,
            "caption": caption,
            "media_type": media_type,
            "children": children,
        }
        return call_api(url, "POST", request)

    def get_container_status(self, container_id: str) -> dict[str, Any]:
        url = self.config.endpoint_base + container_id
        request = {
            "access_token": self.config.access_token,
            "fields": create_fields(["id", "status", "status_code"]),
        }
        return call_api(url, "GET", request)

    def publish_media(self, creation_id: str) -> dict[str, Any]:
        url = self.config.endpoint_base + self.config.account_id + "/media_publish"
        request = {
            "access_token": self.config.access_token,
            "creation_id": creation_id,
        }
        return call_api(url, "POST", request)

    def get_content_publishing_limit(self) -> dict[str, Any]:
        url = (
            self.config.endpoint_base
            + self.config.account_id
            + "/content_publishing_limit"
        )
        request = {
            "access_token": self.config.access_token,
            "fields": create_fields(["config", "quota_usage"]),
        }
        return call_api(url, "GET", request)
