from typing import TypedDict


class GenTextResponse(TypedDict):
    DishName: str
    Recipe: str


class GenImgResponse(TypedDict):
    DishUrl: str
