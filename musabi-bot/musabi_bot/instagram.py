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
            "is_carousel_item": False,
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

    def get_content_publishing_limit(self) -> Any:
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


def upload_image(client: Client, image_url: str, caption: str) -> Any:
    conainer_id = client.create_media(image_url=image_url, caption=caption)["id"]
    status_code = "IN_PROGRESS"
    while status_code != "FINISHED":
        print(status_code)
        status_code = client.get_container_status(container_id=conainer_id)[
            "status_code"
        ]
        time.sleep(3)
    media_id = client.publish_media(creation_id=conainer_id)["id"]
    return client.get_media(media_id=media_id)


def main() -> None:
    load_dotenv(".env")
    client = Client(Config())
    response = upload_image(
        client,
        image_url="https://i.seadn.io/gae/04-RumcGPTAplXUZpCwjAEi7G2xcIEJTJenDM0dGirx0d5DqpkBEDt2mvDisz-P_CNkI5XfjREKCMfvlFkl6pFfLule2SXOUkkS-hQ?auto=format&w=1000",
        caption="",
    )
    pprint.pprint(response)


if __name__ == "__main__":
    main()
