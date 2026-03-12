from ..llm_interface import LLMInterface
from openai import OpenAI
from helpers import get_logger
from ..llm_enums import OpenAIEnums

logger = get_logger(__name__)


class OpenAIProvider(LLMInterface):
    def __init__(self,
                api_key:str,
                api_url:str=None,
                default_input_max_chars=2048,
                default_out_max_tokens=500,
                default_temperature=0.7,
                ):
        self.api_key = api_key
        self.api_url = api_url
        self.default_input_max_chars = default_input_max_chars
        self.default_out_max_tokens = default_out_max_tokens
        self.default_temperature = default_temperature
        
        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.client = OpenAI(api_key=self.api_key,base_url=self.api_url)
                
        
    def set_generation_model(self,model_id:str):
        self.generation_model_id = model_id
        
    def set_embedding_model(self,model_id:str,embedding_size:int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        
    def process_text(self,text:str):
        text = text[self.default_input_max_chars].strip()
        return text
   
    def construct_prompt(self,prompt:str,role:str):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }
    
    def generate_text(self,prompt:str,chat_history:list=[] ,temperature:float = None,max_out_tokens:int=None  ):
        if not self.client:
            logger.error("OpenAI Client not initialized")
            return None
        
        if not self.generation_model_id:
            logger.error("OpenAI Generation model not set")
            return None
        
        if not temperature:
            temperature = self.default_temperature
            
        if not max_out_tokens:
            max_out_tokens = self.default_out_max_tokens
            
        chat_history.append(self.construct_prompt(prompt=prompt,role=OpenAIEnums.USER.value))
    
        response = self.client.chat.completions.create(
        model=self.generation_model_id,
        messages=chat_history,
        temperature=temperature,
        max_tokens=max_out_tokens
        )
        
        if  not response or not response.choices or not response.choices[0].message.content:
            logger.error("OpenAI Error while generating text")
            return None
        
        return response.choices[0].message.content

    
    def embed_text(self,text:str,document_type:str):
        
        if not self.client:
            logger.error("OpenAI Client not initialized")
            return None
        
        if not self.embedding_model_id:
            logger.error("OpenAI Embedding model not set")
            return None
 
        response = self.client.embeddings.create(
            model=self.embedding_model_id,
            input=[text]
        )    
        
        if not response.data  or not response.data[0].embedding:
            logger.error("OpenAI Error while embedding text")
            return None
            
        return response.data[0].embedding
            


        
       
        
        
    
        
        
 
 