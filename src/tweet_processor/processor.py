from typing import List, Dict, Any, Optional
import logging
import asyncio
import json
from datetime import datetime
from supabase import create_client
from openai import OpenAI

from ..config import SUPABASE_URL, SUPABASE_KEY, MIN_ALIGNMENT_SCORE, OPENAI_API_KEY
from ..research.research_manager import research_manager
from ..memory.manager import memory_manager
from ..character.manager import character_manager

# Set up logging
logger = logging.getLogger(__name__)

class TweetProcessor:
    """Processor for researching and storing tweets"""
    
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.research_manager = research_manager
        self.memory_manager = memory_manager
    
    async def get_candidate_tweets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get candidate tweets for processing"""
        
        logger.debug(f"Fetching candidate tweets with limit={limit}")
        
        try:
            # Query tweets_cache table for unarchived tweets without engagement filter
            response = self.supabase.table("tweets_cache") \
                .select("id,tweet_id,tweet_text,tweet_url,engagement_score,public_metrics,vibe_tags,created_at") \
                .eq("archived", False) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            if not response.data:
                logger.info("No candidate tweets found")
                return []
            
            logger.debug(f"Found {len(response.data)} candidate tweets")
            return response.data
            
        except Exception as e:
            logger.error(f"Error fetching candidate tweets: {str(e)}")
            return []
    
    async def generate_research_query(self, tweet_text: str) -> Dict[str, Any]:
        """Generate a research query based on tweet content using the curious evaluation approach"""
        
        logger.debug(f"Evaluating and generating research query for tweet: {tweet_text[:50]}...")
        
        try:
            # Use the curious evaluation approach from character manager
            result = character_manager.evaluate_alignment_curious(tweet_text)
            
            logger.debug(f"Research evaluation: worth_researching={result.get('is_worth_researching', False)}")
            logger.debug(f"Relevance explanation: {result.get('relevance_explanation', '')}")
            
            if result.get('is_worth_researching', False):
                logger.debug(f"Generated research question: {result.get('research_question', '')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating research query: {str(e)}")
            # Fallback to a conservative approach
            return {
                "is_worth_researching": False,
                "relevance_explanation": f"Error in evaluation: {str(e)}",
                "research_question": ""
            }
    
    async def research_tweet(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """Research a tweet using Perplexity AI if it's worth researching"""
        
        tweet_text = tweet.get("tweet_text", "")
        tweet_url = tweet.get("tweet_url", "")
        
        logger.debug(f"Evaluating tweet for research: {tweet_text[:50]}...")
        
        try:
            # Evaluate the tweet and potentially generate a research query
            evaluation = await self.generate_research_query(tweet_text)
            
            # If the tweet is not worth researching, return early
            if not evaluation.get("is_worth_researching", False):
                logger.info(f"Tweet deemed not worth researching: {evaluation.get('relevance_explanation', '')}")
                return {
                    "status": "skipped",
                    "reason": evaluation.get("relevance_explanation", "Not relevant to Marvin's interests"),
                    "tweet_id": tweet.get("tweet_id"),
                    "tweet_text": tweet_text
                }
            
            # Get the research question
            research_query = evaluation.get("research_question", "")
            logger.info(f"Researching with query: {research_query}")
            
            # Use the existing research manager with the generated query
            research_result = await self.research_manager.conduct_research(
                query=research_query,
                auto_approve=False  # We'll process the insights ourselves
            )
            
            # Add tweet metadata and evaluation to the result
            research_result["tweet_id"] = tweet.get("tweet_id")
            research_result["tweet_text"] = tweet_text
            research_result["research_query"] = research_query
            research_result["relevance_explanation"] = evaluation.get("relevance_explanation", "")
            
            return research_result
            
        except Exception as e:
            logger.error(f"Error researching tweet: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def process_insights(self, research_result: Dict[str, Any], tweet: Dict[str, Any]) -> List[str]:
        """Process research insights into memories"""
        
        if research_result.get("status") == "error":
            logger.error(f"Cannot process insights due to research error: {research_result.get('error')}")
            return []
        
        insights = research_result.get("insights", [])
        logger.debug(f"Processing {len(insights)} insights for tweet {tweet.get('tweet_id')}")
        
        memory_ids = []
        
        for insight in insights:
            try:
                # Extract tags from insight and tweet
                tags = insight.get("tags", [])
                if tweet.get("vibe_tags"):
                    # Add tweet vibe tags if available
                    vibe_tags = [tag.strip() for tag in tweet["vibe_tags"].split(",") if tag.strip()]
                    tags.extend(vibe_tags)
                
                # Add curious tag if this came from the curious evaluation
                if "curious" not in tags:
                    tags.append("curious")
                
                # Create memory content with reference to original tweet and research question
                research_question = research_result.get("research_query", "")
                content = f"{insight['content']}\n\nBased on tweet: \"{tweet['tweet_text']}\""
                if research_question:
                    content += f"\n\nResearch question: \"{research_question}\""
                
                # Store in memory system with bypass_alignment_check=True
                # This ensures that if the LLM decided the tweet was worth researching,
                # the resulting memories will be stored regardless of alignment score
                memory_id = await self.memory_manager.store_memory(
                    content=content,
                    memory_type="research",
                    source=f"tweet:{tweet['tweet_id']}",
                    tags=tags,
                    metadata={
                        "relevance_type": "curious",
                        "relevance_explanation": research_result.get("relevance_explanation", ""),
                        "research_question": research_result.get("research_query", "")
                    },
                    bypass_alignment_check=True  # Bypass the alignment check
                )
                
                if memory_id:
                    logger.debug(f"Stored memory with ID: {memory_id}")
                    memory_ids.append(memory_id)
                else:
                    logger.warning(f"Memory was not stored (failed alignment check)")
                
            except Exception as e:
                logger.error(f"Error processing insight: {str(e)}")
        
        return memory_ids
    
    async def update_tweet_status(self, tweet_id: int, memory_ids: List[str]) -> bool:
        """Mark tweet as archived and link to created memories"""
        
        logger.debug(f"Updating status for tweet {tweet_id} with {len(memory_ids)} memories")
        
        try:
            # Update only the archived field to avoid schema cache issues
            # We'll skip updating memory_ids for now until the schema cache refreshes
            response = self.supabase.table("tweets_cache") \
                .update({
                    "archived": True
                }) \
                .eq("id", tweet_id) \
                .execute()
            
            # Log the memory IDs that would have been stored
            if memory_ids:
                logger.info(f"Memory IDs for tweet {tweet_id} (not stored due to schema cache): {memory_ids}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating tweet status: {str(e)}")
            return False
    
    async def process_tweets_batch(self, limit: int = 10) -> Dict[str, Any]:
        """Process a batch of tweets from cache"""
        
        logger.info(f"Starting batch processing of tweets (limit={limit})")
        
        # 1. Select candidate tweets
        tweets = await self.get_candidate_tweets(limit=limit)
        
        if not tweets:
            return {"status": "success", "processed_count": 0, "failed_count": 0, "message": "No tweets to process"}
        
        processed_count = 0
        failed_count = 0
        results = []
        
        for tweet in tweets:
            try:
                # Initialize variables
                memory_ids = []
                research_result = {"status": "not_processed"}
                
                try:
                    # Research tweet content (which now includes relevance evaluation)
                    research_result = await self.research_tweet(tweet)
                    
                    if research_result.get("status") == "skipped":
                        # Tweet was evaluated but deemed not worth researching
                        logger.info(f"Skipping research for tweet {tweet['id']}: {research_result.get('reason')}")
                        # We'll still mark it as archived
                    elif research_result.get("status") == "error":
                        logger.error(f"Research failed for tweet {tweet['id']}: {research_result.get('error')}")
                    else:
                        # Process insights into memories
                        memory_ids = await self.process_insights(research_result, tweet)
                
                except Exception as e:
                    logger.error(f"Error in tweet processing pipeline for tweet {tweet['id']}: {str(e)}")
                    # Continue with marking as archived
                
                # Always update tweet status regardless of processing success
                try:
                    success = await self.update_tweet_status(tweet["id"], memory_ids)
                    
                    if success:
                        processed_count += 1
                        results.append({
                            "tweet_id": tweet.get("tweet_id", "unknown"),
                            "status": research_result.get("status", "unknown"),
                            "reason": research_result.get("reason", ""),
                            "memory_count": len(memory_ids)
                        })
                    else:
                        failed_count += 1
                        logger.error(f"Failed to update tweet status for tweet {tweet['id']}")
                except Exception as e:
                    logger.error(f"Error updating tweet status for tweet {tweet['id']}: {str(e)}")
                    failed_count += 1
                
                # Add a small delay between tweets to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Unhandled error processing tweet {tweet.get('id', 'unknown')}: {str(e)}")
                failed_count += 1
                # Try to mark as archived even in case of unhandled error
                try:
                    await self.update_tweet_status(tweet.get("id"), [])
                except Exception as inner_e:
                    logger.error(f"Failed to mark tweet as archived after error: {str(inner_e)}")
        
        return {
            "status": "success",
            "processed_count": processed_count,
            "failed_count": failed_count,
            "results": results
        }

# Create singleton instance
tweet_processor = TweetProcessor()
