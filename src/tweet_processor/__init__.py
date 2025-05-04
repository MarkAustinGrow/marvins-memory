"""
Tweet processor module for Marvin's Memory System.

This module handles the automated processing of tweets from the tweets_cache table,
researching them using Perplexity AI, and storing the insights in Marvin's memory.
"""

from .processor import tweet_processor
from .scheduler import tweet_scheduler

__all__ = ['tweet_processor', 'tweet_scheduler']
