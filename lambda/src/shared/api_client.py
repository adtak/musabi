import re
from typing import List, Optional

from openai import OpenAI
from loguru import logger

from .error_handler import handle_exceptions, retry_on_failure, safe_list_access, ValidationError
from .logger import get_logger


class OpenAIClient:
    """Wrapper for OpenAI API calls with consistent error handling and logging."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = get_logger("openai_client")
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @handle_exceptions("openai_client")
    def chat_completion(
        self,
        messages: List[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Create a chat completion with error handling and retry logic.
        
        Args:
            messages: List of message dictionaries
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text content
            
        Raises:
            ValidationError: If no content is returned
        """
        self.logger.info(f"Creating chat completion with model {model}")
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValidationError("OpenAI returned empty content")
            
        self.logger.info("Chat completion successful")
        return content
    
    @retry_on_failure(max_retries=2, delay=2.0)
    @handle_exceptions("openai_client")
    def image_generation(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
    ) -> str:
        """
        Generate image with error handling and retry logic.
        
        Args:
            prompt: Image generation prompt
            model: OpenAI model to use
            size: Image size
            quality: Image quality
            n: Number of images to generate
            
        Returns:
            Generated image URL
            
        Raises:
            ValidationError: If no image URL is returned
        """
        self.logger.info(f"Generating image with model {model}")
        
        response = self.client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )
        
        if not response.data or not response.data[0].url:
            raise ValidationError("OpenAI returned no image data")
            
        url = response.data[0].url
        self.logger.info("Image generation successful")
        return url


def extract_quoted_text(text: str, quote_chars: str = "「」", default: str = "") -> str:
    """
    Safely extract text within quote characters.
    
    Args:
        text: Text to search in
        quote_chars: Quote characters (e.g., "「」", '""')
        default: Default value if no quoted text found
        
    Returns:
        Extracted text or default value
    """
    if len(quote_chars) != 2:
        raise ValueError("quote_chars must be exactly 2 characters")
    
    open_quote, close_quote = quote_chars[0], quote_chars[1]
    pattern = f"{re.escape(open_quote)}(.*?){re.escape(close_quote)}"
    
    matches = re.findall(pattern, text)
    result = safe_list_access(matches, 0, default)
    
    if result == default:
        logger.warning(f"No quoted text found in: {text[:100]}...")
        logger.warning(f"Returning default value: {default}")
    
    return result