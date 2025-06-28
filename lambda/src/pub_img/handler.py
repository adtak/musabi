import os
from typing import Any, TypedDict, cast

from loguru import logger

from src.pub_img import mod
from src.pub_img.client import Client
from src.shared.config import MetaConfig
from src.shared.logging import log_exec


class ImageArgs(TypedDict):
    image_bucket: str
    title_image_key: str
    image_key: str


class TextArgs(TypedDict):
    dish_name: str
    genres: str
    main_food: str
    theme: str
    ingredients: str
    steps: str


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:  # noqa: ARG001
    image_bucket = os.getenv("IMAGE_BUCKET")
    if image_bucket is None:
        msg = "IMAGE_BUCKET environment variable is not set"
        raise ValueError(msg)

    title_image_key = cast("str", event.get("TitleImgKey"))
    image_key = cast("str", event.get("ImgKey"))
    dish_name = cast("str", event.get("DishName"))
    genres = cast("str", event.get("Genres"))
    main_food = cast("str", event.get("MainFood"))
    theme = cast("str", event.get("Theme"))
    ingredients = cast("str", event.get("Ingredients"))
    steps = cast("str", event.get("Steps"))
    dry_run = cast("bool", event.get("DryRun", False))
    if not all(
        [
            title_image_key,
            image_key,
            dish_name,
            genres,
            main_food,
            theme,
            ingredients,
            steps,
        ],
    ):
        msg = "Required event fields are missing"
        raise ValueError(msg)

    return main(
        {
            "image_bucket": image_bucket,
            "title_image_key": title_image_key,
            "image_key": image_key,
        },
        {
            "dish_name": dish_name,
            "genres": genres,
            "main_food": main_food,
            "theme": theme,
            "ingredients": ingredients,
            "steps": steps,
        },
        dry_run=dry_run,
    )


@log_exec
def main(
    image_args: ImageArgs,
    text_args: TextArgs,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        logger.info(f"DryRun: {dry_run}. Finish no pub image.")
        return {}
    client = Client(MetaConfig())
    title_image_url = mod.create_presigned_url(
        image_args["image_bucket"],
        image_args["title_image_key"],
    )
    image_url = mod.create_presigned_url(
        image_args["image_bucket"],
        image_args["image_key"],
    )
    comments = "※このレシピと写真はAIによって自動で作成されたものです。\nレシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。"  # noqa: E501
    recipe = f"{text_args['dish_name']}のレシピは以下の通りです。\n\n{text_args['ingredients']}\n\n{text_args['steps']}\n\nぜひ試してみてください！"  # noqa: E501, RUF001
    hashtag = f"#レシピ #料理 #お菓子 #クッキング #今日の献立 #{text_args['genres']} #{text_args['main_food']}レシピ #{text_args['theme']}レシピ #AI #AIレシピ"  # noqa: E501
    mod.upload_images(
        client,
        image_urls=[title_image_url, image_url],
        caption=f"\n{text_args['dish_name']}\n\n{comments}\n\n{recipe}\n\n{hashtag}",
    )
    return {}


if __name__ == "__main__":
    main(
        {
            "image_bucket": "",
            "title_image_key": "",
            "image_key": "",
        },
        {
            "dish_name": "",
            "genres": "",
            "main_food": "",
            "theme": "",
            "ingredients": "",
            "steps": "",
        },
        dry_run=True,
    )
