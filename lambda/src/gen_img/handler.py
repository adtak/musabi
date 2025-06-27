import os
from io import BytesIO
from typing import Any, cast

from google import genai
from google.genai import types
from loguru import logger
from PIL import Image

from src.shared.config import GeminiConfig
from src.shared.logging import log_exec
from src.shared.s3 import put_image
from src.shared.type import GenImgResponse


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
    bucket_name = os.getenv("IMAGE_BUCKET")
    if bucket_name is None:
        msg = "IMAGE_BUCKET environment variable is not set"
        raise ValueError(msg)
    dish_name = cast("str", event.get("DishName"))
    ingredients = cast("str", event.get("Ingredients"))
    exec_name = cast("str", event.get("ExecName"))
    if not all([dish_name, ingredients, exec_name]):
        msg = "Required event fields are missing"
        raise ValueError(msg)

    return main(dish_name, ingredients, bucket_name, exec_name)


@log_exec
def main(
    dish_name: str,
    ingredients: str,
    bucket_name: str,
    exec_name: str,
) -> GenImgResponse:
    config = GeminiConfig()
    client = genai.Client(api_key=config.api_key)
    contents = (
        f"{dish_name}という料理の写真をレシピ本に掲載されている写真のように生成してください。\n"
        f"材料は次のとおりです。\n{ingredients}\n"
        "解像度は1024x1024でお願いします。"
        "ただし、生成する画像に材料に関する説明文は入れないでください。"
    )
    image = generate_dish_img(client, contents)
    img_key = put_image(image, bucket_name, f"{exec_name}/1.png")
    return {
        "ImgKey": img_key,
    }


if __name__ == "__main__":
    main("", "", "", "")
