import json
import os
import pprint
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv


class Config:
    def __init__(self) -> None:
        self.access_token = os.environ["ACCESS_TOKEN"]
        self.app_id = os.environ["APP_ID"]
        self.app_secret = os.environ["APP_SECRET"]
        self.account_id = os.environ["ACCOUNT_ID"]
        self.version = os.environ["VERSION"]
        self.graph_url = os.environ["GRAPH_URL"]

    @property
    def endpoint_base(self) -> str:
        return f"{self.graph_url}/{self.version}/"


def call_api(url: str, method: str, request: Dict[str, Any]) -> Any:
    if method == "GET":
        response = requests.get(url, request)
    elif method == "POST":
        response = requests.post(url, request)
    else:
        raise ValueError("Method not supported.")
    return json.loads(response.content)


class Client:
    def __init__(self, config: Config) -> None:
        self.config = config

    def get_medias(self, paging_url: Optional[str] = None) -> Any:
        request = {
            "access_token": self.config.access_token,
            "fields": ",".join(
                [
                    "id",
                    "caption",
                    "media_type",
                    "media_url",
                    "permalink",
                    "thumbnail_url",
                    "timestamp",
                    "username",
                ]
            ),
        }
        if paging_url is None:
            url = self.config.endpoint_base + self.config.account_id + "/media"
        else:
            url = paging_url
        return call_api(url, "GET", request)

    def get_media(self, media_id: str) -> Any:
        url = self.config.endpoint_base + media_id
        request = {
            "access_token": self.config.access_token,
            "fields": ",".join(
                [
                    "id",
                    "caption",
                    "media_type",
                    "media_url",
                    "permalink",
                    "thumbnail_url",
                    "timestamp",
                    "username",
                ]
            ),
        }
        return call_api(url, "GET", request)

    def create_media(self, image_url: str, caption: str) -> Any:
        url = self.config.endpoint_base + self.config.account_id + "/media"
        request = {
            "access_token": self.config.access_token,
            "image_url": image_url,
            "caption": caption,
            "is_carousel_item": True,
        }
        return call_api(url, "POST", request)

    def get_container_status(self, container_id: str) -> Any:
        url = self.config.endpoint_base + container_id
        request = {
            "access_token": self.config.access_token,
            "fields": ",".join(["id", "status", "status_code"]),
        }
        return call_api(url, "GET", request)

    def publish_media(self, creation_id: str) -> Any:
        url = self.config.endpoint_base + self.config.account_id + "/media_publish"
        request = {
            "access_token": self.config.access_token,
            "creation_id": creation_id,
        }
        return call_api(url, "POST", request)

    def get_content_publishing_limit(self):
        url = (
            self.config.endpoint_base
            + self.config.account_id
            + "/content_publishing_limit"
        )
        request = {
            "access_token": self.config.access_token,
            "fields": ",".join(["config", "quota_usage"]),
        }
        return call_api(url, "GET", request)


def instagram_upload_image(media_url, media_caption):
    client = Client(Config())
    result = client.create_media("IMAGE", media_url, media_caption)
    media_id = result["id"]

    status = "IN_PROGRESS"
    while status != "FINISHED":
        result = client.get_media(media_id)
        status = result["status_code"]
        time.sleep(5)
    result = client.publish_media(media_id)


def main() -> None:
    load_dotenv(".env")
    client = Client(Config())
    response = client.get_media("17879502580930621")
    pprint.pprint(response)


if __name__ == "__main__":
    main()
