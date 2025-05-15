"""
Test script for the tweet processor.

This script can be used to manually test the tweet processor functionality
without having to restart the entire application.

Usage:
    python -m src.tweet_processor.test_processor
"""

import asyncio
import logging
import json
from datetime import datetime

from ..config import SUPABASE_URL, SUPABASE_KEY
from .processor import tweet_processor

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_tweet_processor():
    """Test the tweet processor functionality"""
    
    logger.info("Starting tweet processor test")
    
    try:
        # Process a batch of tweets
        result = await tweet_processor.process_tweets_batch(
            limit=5  # Process up to 5 tweets
        )
        
        logger.info(f"Test result: {json.dumps(result, indent=2)}")
        
        if result["processed_count"] == 0:
            logger.info("No tweets were processed. This could be because:")
            logger.info("1. There are no unprocessed tweets in the tweets_cache table")
            logger.info("2. No tweets met the alignment threshold")
            logger.info("3. There was an error connecting to the tweets_cache table")
            
            # Check if we can connect to the tweets_cache table
            try:
                tweets = await tweet_processor.get_candidate_tweets(
                    limit=5
                )
                
                if tweets:
                    logger.info(f"Found {len(tweets)} tweets in the tweets_cache table")
                    logger.info(f"First tweet: {json.dumps(tweets[0], indent=2)}")
                else:
                    logger.info("No tweets found in the tweets_cache table")
            except Exception as e:
                logger.error(f"Error connecting to tweets_cache table: {str(e)}")
        else:
            logger.info(f"Successfully processed {result['processed_count']} tweets")
            logger.info(f"Failed to process {result['failed_count']} tweets")
            
            for i, tweet_result in enumerate(result["results"]):
                logger.info(f"Tweet {i+1}: {tweet_result['tweet_id']} - {tweet_result['memory_count']} memories created")
    
    except Exception as e:
        logger.error(f"Error in test_tweet_processor: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_tweet_processor())
