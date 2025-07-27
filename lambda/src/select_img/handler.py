import base64
import io
import os
from typing import Any, Self

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from src.shared.config import GeminiConfig
from src.shared.logging import log_exec
from src.shared.s3 import get_image
from src.shared.type import SelectImgResponse


class SelectedImage(BaseModel):
    index: int = Field(ge=0, description="0-based index of selected image")

    def get_valid_index(self, image_cnt: int) -> int:
        if image_cnt < self.index + 1:
            msg = f"Index {self.index} is out of range. Image count is {image_cnt}."
            raise ValueError(msg)
        return self.index


class SelectImgArgs(BaseModel):
    bucket_name: str
    image_keys: list[str]

    @classmethod
    def from_event(cls, event: dict[str, Any]) -> Self:
        return cls.model_validate(
            {
                "bucket_name": os.getenv("IMAGE_BUCKET"),
                "image_keys": event.get("ImageKeys", []),
            },
        )


def decode_images(bucket_name: str, image_keys: list[str]) -> list[str]:
    results: list[str] = []
    for key in image_keys:
        image_bytes = io.BytesIO()
        get_image(bucket_name, key).save(image_bytes, format="PNG")
        decoded_image = base64.b64encode(image_bytes.getvalue()).decode()
        results.append(decoded_image)
    return results


def select_image(decoded_images: list[str]) -> SelectedImage:
    def get_image_message(image: str) -> dict[str, Any]:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image}"},
        }

    prompt_text = """
You are tasked with selecting the best food image from the provided options.
Please analyze each image based on the following detailed criteria:
1. Top-down angle: The photo should be taken from a bird's-eye view,
 clearly showing the entire dish, the plate, and some of the surrounding space.
2. Atmosphere: The image should evoke a refined and sophisticated mood,
 like that of a high-end restaurant.
3. Professional lighting: The lighting should be beautifully executed, with soft,
 balanced illumination that enhances the food's texture and color.
4. Composition: The layout should consider not only the food
 but also the table setting and background elements in a thoughtful, aesthetic way.
5. Commercial quality: The image should be suitable for use in commercial contexts,
 such as advertising or menus.
6. No text: The image should not contain any text or ingredient descriptions.
Evaluate all images and select the one that best matches all of the above criteria.
Please respond with only the number (0, 1, 2, 3, etc.) of the best image.
"""
    messages: list[dict[str, Any]] = [{"type": "text", "text": prompt_text}]
    messages.extend(get_image_message(image) for image in decoded_images)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("human", messages),
        ],
    )
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
    )
    chain = prompt | model.with_structured_output(SelectedImage)
    return chain.invoke({})  # type: ignore[return-value]


def handler(
    event: dict[str, Any],
    context: object,  # noqa: ARG001
) -> SelectImgResponse:
    return main(SelectImgArgs.from_event(event))


@log_exec
def main(args: SelectImgArgs) -> SelectImgResponse:
    config = GeminiConfig()
    os.environ["GOOGLE_API_KEY"] = config.api_key
    decoded_images = decode_images(args.bucket_name, args.image_keys)
    response = select_image(decoded_images)
    selected_index = response.get_valid_index(len(args.image_keys))

    return {
        "ImgKey": args.image_keys[selected_index],
    }


if __name__ == "__main__":
    main(SelectImgArgs(bucket_name="", image_keys=["", ""]))
