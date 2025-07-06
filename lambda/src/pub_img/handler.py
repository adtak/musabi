import os
from typing import Any, Self

from loguru import logger
from pydantic import BaseModel

from src.pub_img import mod
from src.pub_img.client import Client
from src.shared.config import MetaConfig
from src.shared.logging import log_exec


class PubImgArgs(BaseModel):
    image_bucket: str
    title_image_key: str
    image_key: str
    dish_name: str
    genres: str
    main_food: str
    theme: str
    ingredients: str
    steps: str
    dry_run: bool

    @classmethod
    def from_event(cls, event: dict[str, Any]) -> Self:
        return cls.model_validate(
            {
                "image_bucket": os.getenv("IMAGE_BUCKET"),
                "title_image_key": event.get("TitleImgKey"),
                "image_key": event.get("ImgKey"),
                "dish_name": event.get("DishName"),
                "genres": event.get("Genres"),
                "main_food": event.get("MainFood"),
                "theme": event.get("Theme"),
                "ingredients": event.get("Ingredients"),
                "steps": event.get("Steps"),
                "dry_run": event.get("DryRun", False),
            },
        )


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:  # noqa: ARG001
    return main(PubImgArgs.from_event(event))


@log_exec
def main(args: PubImgArgs) -> dict[str, Any]:
    if args.dry_run:
        logger.info(f"DryRun: {args.dry_run}. Finish no pub image.")
        return {}
    client = Client(MetaConfig())
    image_url = mod.create_presigned_url(
        args.image_bucket,
        args.image_key,
    )
    comments = "※このレシピと写真はAIによって自動で作成されたものです。\nレシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。"  # noqa: E501
    recipe = f"{args.dish_name}のレシピは以下の通りです。\n\n{args.ingredients}\n\n{args.steps}\n\nぜひ試してみてください！"  # noqa: E501, RUF001
    hashtag = f"#レシピ #料理 #お菓子 #クッキング #今日の献立 #{args.genres} #{args.main_food}レシピ #{args.theme}レシピ #AI #AIレシピ"  # noqa: E501
    mod.upload_image(
        client,
        image_url=image_url,
        caption=f"\n{args.dish_name}\n\n{comments}\n\n{recipe}\n\n{hashtag}",
    )
    return {}


if __name__ == "__main__":
    main(
        PubImgArgs(
            image_bucket="",
            title_image_key="",
            image_key="",
            dish_name="",
            genres="",
            main_food="",
            theme="",
            ingredients="",
            steps="",
            dry_run=True,
        ),
    )
