import re

import boto3
import openai


class Config:
    def __init__(self) -> None:
        self.api_key = get_ssm_parameter("/openai/musabi/api-key")


def get_ssm_parameter(name: str):
    ssm = boto3.client("ssm")
    value = ssm.get_parameter(Name=name, WithDecryption=False)["Parameter"]["Value"]
    return value


def handler(event, context):
    return main(event)


def send_request(system_content: str, user_content: str):
    results = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
    )
    return results["choices"][0]["message"]["content"]


def generate_dish_name():
    content = send_request(
        "日本語で返答してください。",
        "独創性のあるスイーツの名前を一つ提案してください。返答はスイーツの名前のみを「」で囲って返答してください。",
    )
    return re.findall(r"「(.*)」", content)[0]


def translate_dish_name(dish_name):
    content = send_request("次の料理名を英語に翻訳してください。", dish_name)
    return content


def generate_recipe(dish_name):
    content = send_request(
        "日本語で返答してください。情報が存在しない場合でも、架空の情報で提案してください。",
        f"「{dish_name}」というスイーツのレシピを教えてください。",
    )
    return content


def main(event):
    config = Config()
    openai.api_key = config.api_key
    dish_name = generate_dish_name()
    eng_dish_name = translate_dish_name(dish_name)
    recipe = generate_recipe(dish_name)
    results = {
        "DishName": dish_name,
        "EngDishName": eng_dish_name,
        "Recipe": recipe,
    }
    print(results)
    return results
