from typing import Any, cast

from openai import OpenAI

from src.shared.config import OpenAIConfig
from src.shared.logging import log_exec
from src.shared.type import GenImgResponse


def send_request(client: OpenAI, prompt: str) -> str:
    results = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    url = results.data[0].url
    if url is None:
        msg = "Generated image URL is None"
        raise ValueError(msg)
    return url


def generate_dish_img(client: OpenAI, prompt: str) -> str:
    return send_request(client, prompt)


def handler(event: dict[str, Any], context: object) -> GenImgResponse:  # noqa: ARG001
    dish_name = cast("str", event.get("DishName"))
    recipe = cast("str", event.get("Recipe"))
    if not all([dish_name, recipe]):
        msg = "Required event fields are missing"
        raise ValueError(msg)

    return main(
        dish_name,
        recipe,
    )


@log_exec
def main(dish_name: str, recipe: str) -> GenImgResponse:
    config = OpenAIConfig()
    client = OpenAI(api_key=config.api_key)
    prompt = (
        f"{dish_name}という料理の写真をインスタグラムに投稿される写真風に生成してください。レシピは次のとおりです。"
        f"{recipe}"
        "ただし、写真に文字は絶対に写さないでください。"
    )
    img_url = generate_dish_img(client, prompt)
    return {
        "ImgUrl": img_url,
    }


if __name__ == "__main__":
    main("", "")
