import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

from .processor import tweet_processor

# Set up logging
logger = logging.getLogger(__name__)

class TweetProcessorScheduler:
    """Scheduler for tweet processing"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Set up scheduled jobs"""
        
        # Process tweets every 6 hours
        self.scheduler.add_job(
            self.scheduled_tweet_processing,
            'interval', 
            hours=6,
            id='process_tweets',
            next_run_time=datetime.now()  # Run immediately on startup
        )
    
    async def scheduled_tweet_processing(self):
        """Run scheduled tweet processing"""
        
        logger.info("Starting scheduled tweet processing")
        
        try:
            result = await tweet_processor.process_tweets_batch(limit=10, min_engagement=0.7)
            logger.info(f"Processed {result['processed_count']} tweets, {result['failed_count']} failed")
        except Exception as e:
            logger.error(f"Error in scheduled tweet processing: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Tweet processor scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Tweet processor scheduler shutdown")

# Create singleton instance
tweet_scheduler = TweetProcessorScheduler()
