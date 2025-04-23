import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging
import time
from enum import Enum

from ..config import PERPLEXITY_API_KEY, RESEARCH_MIN_CONFIDENCE, RESEARCH_MAX_INSIGHTS

# Set up logging
logger = logging.getLogger(__name__)

class PerplexityError(Exception):
    """Base exception for Perplexity API errors"""
    pass

class PerplexityAuthError(PerplexityError):
    """Authentication error with Perplexity API"""
    pass

class PerplexityRateLimitError(PerplexityError):
    """Rate limit error with Perplexity API"""
    pass

class PerplexityServerError(PerplexityError):
    """Server error with Perplexity API"""
    pass

class PerplexityTimeoutError(PerplexityError):
    """Timeout error with Perplexity API"""
    pass

class PerplexityClient:
    """Client for interacting with the Perplexity API"""
    
    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def query(self, question: str, model: str = "pplx-70b-online", max_retries: int = 3, timeout: int = 30) -> Dict[str, Any]:
        """
        Send a query to the Perplexity API
        
        Args:
            question: The research question to ask
            model: The model to use for the query
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            
        Returns:
            The raw API response
            
        Raises:
            PerplexityAuthError: If authentication fails
            PerplexityRateLimitError: If rate limit is exceeded
            PerplexityServerError: If server error occurs
            PerplexityTimeoutError: If request times out
            PerplexityError: For other API errors
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
        
        # Add query to payload for reference
        payload["query"] = question
        
        retry_count = 0
        last_exception = None
        
        while retry_count < max_retries:
            try:
                logger.debug(f"Sending request to Perplexity API (attempt {retry_count + 1}/{max_retries})")
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        endpoint,
                        headers=self.headers,
                        json=payload
                    )
                
                # Handle different status codes
                if response.status_code == 200:
                    logger.debug("Perplexity API request successful")
                    return response.json()
                elif response.status_code == 401:
                    logger.error("Perplexity API authentication failed")
                    raise PerplexityAuthError("Authentication failed. Check your API key.")
                elif response.status_code == 429:
                    logger.warning("Perplexity API rate limit exceeded")
                    # If this is the last retry, raise the error
                    if retry_count == max_retries - 1:
                        raise PerplexityRateLimitError("Rate limit exceeded")
                    # Otherwise, wait and retry
                    retry_delay = min(2 ** retry_count, 60)  # Exponential backoff, max 60 seconds
                    logger.info(f"Waiting {retry_delay} seconds before retrying...")
                    await asyncio.sleep(retry_delay)
                elif 500 <= response.status_code < 600:
                    logger.warning(f"Perplexity API server error: {response.status_code}")
                    # If this is the last retry, raise the error
                    if retry_count == max_retries - 1:
                        raise PerplexityServerError(f"Server error: {response.status_code}")
                    # Otherwise, wait and retry
                    retry_delay = min(2 ** retry_count, 60)
                    logger.info(f"Waiting {retry_delay} seconds before retrying...")
                    await asyncio.sleep(retry_delay)
                else:
                    error_msg = f"Perplexity API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg += f" - {error_data['error']}"
                    except:
                        pass
                    logger.error(error_msg)
                    raise PerplexityError(error_msg)
                    
            except httpx.TimeoutException as e:
                logger.warning(f"Perplexity API request timed out: {str(e)}")
                last_exception = PerplexityTimeoutError(f"Request timed out: {str(e)}")
                
            except (httpx.RequestError, asyncio.TimeoutError) as e:
                logger.warning(f"Perplexity API request error: {str(e)}")
                last_exception = PerplexityError(f"Request error: {str(e)}")
                
            except (PerplexityAuthError, PerplexityError) as e:
                # Don't retry auth errors or general API errors
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error querying Perplexity API: {str(e)}")
                last_exception = PerplexityError(f"Unexpected error: {str(e)}")
            
            # Increment retry count
            retry_count += 1
            
            # Wait before retrying (exponential backoff)
            if retry_count < max_retries:
                retry_delay = min(2 ** retry_count, 60)
                logger.info(f"Waiting {retry_delay} seconds before retrying...")
                await asyncio.sleep(retry_delay)
        
        # If we've exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception
        
        # This should never happen, but just in case
        raise PerplexityError("Failed to query Perplexity API after multiple retries")
    
    async def extract_insights(self, response: Dict[str, Any], max_insights: int = RESEARCH_MAX_INSIGHTS) -> List[Dict[str, Any]]:
        """
        Extract key insights from a Perplexity response
        
        Args:
            response: The raw API response
            max_insights: Maximum number of insights to extract
            
        Returns:
            List of extracted insights with metadata
        """
        logger.debug("Extracting insights from Perplexity response")
        
        try:
            # Validate response structure
            if not response:
                logger.warning("Empty response received")
                return []
                
            if not response.get("choices"):
                logger.warning("No choices in response")
                return []
                
            if not response["choices"][0].get("message"):
                logger.warning("No message in first choice")
                return []
            
            content = response["choices"][0]["message"]["content"]
            query = response.get("query", "Unknown query")
            
            logger.debug(f"Extracting insights from content of length {len(content)}")
            
            # Improved insight extraction algorithm
            # 1. Split by paragraphs
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            
            # 2. Look for sections that might contain insights
            sections = []
            current_section = []
            
            for paragraph in paragraphs:
                # Check if this paragraph starts a new section
                if paragraph.startswith("•") or paragraph.startswith("-") or any(paragraph.startswith(str(i) + ".") for i in range(1, 11)):
                    # If we have a current section, add it to sections
                    if current_section:
                        sections.append(" ".join(current_section))
                    # Start a new section
                    current_section = [paragraph]
                else:
                    # Add to current section
                    current_section.append(paragraph)
            
            # Add the last section if it exists
            if current_section:
                sections.append(" ".join(current_section))
            
            # If no sections were found, use paragraphs as fallback
            if not sections:
                logger.debug("No sections found, using paragraphs as fallback")
                sections = paragraphs
            
            # 3. Process sections to extract insights
            insights = []
            for i, section in enumerate(sections[:max_insights]):
                # Skip very short sections
                if len(section) < 50:
                    logger.debug(f"Skipping short section: {section[:30]}...")
                    continue
                
                # Calculate confidence score
                # Base confidence starts high and decreases with position
                base_confidence = 0.95 - (i * 0.03)
                
                # Adjust confidence based on section characteristics
                # Longer sections might be more informative
                length_factor = min(len(section) / 1000, 0.05)
                
                # Sections with numbers or statistics might be more factual
                fact_indicators = sum(1 for c in section if c.isdigit()) / len(section)
                fact_factor = min(fact_indicators * 10, 0.05)
                
                # Calculate final confidence
                confidence = min(base_confidence + length_factor + fact_factor, 0.99)
                
                # Create insight
                insights.append({
                    "content": section,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat(),
                    "source": "perplexity",
                    "query": query,
                    "tags": self._extract_tags(section)
                })
            
            logger.debug(f"Extracted {len(insights)} insights")
            
            # Filter by confidence threshold
            filtered_insights = [insight for insight in insights if insight["confidence"] >= RESEARCH_MIN_CONFIDENCE]
            
            logger.debug(f"{len(filtered_insights)} insights meet confidence threshold")
            
            return filtered_insights
            
        except Exception as e:
            logger.error(f"Error extracting insights: {str(e)}")
            # Return empty list on error
            return []
    
    def _extract_tags(self, text: str) -> List[str]:
        """
        Extract relevant tags from text
        
        Args:
            text: The text to extract tags from
            
        Returns:
            List of extracted tags
        """
        try:
            # This is an improved implementation that uses keyword frequency
            # and common categories to extract tags
            
            # Convert to lowercase for case-insensitive matching
            text_lower = text.lower()
            
            # Define common categories and their related keywords
            categories = {
                "technology": ["technology", "tech", "software", "hardware", "digital", "computer", "ai", "artificial intelligence", 
                              "machine learning", "data", "internet", "online", "app", "application", "device", "smartphone", 
                              "innovation", "programming", "code", "algorithm", "automation", "robot"],
                
                "science": ["science", "scientific", "research", "study", "experiment", "laboratory", "physics", "chemistry", 
                           "biology", "astronomy", "medicine", "medical", "discovery", "theory", "hypothesis", "evidence", 
                           "analysis", "observation", "quantum", "molecular", "genetic", "gene", "dna", "cell", "organism"],
                
                "business": ["business", "company", "corporation", "startup", "entrepreneur", "market", "economy", "economic", 
                            "finance", "financial", "investment", "investor", "stock", "trade", "commerce", "commercial", 
                            "industry", "industrial", "product", "service", "customer", "client", "revenue", "profit", "strategy"],
                
                "health": ["health", "healthcare", "medical", "medicine", "doctor", "hospital", "patient", "treatment", "therapy", 
                          "disease", "illness", "condition", "symptom", "diagnosis", "prescription", "drug", "pharmaceutical", 
                          "wellness", "fitness", "diet", "nutrition", "mental health", "psychology", "vaccine", "immunity"],
                
                "politics": ["politics", "political", "government", "policy", "law", "regulation", "legislation", "election", 
                            "vote", "voter", "campaign", "candidate", "president", "congress", "senate", "representative", 
                            "democrat", "republican", "liberal", "conservative", "party", "nation", "state", "international", "global"],
                
                "environment": ["environment", "environmental", "climate", "climate change", "global warming", "sustainability", 
                               "sustainable", "renewable", "energy", "pollution", "emission", "carbon", "ecosystem", "biodiversity", 
                               "conservation", "wildlife", "nature", "natural", "green", "eco-friendly", "recycling", "waste"],
                
                "education": ["education", "educational", "school", "university", "college", "student", "teacher", "professor", 
                             "academic", "learning", "teaching", "curriculum", "course", "class", "lecture", "study", "knowledge", 
                             "skill", "training", "degree", "diploma", "certificate", "scholarship"],
                
                "social": ["social", "society", "community", "culture", "cultural", "people", "population", "demographic", 
                          "trend", "behavior", "relationship", "communication", "media", "network", "platform", "user", 
                          "content", "engagement", "interaction", "influence", "impact", "change", "movement"]
            }
            
            # Count keyword occurrences for each category
            category_scores = {}
            for category, keywords in categories.items():
                # Count occurrences of each keyword
                score = sum(text_lower.count(keyword) for keyword in keywords)
                # Normalize by number of keywords to avoid bias towards categories with more keywords
                category_scores[category] = score / len(keywords)
            
            # Select categories with non-zero scores, sorted by score (highest first)
            selected_categories = [category for category, score in 
                                  sorted(category_scores.items(), key=lambda x: x[1], reverse=True) 
                                  if score > 0]
            
            # Limit to top 3 categories
            tags = selected_categories[:3]
            
            # If no categories were found, use a generic tag
            if not tags:
                tags = ["general"]
                
            logger.debug(f"Extracted tags: {tags}")
            return tags
            
        except Exception as e:
            logger.error(f"Error extracting tags: {str(e)}")
            # Return a generic tag on error
            return ["general"]
    
    async def format_for_memory(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format insights for storage in the memory system
        
        Args:
            insights: List of extracted insights
            
        Returns:
            List of formatted memories ready for storage
        """
        logger.debug(f"Formatting {len(insights)} insights for memory storage")
        
        try:
            memories = []
            
            for i, insight in enumerate(insights):
                try:
                    # Validate required fields
                    if not insight.get("content"):
                        logger.warning(f"Skipping insight {i}: missing content")
                        continue
                    
                    # Format the memory
                    memory = {
                        "content": insight["content"],
                        "type": "research",
                        "source": f"perplexity:{insight.get('source', 'unknown')}",
                        "tags": insight.get("tags", ["research"]),
                        "metadata": {
                            "confidence": insight.get("confidence", 0.8),
                            "query": insight.get("query", ""),
                            "timestamp": insight.get("timestamp", datetime.now().isoformat())
                        }
                    }
                    
                    # Add additional metadata if available
                    if "url" in insight:
                        memory["metadata"]["url"] = insight["url"]
                    
                    memories.append(memory)
                    logger.debug(f"Formatted insight {i} with {len(memory['content'])} characters")
                    
                except Exception as e:
                    logger.error(f"Error formatting insight {i}: {str(e)}")
                    # Continue with next insight
                    continue
            
            logger.debug(f"Successfully formatted {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Error formatting insights for memory: {str(e)}")
            # Return empty list on error
            return []

# Create singleton instance
perplexity_client = PerplexityClient()
