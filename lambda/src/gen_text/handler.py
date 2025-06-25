import os
import random
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.shared.config import OpenAIConfig
from src.shared.logging import log_exec
from src.shared.type import GenTextResponse


class Dish(BaseModel):
    dish_name: str = Field(description="料理の名前")
    ingredients: list[str] = Field(description="料理を作るのに使用する材料と分量")
    steps: list[str] = Field(description="料理を作るための手順")

    def ingredients_str(self) -> str:
        ingredients = [f"- {ing}" for ing in self.ingredients]
        return f"【材料】\n{'\n'.join(ingredients)}"

    def steps_str(self) -> str:
        steps = [f"{i}. {step}" for i, step in enumerate(self.steps, 1)]
        return f"【作り方】\n{'\n'.join(steps)}"


def generate_dish() -> Dish:
    genres = random.choice(["和食", "洋食", "中華料理", "エスニック"])  # noqa: S311
    main_food = random.choice(["牛肉", "豚肉", "鶏肉", "魚介類"])  # noqa: S311
    message = f"""
あなたは一流のシェフであり、世界中のあらゆる料理について熟知しています。
また、探究心が強く、独創的で画期的な料理のレシピを常日頃から創作しています。
独創的でおしゃれだけど、比較的簡単に作れる料理を一つ提案してください。
料理は{genres}で{main_food}を使ってください。
"""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("human", message),
        ],
    )
    model = ChatOpenAI(
        model="gpt-4.1",
        temperature=0.8,
        top_p=0.8,
        frequency_penalty=0.5,
        presence_penalty=0.8,
    )
    chain = prompt | model.with_structured_output(Dish)
    return chain.invoke({})  # type: ignore[return-value]


def handler(event: dict[str, Any], context: object) -> GenTextResponse:  # noqa: ARG001
    return main()


@log_exec
def main() -> GenTextResponse:
    config = OpenAIConfig()
    os.environ["OPENAI_API_KEY"] = config.api_key
    recipe = generate_dish()
    return {
        "DishName": recipe.dish_name,
        "Ingredients": recipe.ingredients_str(),
        "Steps": recipe.steps_str(),
    }


if __name__ == "__main__":
    main()
