from loguru import logger
from openai import OpenAI

from src.shared.config import OpenAIConfig
from src.shared.type import GenImgResponse


def handler(event: dict, context: object) -> GenImgResponse:  # noqa: ARG001
    return main(
        dish_name=event.get("DishName", ""),
        recipe=event.get("Recipe", ""),
    )


def send_request(client: OpenAI, prompt: str) -> str:
    results = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    return results.data[0].url


def generate_dish_img(client: OpenAI, prompt: str) -> str:
    return send_request(client, prompt)


def main(dish_name: str, recipe: str) -> GenImgResponse:
    config = OpenAIConfig()
    client = OpenAI(api_key=config.api_key)
    prompt = f"""
{dish_name}という料理の画像を生成してください。レシピは次のとおりです。
{recipe}
"""
    img_url = generate_dish_img(client, prompt)
    return {
        "ImgUrl": img_url,
    }


if __name__ == "__main__":
    logger.info(main("", ""))
