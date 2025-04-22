from openai import OpenAI
from ..config import OPENAI_API_KEY

class EmbeddingGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "text-embedding-3-small"
    
    def generate(self, text):
        """Generate embedding for given text"""
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

# Create singleton instance
embedding_generator = EmbeddingGenerator() 