import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..config import PERPLEXITY_API_KEY, RESEARCH_MIN_CONFIDENCE, RESEARCH_MAX_INSIGHTS

class PerplexityClient:
    """Client for interacting with the Perplexity API"""
    
    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def query(self, question: str, model: str = "pplx-70b-online") -> Dict[str, Any]:
        """
        Send a query to the Perplexity API
        
        Args:
            question: The research question to ask
            model: The model to use for the query
            
        Returns:
            The raw API response
        """
        if not self.api_key:
            raise ValueError("Perplexity API key is not set")
        
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a research assistant that provides accurate, factual information with sources."},
                {"role": "user", "content": question}
            ]
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error querying Perplexity API: {e}")
            raise
    
    async def extract_insights(self, response: Dict[str, Any], max_insights: int = RESEARCH_MAX_INSIGHTS) -> List[Dict[str, Any]]:
        """
        Extract key insights from a Perplexity response
        
        Args:
            response: The raw API response
            max_insights: Maximum number of insights to extract
            
        Returns:
            List of extracted insights with metadata
        """
        if not response.get("choices") or not response["choices"][0].get("message"):
            return []
        
        content = response["choices"][0]["message"]["content"]
        
        # Use OpenAI to extract structured insights
        # This is a placeholder - in a real implementation, you would use
        # an LLM to extract structured insights from the content
        
        # For now, we'll simulate by splitting by paragraphs and treating each as an insight
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        
        insights = []
        for i, paragraph in enumerate(paragraphs[:max_insights]):
            # Skip very short paragraphs
            if len(paragraph) < 50:
                continue
                
            insights.append({
                "content": paragraph,
                "confidence": 0.9 - (i * 0.05),  # Simulate decreasing confidence
                "timestamp": datetime.now().isoformat(),
                "source": "perplexity",
                "query": response.get("query", ""),
                "tags": self._extract_tags(paragraph)
            })
        
        # Filter by confidence threshold
        return [insight for insight in insights if insight["confidence"] >= RESEARCH_MIN_CONFIDENCE]
    
    def _extract_tags(self, text: str) -> List[str]:
        """
        Extract relevant tags from text
        
        Args:
            text: The text to extract tags from
            
        Returns:
            List of extracted tags
        """
        # This is a placeholder - in a real implementation, you would use
        # an LLM or keyword extraction algorithm to identify relevant tags
        
        # For now, we'll use a simple approach based on common words
        common_tags = ["technology", "science", "business", "health", "politics"]
        text_lower = text.lower()
        
        return [tag for tag in common_tags if tag in text_lower]
    
    async def format_for_memory(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format insights for storage in the memory system
        
        Args:
            insights: List of extracted insights
            
        Returns:
            List of formatted memories ready for storage
        """
        memories = []
        
        for insight in insights:
            memories.append({
                "content": insight["content"],
                "type": "research",
                "source": f"perplexity:{insight['source']}",
                "tags": insight["tags"],
                "metadata": {
                    "confidence": insight["confidence"],
                    "query": insight.get("query", ""),
                    "timestamp": insight["timestamp"]
                }
            })
        
        return memories

# Create singleton instance
perplexity_client = PerplexityClient()
