import os
import tempfile
from typing import Any, Self

from google import genai
from loguru import logger
from pydantic import BaseModel

from src.shared.config import GeminiConfig
from src.shared.logging import log_exec
from src.shared.s3 import get_image
from src.shared.type import SelectImgResponse


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


def select_best_image(
    client: genai.Client, image_keys: list[str], bucket_name: str,
) -> str:
    uploaded_imgs = []
    for i, key in enumerate(image_keys):
        image = get_image(bucket_name, key)
        temp_img = tempfile.NamedTemporaryFile(suffix=f"_{i}.png", delete=False)
        image.save(temp_img.name, format="PNG")
        temp_img.append(temp_img.name)

        uploaded_img = client.files.upload(path=temp_img.name)
        uploaded_imgs.append(uploaded_img)

    prompt = """
You are tasked with selecting the best food image from the provided options.
Please analyze each image and select the one that best meets these criteria:
1. Visual appeal and presentation quality
2. Clarity and sharpness of the image
3. Proper lighting and color balance
4. Appetizing appearance that would make viewers want to try the food
5. Overall composition and aesthetic quality

Please respond with only the number (1, 2, 3, etc.) of the best image,
where 1 corresponds to the first image, 2 to the second, and so on.
Do not include any explanation or additional text - just the number.
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, *uploaded_imgs],
    )

    if (
        response.candidates is None
        or response.candidates[0].content is None
        or response.candidates[0].content.parts is None
    ):
        msg = "No response from Gemini."
        raise RuntimeError(msg)

    response_text = ""
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            response_text += part.text

    response_text = response_text.strip()
    logger.info(f"Gemini response: {response_text}")

    try:
        selected_index = int(response_text) - 1
        if 0 <= selected_index < len(image_keys):
            return image_keys[selected_index]
        logger.warning(
            f"Invalid index {selected_index}, defaulting to first image",
        )
        return image_keys[0]
    except ValueError:
        logger.warning(
            f"Could not parse response '{response_text}', defaulting to first image",
        )
        return image_keys[0]
    finally:
        for uploaded_img in uploaded_imgs:
            client.files.delete(name=uploaded_img.name)


def handler(event: dict[str, Any], context: object) -> SelectImgResponse:  # noqa: ARG001
    return main(SelectImgArgs.from_event(event))


@log_exec
def main(args: SelectImgArgs) -> SelectImgResponse:
    config = GeminiConfig()
    client = genai.Client(api_key=config.api_key)

    selected_key = select_best_image(client, args.image_keys, args.bucket_name)

    return {
        "ImgKey": selected_key,
    }


if __name__ == "__main__":
    main(SelectImgArgs(bucket_name="", image_keys=["", ""]))
