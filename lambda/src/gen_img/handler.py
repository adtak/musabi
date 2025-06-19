from src.shared.config import OpenAIConfig
from src.shared.type import GenImgResponse
from src.shared import (
    OpenAIClient,
    handle_exceptions,
    get_logger,
    validate_required_fields,
)


@handle_exceptions("gen_img")
def handler(event: dict, context: object) -> GenImgResponse:  # noqa: ARG001
    return main(
        dish_name=event.get("DishName", ""),
        recipe=event.get("Recipe", ""),
    )


def generate_dish_img(client: OpenAIClient, dish_name: str, recipe: str) -> str:
    """Generate dish image using OpenAI DALL-E."""
    prompt = f"""
{dish_name}という料理の画像を生成してください。レシピは次のとおりです。
{recipe}
"""
    
    return client.image_generation(
        prompt=prompt,
        model="dall-e-3",
        size="1024x1024",
        quality="standard",
        n=1,
    )


def main(dish_name: str, recipe: str) -> GenImgResponse:
    """Main function to generate dish image."""
    logger = get_logger("gen_img")
    
    try:
        # Validate required input fields
        validate_required_fields(
            {"DishName": dish_name, "Recipe": recipe},
            ["DishName", "Recipe"]
        )
        
        config = OpenAIConfig()
        client = OpenAIClient(config.api_key)
        
        logger.info(f"Generating image for dish: {dish_name}")
        img_url = generate_dish_img(client, dish_name, recipe)
        logger.info("Image generation completed")
        
        return {
            "ImgUrl": img_url,
        }
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info(main("", ""))
