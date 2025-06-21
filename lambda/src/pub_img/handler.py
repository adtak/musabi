import os

from loguru import logger

from src.pub_img import mod
from src.pub_img.client import Client
from src.shared.config import MetaConfig


def handler(event: dict, context: object) -> None:  # noqa: ARG001
    dry_run = event.get("DryRun")
    if dry_run:
        logger.info(f"DryRun: {dry_run}. Finish no pub image.")
        return {}
    return main(
        os.getenv("IMAGE_BUCKET"),
        event.get("TitleImgKey"),
        event.get("ImgKey"),
        event.get("DishName"),
        event.get("Recipe"),
    )


def main(
    image_bucket: str,
    title_image_key: str,
    image_key: str,
    dish_name: str,
    recipe: str,
) -> None:
    client = Client(MetaConfig())
    title_image_url = mod.create_presigned_url(
        image_bucket,
        title_image_key,
    )
    image_url = mod.create_presigned_url(image_bucket, image_key)
    comments = "※このレシピと写真はAIによって自動で作成されたものです。\nレシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。"  # noqa: E501
    hashtag = "#レシピ #料理 #お菓子 #クッキング #AI #AIレシピ"
    mod.upload_images(
        client,
        image_urls=[title_image_url, image_url],
        caption=f"\n{dish_name}\n\n{comments}\n\n{recipe}\n\n{hashtag}",
    )
    return {}


if __name__ == "__main__":
    main("", "", "", "", "")
