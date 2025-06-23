import os
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

    def to_recipe(self) -> str:
        ingredients = [f"- {ing}" for ing in self.ingredients]
        steps = [f"{i}. {step}" for i, step in enumerate(self.steps, 1)]
        return f"""{self.dish_name}のレシピは以下の通りです。

【材料】
{'\n'.join(ingredients)}

【作り方】
{'\n'.join(steps)}

ぜひ試してみてください！
"""  # noqa: RUF001


def generate_dish() -> Dish:
    message = """
あなたは一流のシェフであり、世界中のあらゆる料理について熟知しています。
また、探究心が強く、独創的で画期的な料理のレシピを常日頃から創作しています。
独創的でおしゃれだけど、比較的簡単に作れる料理を一つ提案してください。
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
        "Recipe": recipe.to_recipe(),
    }


if __name__ == "__main__":
    main()
