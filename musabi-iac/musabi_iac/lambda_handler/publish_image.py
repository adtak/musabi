import json
import os
import time
from typing import Any, Dict

import boto3
import botocore
import requests
from botocore.exceptions import ClientError


class Config:
    def __init__(self) -> None:
        self.access_token = get_ssm_parameter("/meta/musabi/access-token")
        self.account_id = get_ssm_parameter("/meta/musabi/account-id")
        self.version = get_ssm_parameter("/meta/musabi/version")
        self.graph_url = get_ssm_parameter("/meta/musabi/graph-url")

    @property
    def endpoint_base(self) -> str:
        return f"{self.graph_url}/{self.version}/"


class Client:
    def __init__(self, config: Config) -> None:
        self.config = config

    def get_user_media(self) -> Any:
        url = self.config.endpoint_base + self.config.account_id + "/media"
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


def handler(event, context):
    main(event)


def main(event) -> None:
    client = Client(Config())
    url = create_presigned_url(os.environ["ImageBucket"], event.get("ImageKey"))
    # response = client.get_user_media()
    comments = "※このレシピはAIによって自動で作成されたものです。\nレシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。"
    dish_name = event.get("DishName")
    recipe = event.get("Recipe")
    response = upload_image(
        client,
        image_url=url,
        caption=f"\n{dish_name}\n\n{comments}\n\n{recipe}",
    )
    print(response)
    return {}


def upload_image(client: Client, image_url: str, caption: str) -> Any:
    response = client.create_media(image_url=image_url, caption=caption)
    print(response)
    conainer_id = response["id"]
    status_code = "IN_PROGRESS"
    while status_code != "FINISHED":
        status_code = client.get_container_status(container_id=conainer_id)[
            "status_code"
        ]
        time.sleep(3)
    media_id = client.publish_media(creation_id=conainer_id)["id"]
    return client.get_media(media_id=media_id)


def get_ssm_parameter(name: str):
    ssm = boto3.client("ssm")
    value = ssm.get_parameter(Name=name, WithDecryption=False)["Parameter"]["Value"]
    return value


def create_presigned_url(bucket_name, object_name, expiration=300):
    s3_client = boto3.client(
        "s3", config=botocore.client.Config(signature_version="s3v4")
    )
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        return None
    print(f"Generated URL: {url}")
    return url


def call_api(url: str, method: str, request: Dict[str, Any]) -> Any:
    print(f"Request URL: ({method}) {url}")
    if method == "GET":
        response = requests.get(url, request)
    elif method == "POST":
        response = requests.post(url, request)
    else:
        raise ValueError("Method not supported.")
    return json.loads(response.content)
