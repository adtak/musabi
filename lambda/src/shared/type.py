from typing import TypedDict


class GenTextResponse(TypedDict):
    DishName: str
    Ingredients: str
    Steps: str


class GenImgResponse(TypedDict):
    ImgUrl: str
