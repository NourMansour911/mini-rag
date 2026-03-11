from .providers import OpenAIProvider, CoHereProvider
from helpers import Settings,get_logger

logger = get_logger(__name__)
class LLMFactory:
    def __init__(self,settings: Settings):
        self.settings = settings


    def create(self, provider: str):
        if provider == "OPENAI":
            return OpenAIProvider(
                api_key = self.settings.OPENAI_API_KEY,
                api_url = self.settings.OPENAI_API_URL,
                default_input_max_characters=2048,
                default_generation_max_output_tokens=500,
                default_generation_temperature=0.7
            )

        if provider == "COHERE":
            return CoHereProvider(
                api_key = self.settings.COHERE_API_KEY,
                default_input_max_characters=2048,
                default_generation_max_output_tokens=500,
                default_generation_temperature=0.7
            )

        return None
