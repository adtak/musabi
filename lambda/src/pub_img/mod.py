import time

import boto3
import botocore
from botocore.exceptions import ClientError
from loguru import logger

from src.pub_img.client import Client


def upload_images(client: Client, image_urls: list[str], caption: str) -> None:
    container_ids = []
    for image_url in image_urls:
        container_id = _create_and_wait_for_image_media(
            client=client,
            image_url=image_url,
            caption=caption,
            is_carousel_item=True,
        )
        container_ids.append(container_id)
    response = client.create_carousel_media(
        caption=caption,
        media_type="CAROUSEL",
        children=container_ids,
    )
    container_id = response["id"]
    wait_container_finish(client, container_id)
    media_id = client.publish_media(creation_id=container_id)["id"]
    response = client.get_media(media_id=media_id)


def upload_image(client: Client, image_url: str, caption: str) -> None:
    container_id = _create_and_wait_for_image_media(
        client=client,
        image_url=image_url,
        caption=caption,
        is_carousel_item=False,
    )
    media_id = client.publish_media(creation_id=container_id)["id"]
    response = client.get_media(media_id=media_id)


def _create_and_wait_for_image_media(
    client: Client, image_url: str, caption: str, is_carousel_item: bool
) -> str:
    """Create image media and wait for container to finish processing.
    
    Args:
        client: SNS client instance
        image_url: URL of the image to upload
        caption: Caption for the image
        is_carousel_item: Whether this image is part of a carousel
    
    Returns:
        Container ID of the processed media
    """
    response = client.create_image_media(
        image_url=image_url,
        caption=caption,
        is_carousel_item=is_carousel_item,
    )
    container_id = response["id"]
    wait_container_finish(client, container_id)
    return container_id


def wait_container_finish(client: Client, container_id: str) -> None:
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
