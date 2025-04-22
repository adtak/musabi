import re

import boto3
from loguru import logger
from openai import OpenAI

from src.shared.type import GenTextResponse


class Config:
    def __init__(self) -> None:
        self.api_key = get_ssm_parameter("/openai/musabi/api-key")


def get_ssm_parameter(name: str) -> str:
    ssm = boto3.client("ssm")
    return ssm.get_parameter(Name=name, WithDecryption=False)["Parameter"]["Value"]


def handler(event: dict) -> GenTextResponse:  # noqa: ARG001
    return main()


def send_request(client: OpenAI, system_content: str, user_content: str) -> str:
    results = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
    )
    return results.choices[0].message.content


def generate_dish_name(client: OpenAI) -> str:
    user_content = """
あなたは一流のシェフであり、世界中のあらゆる料理について熟知しています。
また、探究心が強く、独創的で画期的な料理のレシピを常日頃から創作しています。
独創的でおしゃれな料理の名前を一つ提案してください。
また、料理の名前には食材の名前を入れてください。
ただし、生き物の名前を入れないでください。
返答は料理の名前のみを「」で囲って返答してください。
"""
    content = send_request(client, "日本語で返答してください。", user_content)
    return re.findall(r"「(.*)」", content)[0]


def generate_recipe(client: OpenAI, dish_name: str) -> str:
    user_content = f"""
「{dish_name}」という料理のレシピを教えてください。
返答は「{dish_name}のレシピは以下の通りです。」から始めてください。
"""
    return send_request(
        client,
        "日本語で返答してください。情報が存在しない場合でも、架空の情報で提案してください。",
        user_content,
    )


def main() -> GenTextResponse:
    config = Config()
    client = OpenAI(api_key=config.api_key)
    dish_name = generate_dish_name(client)
    recipe = generate_recipe(client, dish_name)
    return {
        "DishName": dish_name,
        "Recipe": recipe,
    }


if __name__ == "__main__":
    logger.info(main())
