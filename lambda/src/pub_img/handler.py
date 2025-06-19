import os

from src.pub_img import mod
from src.pub_img.client import Client
from src.shared.config import MetaConfig
from src.shared import (
    handle_exceptions, 
    get_logger,
    validate_required_fields,
    safe_dict_access,
)


@handle_exceptions("pub_img")
def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    # Skip publication if dry run flag is set
    if safe_dict_access(event, "DryRun", False):
        logger = get_logger("pub_img")
        logger.info("Dry run mode - skipping publication")
        return {"status": "skipped", "reason": "dry_run"}
        
    return main(
        image_bucket=os.getenv("IMAGE_BUCKET"),
        title_image_key=safe_dict_access(event, "TitleImageKey", ""),
        image_key=safe_dict_access(event, "ImageKey", ""),
        dish_name=safe_dict_access(event, "DishName", ""),
        recipe=safe_dict_access(event, "Recipe", ""),
    )


def main(
    image_bucket: str,
    title_image_key: str,
    image_key: str,
    dish_name: str,
    recipe: str,
) -> dict:
    """Main function to publish images to social media."""
    logger = get_logger("pub_img")
    
    try:
        # Validate required input fields
        validate_required_fields(
            {
                "image_bucket": image_bucket,
                "title_image_key": title_image_key,
                "image_key": image_key,
                "dish_name": dish_name,
                "recipe": recipe,
            },
            ["image_bucket", "title_image_key", "image_key", "dish_name", "recipe"]
        )
        
        logger.info(f"Publishing images for dish: {dish_name}")
        
        # Initialize client and create image URLs
        client = Client(MetaConfig())
        title_image_url = mod.create_presigned_url(image_bucket, title_image_key)
        image_url = mod.create_presigned_url(image_bucket, image_key)
        
        # Prepare caption content
        comments = "※このレシピと写真はAIによって自動で作成されたものです。\nレシピの内容について確認はしていないため、食べられる料理が作成できない恐れがあります。"  # noqa: E501
        hashtag = "#レシピ #料理 #お菓子 #クッキング #AI #AIレシピ"
        caption = f"\n{dish_name}\n\n{comments}\n\n{recipe}\n\n{hashtag}"
        
        logger.info("Uploading images to social media...")
        mod.upload_images(
            client,
            image_urls=[title_image_url, image_url],
            caption=caption,
        )
        
        logger.info("Images published successfully")
        
        return {
            "status": "published",
            "dish_name": dish_name,
            "images_uploaded": 2
        }
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main("", "", "", "", "")
