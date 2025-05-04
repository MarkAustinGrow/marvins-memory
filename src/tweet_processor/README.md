# Tweet Processor Module

This module automates the process of researching tweets from the `tweets_cache` table using Perplexity AI and storing the insights in Marvin's memory system.

## Overview

The Tweet Processor performs the following steps:

1. Selects candidate tweets from the `tweets_cache` table based on engagement score
2. Uses Perplexity AI to research each tweet's cultural and artistic context
3. Processes the research results into insights
4. Stores the insights in Marvin's memory system (with character alignment check)
5. Updates the tweet's status in the `tweets_cache` table

## Components

- **TweetProcessor**: Main class that handles the tweet processing logic
- **TweetProcessorScheduler**: Scheduler that runs the tweet processor on a regular schedule
- **API Endpoint**: FastAPI endpoint for manually triggering tweet processing

## Configuration

The tweet processor uses the following configuration:

- **Engagement Threshold**: Minimum engagement score for tweets to be processed (default: 0.7)
- **Batch Size**: Number of tweets to process in each batch (default: 10)
- **Schedule**: Runs every 6 hours by default

## Usage

### Automatic Processing

The tweet processor scheduler starts automatically when the FastAPI application starts. It will process tweets every 6 hours.

### Manual Processing

You can manually trigger tweet processing using the API endpoint:

```bash
curl -X POST "http://localhost:8000/tweets/process?limit=10&min_engagement=0.7"
```

Or using the test script:

```bash
python -m src.tweet_processor.test_processor
```

### API Response

The API endpoint returns a JSON response with the following structure:

```json
{
  "status": "success",
  "processed_count": 3,
  "failed_count": 0,
  "results": [
    {
      "tweet_id": "1234567890",
      "memory_count": 2
    },
    {
      "tweet_id": "0987654321",
      "memory_count": 3
    },
    {
      "tweet_id": "1122334455",
      "memory_count": 1
    }
  ]
}
```

## Tweets Cache Table Schema

The processor expects the following schema for the `tweets_cache` table:

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary key |
| tweet_id | text | Twitter/X tweet ID |
| tweet_text | text | Content of the tweet |
| tweet_url | text | URL to the original tweet |
| engagement_score | real | Engagement score (higher is better) |
| vibe_tags | text | Comma-separated list of tags |
| created_at | timestamp | When the tweet was created |
| fetched_at | timestamp | When the tweet was added to the cache |
| processed_at | timestamp | When the tweet was processed (null if not processed) |
| memory_ids | text | JSON array of memory IDs created from this tweet |

## Troubleshooting

If the tweet processor is not working as expected, check the following:

1. **No tweets being processed**: Ensure there are unprocessed tweets in the `tweets_cache` table with engagement scores above the threshold
2. **Connection errors**: Verify the Supabase credentials in the `.env` file
3. **Research errors**: Check the Perplexity API key and quota
4. **Memory storage errors**: Ensure the character alignment check is not rejecting the insights

## Logs

The tweet processor logs detailed information about its operations. Look for log messages with the following prefixes:

- `[tweet_processor]`: General tweet processor operations
- `[tweet_processor.research]`: Research-related operations
- `[tweet_processor.memory]`: Memory storage operations
- `[tweet_processor.scheduler]`: Scheduler operations
