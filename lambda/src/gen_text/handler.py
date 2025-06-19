from src.shared.config import OpenAIConfig
from src.shared.type import GenTextResponse
from src.shared import (
    OpenAIClient,
    extract_quoted_text,
    handle_exceptions,
    get_logger,
    ValidationError,
)


@handle_exceptions("gen_text")
def handler(event: dict, context: object) -> GenTextResponse:  # noqa: ARG001
    return main()


def generate_dish_name(client: OpenAIClient) -> str:
    """Generate a creative dish name using OpenAI."""
    user_content = """
あなたは一流のシェフであり、世界中のあらゆる料理について熟知しています。
また、探究心が強く、独創的で画期的な料理のレシピを常日頃から創作しています。
独創的でおしゃれな料理の名前を一つ提案してください。
また、料理の名前には食材の名前を入れてください。
ただし、生き物の名前を入れないでください。
返答は料理の名前のみを「」で囲って返答してください。
"""
    
    messages = [
        {"role": "system", "content": "日本語で返答してください。"},
        {"role": "user", "content": user_content}
    ]
    
    content = client.chat_completion(messages, model="gpt-4o-mini")
    
    # Safely extract quoted text with fallback
    dish_name = extract_quoted_text(content, "「」", "AIクリエイティブ料理")
    
    if not dish_name or dish_name == "AIクリエイティブ料理":
        raise ValidationError(
            "Failed to extract dish name from OpenAI response",
            details={"response_content": content}
        )
    
    return dish_name


def generate_recipe(client: OpenAIClient, dish_name: str) -> str:
    """Generate a recipe for the given dish name."""
    user_content = f"""
「{dish_name}」という料理のレシピを教えてください。
返答は「{dish_name}のレシピは以下の通りです。」から始めてください。
"""
    
    messages = [
        {
            "role": "system", 
            "content": "日本語で返答してください。情報が存在しない場合でも、架空の情報で提案してください。"
        },
        {"role": "user", "content": user_content}
    ]
    
    return client.chat_completion(messages, model="gpt-4o-mini")


def main() -> GenTextResponse:
    """Main function to generate dish name and recipe."""
    logger = get_logger("gen_text")
    
    try:
        config = OpenAIConfig()
        client = OpenAIClient(config.api_key)
        
        logger.info("Generating dish name...")
        dish_name = generate_dish_name(client)
        logger.info(f"Generated dish name: {dish_name}")
        
        logger.info("Generating recipe...")
        recipe = generate_recipe(client, dish_name)
        logger.info("Recipe generation completed")
        
        return {
            "DishName": dish_name,
            "Recipe": recipe,
        }
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info(main())
