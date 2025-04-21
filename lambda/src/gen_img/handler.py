from typing import TypedDict

import boto3
from openai import OpenAI


class Config:
    def __init__(self) -> None:
        self.api_key = get_ssm_parameter("/openai/musabi/api-key")


class Response(TypedDict):
    DishName: str
    EngDishName: str
    Recipe: str


def get_ssm_parameter(name: str) -> str:
    ssm = boto3.client("ssm")
    return ssm.get_parameter(Name=name, WithDecryption=False)["Parameter"]["Value"]


def handler(event, context) -> Response:  # noqa: ANN001, ARG001
    return main()


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


def main() -> Response:
    config = Config()
    client = OpenAI(api_key=config.api_key)
    dish_name = ""
    recipe = ""
    prompt = f"""
{dish_name}という料理の画像を生成してください。レシピは次のとおりです。
{recipe}
"""
    img_url = generate_dish_img(
        client,
        prompt,
    )
    return {
        "DishUrl": img_url,
    }


if __name__ == "__main__":
    print(main())
