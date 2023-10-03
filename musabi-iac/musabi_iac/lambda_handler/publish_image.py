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

    def create_image_media(
        self,
        image_url: str,
        caption: str,
        is_carousel_item: bool,
    ) -> Any:
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
    ) -> Any:
        url = self.config.endpoint_base + self.config.account_id + "/media"
        request = {
            "access_token": self.config.access_token,
            "caption": caption,
            "media_type": media_type,
            "children": children,
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
    if event.get("DryRun"):
        return {}
    else:
        main(event)


def main(event) -> None:
    client = Client(Config())
    title_image_url = create_presigned_url(
        os.environ["ImageBucket"], event.get("TitleImageKey")
    )
    image_url = create_presigned_url(os.environ["ImageBucket"], event.get("ImageKey"))
    comments = (
        "※このレシピと写真はAIによって自動で作成されたものです。\nレシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。"
    )
    dish_name = event.get("DishName")
    recipe = event.get("Recipe")
    hashtag = "#レシピ #料理 #お菓子 #クッキング #AI #AIレシピ"
    response = upload_images(
        client,
        image_urls=[title_image_url, image_url],
        caption=f"\n{dish_name}\n\n{comments}\n\n{recipe}\n\n{hashtag}",
    )
    print(response)
    return {}


def upload_images(client: Client, image_urls: list[str], caption: str) -> Any:
    container_ids = []
    for image_url in image_urls:
        response = client.create_image_media(
            image_url=image_url,
            caption=caption,
            is_carousel_item=True,
        )
        print(response)
        conainer_id = response["id"]
        wait_container_finish(conainer_id)
        container_ids.append(conainer_id)
    response = client.create_carousel_media(
        caption=caption, media_type="CAROUSEL", children=container_ids
    )
    print(response)
    conainer_id = response["id"]
    wait_container_finish(conainer_id)
    media_id = client.publish_media(creation_id=conainer_id)["id"]
    return client.get_media(media_id=media_id)


def upload_image(client: Client, image_url: str, caption: str) -> Any:
    response = client.create_image_media(
        image_url=image_url,
        caption=caption,
        is_carousel_item=False,
    )
    print(response)
    conainer_id = response["id"]
    wait_container_finish(conainer_id)
    media_id = client.publish_media(creation_id=conainer_id)["id"]
    return client.get_media(media_id=media_id)


def wait_container_finish(client: Client, container_id: str) -> None:
    status_code = "IN_PROGRESS"
    while status_code != "FINISHED":
        status_code = client.get_container_status(container_id=container_id)[
            "status_code"
        ]
        time.sleep(3)
    return None


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
        print("Fail to generate Presigned-URL")
        raise e
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
