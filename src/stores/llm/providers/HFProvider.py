from ..llm_interface import LLMInterface
from sentence_transformers import SentenceTransformer
from ..llm_enums import OpenAIEnums
from helpers import get_logger

logger = get_logger(__name__)


class HuggingFaceProvider(LLMInterface):
    def __init__(self,
                default_input_max_chars=2048,
                default_out_max_tokens=500,
                default_temperature=0.7,
                ):
        self.default_input_max_chars = default_input_max_chars
        self.default_out_max_tokens = default_out_max_tokens
        self.default_temperature = default_temperature
        
        self.embedding_model_id = None
        self.embedding_size = None
        self.client = None
        
    def set_generation_model(self, model_id: str):
        logger.warning("HuggingFaceProvider doesn't support text generation. Use OpenRouter or OpenAI for that.")
        self.generation_model_id = None
        return NotImplementedError
        
    def set_embedding_model(self, model_id:str, embedding_size:int = None):

        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        try:
            self.client = SentenceTransformer(model_id)
            if not self.embedding_size:
                sample_embedding = self.client.encode("test")
                self.embedding_size = len(sample_embedding)
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model '{model_id}': {e}")
            self.client = None
    
    def process_text(self, text:str):
        
        return text[:self.default_input_max_chars].strip()
    
    def construct_prompt(self, prompt:str, role:str):
        return NotImplementedError
    def generate_text(self, prompt:str, chat_history:list = [], temperature:float = None, max_out_tokens:int = None):
        return NotImplementedError

    
    def embed_text(self, text:str, document_type:str = None):
        if not self.client:
            logger.error("HuggingFace Client not initialized")
            return None
        try:
            embedding = self.client.encode(self.process_text(text))
            return embedding
        except Exception as e:
            logger.error(f"Error while embedding text: {e}")
            return None