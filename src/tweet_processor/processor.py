from typing import List, Dict, Any, Optional
import logging
import asyncio
import json
from datetime import datetime
from supabase import create_client

from ..config import SUPABASE_URL, SUPABASE_KEY, MIN_ALIGNMENT_SCORE
from ..research.research_manager import research_manager
from ..memory.manager import memory_manager

# Set up logging
logger = logging.getLogger(__name__)

class TweetProcessor:
    """Processor for researching and storing tweets"""
    
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.research_manager = research_manager
        self.memory_manager = memory_manager
    
    async def get_candidate_tweets(self, limit: int = 10, min_engagement: float = 0.7) -> List[Dict[str, Any]]:
        """Get candidate tweets for processing"""
        
        logger.debug(f"Fetching candidate tweets with min_engagement={min_engagement}, limit={limit}")
        
        try:
            # Query tweets_cache table for unprocessed tweets with high engagement
            response = self.supabase.table("tweets_cache") \
                .select("id,tweet_id,tweet_text,tweet_url,engagement_score,public_metrics,vibe_tags,created_at") \
                .is_("processed_at", "null") \
                .gte("engagement_score", min_engagement) \
                .order("engagement_score", desc=True) \
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
    
    async def research_tweet(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """Research a tweet using Perplexity AI"""
        
        tweet_text = tweet.get("tweet_text", "")
        tweet_url = tweet.get("tweet_url", "")
        
        logger.debug(f"Researching tweet: {tweet_text[:50]}...")
        
        # Craft a prompt specifically for tweet research
        prompt = f"""
        Can you explain the cultural or artistic context of this tweet:
        '{tweet_text}'
        
        Include any relevant subcultures, art movements, or philosophies it relates to.
        Analyze any references, metaphors, or themes present in the tweet.
        Provide historical or contemporary context that helps understand its meaning.
        """
        
        try:
            # Use the existing research manager
            research_result = await self.research_manager.conduct_research(
                query=prompt,
                auto_approve=False  # We'll process the insights ourselves
            )
            
            # Add tweet metadata to the result
            research_result["tweet_id"] = tweet.get("tweet_id")
            research_result["tweet_text"] = tweet_text
            
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
                
                # Create memory content with reference to original tweet
                content = f"{insight['content']}\n\nBased on tweet: \"{tweet['tweet_text']}\""
                
                # Store in memory system (this will check character alignment)
                memory_id = await self.memory_manager.store_memory(
                    content=content,
                    memory_type="research",
                    source=f"tweet:{tweet['tweet_id']}",
                    tags=tags
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
        """Mark tweet as processed and link to created memories"""
        
        logger.debug(f"Updating status for tweet {tweet_id} with {len(memory_ids)} memories")
        
        try:
            # Update the tweet record
            response = self.supabase.table("tweets_cache") \
                .update({
                    "processed_at": datetime.now().isoformat(),
                    "memory_ids": json.dumps(memory_ids)
                }) \
                .eq("id", tweet_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating tweet status: {str(e)}")
            return False
    
    async def process_tweets_batch(self, limit: int = 10, min_engagement: float = 0.7) -> Dict[str, Any]:
        """Process a batch of tweets from cache"""
        
        logger.info(f"Starting batch processing of tweets (limit={limit}, min_engagement={min_engagement})")
        
        # 1. Select candidate tweets
        tweets = await self.get_candidate_tweets(limit=limit, min_engagement=min_engagement)
        
        if not tweets:
            return {"status": "success", "processed_count": 0, "message": "No tweets to process"}
        
        processed_count = 0
        failed_count = 0
        results = []
        
        for tweet in tweets:
            try:
                # 2. Research tweet content
                research_result = await self.research_tweet(tweet)
                
                if research_result.get("status") == "error":
                    logger.error(f"Research failed for tweet {tweet['id']}: {research_result.get('error')}")
                    failed_count += 1
                    continue
                
                # 3. Process insights into memories
                memory_ids = await self.process_insights(research_result, tweet)
                
                # 4. Update tweet status
                success = await self.update_tweet_status(tweet["id"], memory_ids)
                
                if success:
                    processed_count += 1
                    results.append({
                        "tweet_id": tweet["tweet_id"],
                        "memory_count": len(memory_ids)
                    })
                else:
                    failed_count += 1
                
                # Add a small delay between tweets to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing tweet {tweet['id']}: {str(e)}")
                failed_count += 1
        
        return {
            "status": "success",
            "processed_count": processed_count,
            "failed_count": failed_count,
            "results": results
        }

# Create singleton instance
tweet_processor = TweetProcessor()
