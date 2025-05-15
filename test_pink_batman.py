import asyncio
import json
import logging
from src.tweet_processor.processor import tweet_processor

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_pink_batman_tweet():
    """Test processing the Pink Batman tweet with the curious evaluation approach"""
    
    # Create a mock tweet object with more descriptive content to trigger curiosity
    tweet = {
        "id": 10599,
        "tweet_id": "1922949472088203571",  # Using a unique ID
        "tweet_text": "RT @LudovicCreator: My Pink Batman reimagines the Dark Knight through a glitch aesthetic lens. #AIart #ExperimentalArt",
        "tweet_url": "https://twitter.com/user/status/1922949472088203571",
        "engagement_score": 10.5,
        "public_metrics": json.dumps({"retweet_count": 5, "reply_count": 2, "like_count": 15}),
        "vibe_tags": "art,creative,batman,glitch,experimental",
        "created_at": "2025-05-15 09:52:19.903"
    }
    
    logger.info("Starting Pink Batman tweet test with curious evaluation")
    
    try:
        # First, evaluate if the tweet is worth researching using the curious approach
        evaluation = await tweet_processor.generate_research_query(tweet["tweet_text"])
        
        logger.info(f"Curious evaluation result: {json.dumps(evaluation, indent=2)}")
        
        if evaluation.get("is_worth_researching", False):
            logger.info("Tweet deemed worth researching through curious evaluation!")
            
            # Process the tweet
            result = await tweet_processor.research_tweet(tweet)
            
            if result.get("status") == "error":
                logger.error(f"Research failed: {result.get('error')}")
            else:
                # Process insights into memories
                memory_ids = await tweet_processor.process_insights(result, tweet)
                
                logger.info(f"Created {len(memory_ids)} memories with curious approach")
                logger.info(f"Memory IDs: {memory_ids}")
                
                # Print the research result
                logger.info(f"Research result: {json.dumps(result, indent=2)}")
        else:
            logger.info(f"Tweet NOT deemed worth researching: {evaluation.get('relevance_explanation', '')}")
            
            # Let's try a simpler tweet to see if it gets rejected
            simple_tweet = {
                "id": 10600,
                "tweet_id": "1922949472088203572",
                "tweet_text": "Good morning everyone!",
                "tweet_url": "https://twitter.com/user/status/1922949472088203572",
                "engagement_score": 5.2,
                "public_metrics": json.dumps({"retweet_count": 1, "reply_count": 0, "like_count": 3}),
                "vibe_tags": "morning,greeting",
                "created_at": "2025-05-15 09:53:19.903"
            }
            
            logger.info("Testing a simple tweet for comparison")
            simple_evaluation = await tweet_processor.generate_research_query(simple_tweet["tweet_text"])
            logger.info(f"Simple tweet evaluation: {json.dumps(simple_evaluation, indent=2)}")
    
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_pink_batman_tweet())
