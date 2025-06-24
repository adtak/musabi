import os
from typing import Any, cast

from loguru import logger

from src.pub_img import mod
from src.pub_img.client import Client
from src.shared.config import MetaConfig
from src.shared.logging import log_exec


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:  # noqa: ARG001
    image_bucket = os.getenv("IMAGE_BUCKET")
    if image_bucket is None:
        msg = "IMAGE_BUCKET environment variable is not set"
        raise ValueError(msg)

    title_image_key = cast("str", event.get("TitleImgKey"))
    image_key = cast("str", event.get("ImgKey"))
    dish_name = cast("str", event.get("DishName"))
    ingredients = cast("str", event.get("Ingredients"))
    steps = cast("str", event.get("Steps"))
    dry_run = cast("bool", event.get("DryRun", False))
    if not all([title_image_key, image_key, dish_name, ingredients, steps]):
        msg = "Required event fields are missing"
        raise ValueError(msg)

    return main(
        image_bucket,
        title_image_key,
        image_key,
        dish_name,
        ingredients,
        steps,
        dry_run=dry_run,
    )


@log_exec
def main(  # noqa: PLR0913
    image_bucket: str,
    title_image_key: str,
    image_key: str,
    dish_name: str,
    ingredients: str,
    steps: str,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        logger.info(f"DryRun: {dry_run}. Finish no pub image.")
        return {}
    client = Client(MetaConfig())
    title_image_url = mod.create_presigned_url(
        image_bucket,
        title_image_key,
    )
    image_url = mod.create_presigned_url(image_bucket, image_key)
    comments = "※このレシピと写真はAIによって自動で作成されたものです。\nレシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。"  # noqa: E501
    recipe = f"{dish_name}のレシピは以下の通りです。\n\n{ingredients}\n\n{steps}\n\nぜひ試してみてください！"  # noqa: E501, RUF001
    hashtag = "#レシピ #料理 #お菓子 #クッキング #AI #AIレシピ"
    mod.upload_images(
        client,
        image_urls=[title_image_url, image_url],
        caption=f"\n{dish_name}\n\n{comments}\n\n{recipe}\n\n{hashtag}",
    )
    return {}


if __name__ == "__main__":
    main("", "", "", "", "", "", dry_run=True)
