# Marvin's Memory: Feature Overview

## What is Marvin's Memory?

Marvin's Memory is an AI-powered memory management system that stores, organizes, and retrieves various types of content using semantic search. It helps Marvin (our AI persona) maintain a consistent personality and knowledge base across interactions.

## Key Features

### 1. Tweet Processor

- **Automated Tweet Research**: Automatically research tweets from the tweets_cache table
- **Engagement-Based Selection**: Process high-engagement tweets first
- **Cultural Context Analysis**: Analyze tweets for cultural and artistic context
- **Scheduled Processing**: Automatically process tweets every 6 hours
- **Manual Triggering**: Manually trigger tweet processing via API
- **Character-Aligned Insights**: Ensure all insights align with Marvin's persona

### 2. Research Assistant

- **Automated Research**: Conduct research on any topic using Perplexity AI
- **Insight Extraction**: Automatically extract key insights from research results
- **Auto-Approve Option**: Choose to automatically store insights or review them first
- **Insight Review**: Review, select, and approve specific insights to store in memory
- **Confidence Scoring**: Each insight comes with a confidence score

### 2. Memory Stream

- **Chronological View**: See all stored memories in chronological order
- **Content Types**: View different types of memories (research, thoughts, tweets, etc.)
- **Memory Management**: Delete individual memories as needed
- **Metadata Display**: See tags, timestamps, and alignment scores for each memory

### 3. Semantic Search

- **Natural Language Search**: Find memories using natural language queries
- **Similarity Ranking**: Results are ranked by semantic similarity to your query
- **Configurable Results**: Adjust how many results to display
- **Robust Error Handling**: Gracefully handles search errors with fallback mechanisms

### 4. Analytics Dashboard

- **Memory Distribution**: View the distribution of memory types
- **Alignment Scores**: See the distribution of persona alignment scores
- **Memory Timeline**: Track when memories were added over time
- **Tag Analysis**: Identify the most common tags across memories

## Technical Highlights

- **Vector Database**: Uses Qdrant for efficient semantic search
- **Embedding Generation**: Utilizes OpenAI's text-embedding-3-small model
- **Character Alignment**: Ensures all content aligns with Marvin's persona
- **Robust Architecture**: Centralized state management and error handling
- **Caching System**: Optimized performance with smart caching
- **Scheduled Tasks**: Automated processing with APScheduler
- **Supabase Integration**: Seamless connection to tweets_cache table

## User Interface

- **Streamlined Tabs**: Easy navigation between different features
- **Responsive Design**: Works well on different screen sizes
- **Visual Indicators**: Clear visual feedback for actions and states
- **Error Recovery**: Graceful handling of errors with helpful messages

## Getting Started

1. Navigate to the Research tab to conduct research
2. Use the Memory Stream tab to view all stored memories
3. Try the Search tab to find specific information
4. Explore the Analytics tab to gain insights into the memory database

## Best Practices

- Use specific, focused research queries for best results
- Review research insights carefully before approving
- Use tags consistently to improve organization
- Check the Analytics tab periodically to understand memory distribution
- Use search with natural language questions for best results
- Ensure tweets have appropriate engagement scores for processing
- Monitor the tweet processor logs for any issues
