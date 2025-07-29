from google import genai
from google.genai import types
from langsmith import traceable


class TracedGeminiClient:
    def __init__(self, api_key: str) -> None:
        self.client = genai.Client(api_key=api_key)

    @traceable(name="gemini_generate_content", project_name="musabi")
    def generate_content(
        self,
        model: str,
        contents: str,
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse:
        return self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
