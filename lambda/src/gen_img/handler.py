import os
from io import BytesIO
from typing import Any, Self

from google import genai
from google.genai import types
from loguru import logger
from PIL import Image
from pydantic import BaseModel

from src.shared.config import GeminiConfig
from src.shared.logging import log_exec
from src.shared.s3 import put_image
from src.shared.type import GenImgResponse


class GenImgArgs(BaseModel):
    bucket_name: str
    dish_name: str
    ingredients: str
    exec_name: str
    parallel_index: int

    @classmethod
    def from_event(cls, event: dict[str, Any]) -> Self:
        return cls.model_validate(
            {
                "bucket_name": os.getenv("IMAGE_BUCKET"),
                "dish_name": event.get("DishName"),
                "ingredients": event.get("Ingredients"),
                "exec_name": event.get("ExecName"),
                "parallel_index": event.get("ParallelIndex"),
            },
        )


def generate_dish_img(client: genai.Client, contents: str) -> Image.Image:
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    if (
        response.candidates is None
        or response.candidates[0].content is None
        or response.candidates[0].content.parts is None
    ):
        msg = "Generated image is None."
        raise RuntimeError(msg)

    image = None
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            logger.info(f"Text response: {part.text}")
        elif part.inline_data is not None and part.inline_data.data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
    if image is None:
        msg = "Generated image is None."
        raise RuntimeError(msg)
    return image


def handler(event: dict[str, Any], context: object) -> GenImgResponse:  # noqa: ARG001
    return main(GenImgArgs.from_event(event))


@log_exec
def main(
    args: GenImgArgs,
) -> GenImgResponse:
    config = GeminiConfig()
    client = genai.Client(api_key=config.api_key)
    contents = (
        f"{args.dish_name}という料理の写真を、プロの写真家が撮影したレストランの宣材写真のように生成してください。\n"
        f"材料は次のとおりです。\n{args.ingredients}\n"
        "撮影スタイル:\n"
        "- 少し引いたアングルで、料理全体とお皿、周囲の空間も含めて撮影\n"
        "- 高級レストランの上品で洗練された雰囲気\n"
        "- プロの照明技術による美しい光の演出\n"
        "- 料理だけでなく、テーブルセッティングや背景も考慮した構図\n"
        "- 商業用写真として使用できるクオリティ\n"
        "解像度は1024x1024でお願いします。"
        "ただし、生成する画像に材料に関する説明文は入れないでください。"
    )
    image = generate_dish_img(client, contents)
    img_key = put_image(
        image,
        args.bucket_name,
        f"{args.exec_name}/1-{args.parallel_index}.png",
    )
    return {
        "ImgKey": img_key,
    }


if __name__ == "__main__":
    main(
        GenImgArgs(
            bucket_name="",
            dish_name="",
            ingredients="",
            exec_name="",
            parallel_index=0,
        ),
    )
