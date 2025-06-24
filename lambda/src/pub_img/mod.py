import time
from typing import cast

import boto3
import botocore
from botocore.exceptions import ClientError
from loguru import logger

from src.pub_img.client import Client


def upload_images(client: Client, image_urls: list[str], caption: str) -> None:
    container_ids = []
    for image_url in image_urls:
        container_id = _create_and_wait_for_image(
            client=client,
            image_url=image_url,
            caption=caption,
            is_carousel_item=True,
        )
        container_ids.append(container_id)
    container_id = _create_and_wait_for_carousel(
        client=client,
        children=container_ids,
        caption=caption,
    )
    client.publish_media(creation_id=container_id)["id"]


def _create_and_wait_for_image(
    client: Client,
    image_url: str,
    caption: str,
    *,
    is_carousel_item: bool,
) -> str:
    response = client.create_image_media(
        image_url=image_url,
        caption=caption,
        is_carousel_item=is_carousel_item,
    )
    container_id = cast("str", response["id"])
    _wait_container_finish(client, container_id)
    return container_id


def _create_and_wait_for_carousel(
    client: Client,
    children: list[str],
    caption: str,
) -> str:
    response = client.create_carousel_media(
        caption=caption,
        media_type="CAROUSEL",
        children=children,
    )
    container_id = cast("str", response["id"])
    _wait_container_finish(client, container_id)
    return container_id


def _wait_container_finish(client: Client, container_id: str) -> None:
    status_code = "IN_PROGRESS"
    while status_code != "FINISHED":
        status_code = client.get_container_status(container_id=container_id)[
            "status_code"
        ]
        time.sleep(3)


def create_presigned_url(
    bucket_name: str,
    object_name: str,
    expiration: int = 300,
) -> str:
    s3_client = boto3.client(
        "s3",
        config=botocore.client.Config(signature_version="s3v4"),
    )
    try:
        url: str = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except ClientError:
        logger.info("Fail to generate Presigned-URL")
        raise
    logger.info(f"Generated URL: {url}")
    return url
