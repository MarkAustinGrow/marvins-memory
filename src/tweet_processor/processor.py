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
    
    async def generate_research_query(self, tweet_text: str) -> str:
        """Generate a research query based on tweet content using OpenAI"""
        
        logger.debug(f"Generating research query for tweet: {tweet_text[:50]}...")
        
        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Create the prompt for research query generation
            prompt = f"""
            Marvin is an AI researching culture and philosophy. Based on this tweet, generate a culturally insightful research question.
            
            Tweet: "{tweet_text}"
            
            Generate a research question that:
            1. Explores the cultural, philosophical, or artistic context of this tweet
            2. Digs deeper into any references, metaphors, or themes present
            3. Connects to broader intellectual movements or ideas
            4. Would yield interesting and meaningful insights when researched
            
            Research Question:
            """
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # Extract the research question
            research_question = response.choices[0].message.content.strip()
            
            logger.debug(f"Generated research question: {research_question}")
            
            return research_question
            
        except Exception as e:
            logger.error(f"Error generating research query: {str(e)}")
            # Fallback to a generic research prompt
            return f"Explain the cultural and philosophical context of this tweet: '{tweet_text}'"
    
    async def research_tweet(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """Research a tweet using Perplexity AI"""
        
        tweet_text = tweet.get("tweet_text", "")
        tweet_url = tweet.get("tweet_url", "")
        
        logger.debug(f"Researching tweet: {tweet_text[:50]}...")
        
        try:
            # Generate a targeted research query using OpenAI
            research_query = await self.generate_research_query(tweet_text)
            
            logger.info(f"Researching with query: {research_query}")
            
            # Use the existing research manager with the generated query
            research_result = await self.research_manager.conduct_research(
                query=research_query,
                auto_approve=False  # We'll process the insights ourselves
            )
            
            # Add tweet metadata to the result
            research_result["tweet_id"] = tweet.get("tweet_id")
            research_result["tweet_text"] = tweet_text
            research_result["research_query"] = research_query
            
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
                # We don't need to check if tweet has already been processed
                # since we're now filtering by archived=False in get_candidate_tweets
                
                # Initialize variables
                alignment = {"alignment_score": 0, "matched_aspects": [], "explanation": "Not evaluated"}
                memory_ids = []
                should_mark_archived = True
                
                try:
                    # 2. Evaluate tweet alignment with character
                    tweet_text = tweet.get("tweet_text", "")
                    alignment = memory_manager.character_manager.evaluate_alignment(tweet_text)
                    
                    # Log alignment result
                    logger.info(f"Tweet alignment: score={alignment.get('alignment_score', 0)}, aspects={alignment.get('matched_aspects', [])}")
                    logger.debug(f"Alignment explanation: {alignment.get('explanation', 'No explanation')}")
                    
                    # Skip tweets that don't align well with character
                    if alignment.get("alignment_score", 0) < 0.75:  # Changed from MIN_ALIGNMENT_SCORE to 0.75
                        logger.info(f"Skipping tweet {tweet['id']} due to low alignment score: {alignment.get('alignment_score', 0)}")
                        # Continue with marking as archived but with no memories
                    else:
                        # 3. Research tweet content
                        research_result = await self.research_tweet(tweet)
                        
                        if research_result.get("status") == "error":
                            logger.error(f"Research failed for tweet {tweet['id']}: {research_result.get('error')}")
                        else:
                            # 4. Process insights into memories
                            memory_ids = await self.process_insights(research_result, tweet)
                
                except Exception as e:
                    logger.error(f"Error in tweet processing pipeline for tweet {tweet['id']}: {str(e)}")
                    # Continue with marking as archived
                
                # 5. Always update tweet status regardless of processing success
                try:
                    success = await self.update_tweet_status(tweet["id"], memory_ids)
                    
                    if success:
                        processed_count += 1
                        results.append({
                            "tweet_id": tweet.get("tweet_id", "unknown"),
                            "alignment_score": alignment.get("alignment_score", 0),
                            "matched_aspects": alignment.get("matched_aspects", []),
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
