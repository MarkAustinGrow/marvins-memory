from openai import OpenAI
import logging
import numpy as np

from ..config import OPENAI_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "text-embedding-3-small"
    
    def generate(self, text):
        """Generate embedding for given text"""
        try:
            if not text or not isinstance(text, str):
                logger.warning(f"Invalid text for embedding: {type(text)}")
                # Return a zero vector of the expected size (1536 for text-embedding-3-small)
                return [0.0] * 1536
            
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            
            if not response or not response.data or len(response.data) == 0:
                logger.error("Empty response from OpenAI API")
                return [0.0] * 1536
                
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * 1536

# Create singleton instance
embedding_generator = EmbeddingGenerator()
