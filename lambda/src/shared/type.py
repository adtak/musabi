from typing import TypedDict


class GenTextResponse(TypedDict):
    DishName: str
    Genres: str
    MainFood: str
    Theme: str
    Ingredients: str
    Steps: str


class GenImgResponse(TypedDict):
    ImgKey: str
