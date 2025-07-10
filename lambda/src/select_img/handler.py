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


def select_best_image(client: genai.Client, image_keys: list[str], bucket_name: str) -> str:
    if not image_keys:
        msg = "No image keys provided"
        raise ValueError(msg)
    
    if len(image_keys) == 1:
        return image_keys[0]
    
    # Create temporary files for each image
    temp_files = []
    uploaded_files = []
    
    try:
        for i, key in enumerate(image_keys):
            # Download image from S3
            image = get_image(bucket_name, key)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=f"_{i}.png", delete=False)
            image.save(temp_file.name, format="PNG")
            temp_files.append(temp_file.name)
            
            # Upload to Gemini Files API
            uploaded_file = client.files.upload(path=temp_file.name)
            uploaded_files.append(uploaded_file)
        
        # Create prompt for image selection
        prompt = """You are tasked with selecting the best food image from the provided options.
        
Please analyze each image and select the one that best meets these criteria:
1. Visual appeal and presentation quality
2. Clarity and sharpness of the image
3. Proper lighting and color balance
4. Appetizing appearance that would make viewers want to try the food
5. Overall composition and aesthetic quality

Please respond with only the number (1, 2, 3, etc.) of the best image, where 1 corresponds to the first image, 2 to the second, and so on.
Do not include any explanation or additional text - just the number."""
        
        # Prepare content with uploaded files
        content = [prompt]
        for uploaded_file in uploaded_files:
            content.append(uploaded_file)
        
        # Generate response using Gemini 2.5-flash
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content,
        )
        
        if (
            response.candidates is None
            or response.candidates[0].content is None
            or response.candidates[0].content.parts is None
        ):
            msg = "No response from Gemini"
            raise RuntimeError(msg)
        
        # Extract the selected image index
        response_text = ""
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                response_text += part.text
        
        response_text = response_text.strip()
        logger.info(f"Gemini response: {response_text}")
        
        try:
            selected_index = int(response_text) - 1  # Convert to 0-based index
            if 0 <= selected_index < len(image_keys):
                return image_keys[selected_index]
            else:
                logger.warning(f"Invalid index {selected_index}, defaulting to first image")
                return image_keys[0]
        except ValueError:
            logger.warning(f"Could not parse response '{response_text}', defaulting to first image")
            return image_keys[0]
    
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        
        # Clean up uploaded files
        for uploaded_file in uploaded_files:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass


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
    main(SelectImgArgs(bucket_name="test-bucket", image_keys=["image1.png", "image2.png"]))