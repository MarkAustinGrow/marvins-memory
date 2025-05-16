# Marvin's Memory System Documentation

## Overview
Marvin's Memory System is a sophisticated AI memory management system that enables persistent storage and retrieval of various types of content using vector embeddings. The system is built using Qdrant for vector storage, Supabase for metadata management, and integrates with LLMs for intelligent recall and response generation. The system features a curious evaluation approach that prioritizes creative interpretation and exploration over strict relevance.

## Architecture

### Core Components

1. **Vector Database (Qdrant)**
   - Host: qdrant.marvn.club
   - Port: 6333
   - Stores vector embeddings of various content types
   - Enables semantic search and similarity matching

2. **Application Services**
   - FastAPI backend (port 8000)
   - Streamlit UI (port 8501)
   - Docker containerized deployment

### Directory Structure

```
src/
├── api/           # FastAPI endpoints and routes
├── character/     # AI character configuration and personality
│   └── prompts/   # Prompt templates for character evaluation
├── database/      # Database connections and models
├── embeddings/    # Embedding generation and management
├── memory/        # Memory management and retrieval logic
├── tweet_processor/ # Tweet processing and research automation
├── ui/            # Streamlit interface components
└── config.py      # Application configuration
```

## Key Features

### Memory Types
The system stores and manages several types of content:

1. **Tweets**
   - High-engagement tweets from cache
   - Includes engagement metrics and context

2. **Research**
   - Perplexity summaries
   - Key insights and findings

3. **Marvin's Thoughts**
   - Manually added notes
   - Personality and belief system

4. **Past Outputs**
   - Historical replies and generated content
   - Response patterns and styles

5. **Quote Inspiration**
   - High-vibe lines and phrases
   - Reusable content elements

### Memory Schema
Each memory entry contains:

- `id`: UUID for internal reference
- `type`: Content category (tweet, research, thought, etc.)
- `source`: Origin of the content
- `content`: Full text content
- `tags`: Topic categorization (including "curious" tag for memories from curious evaluation)
- `timestamp`: Creation/update time
- `agent_id`: Persona identifier
- `metadata`: Additional contextual information:
  - `relevance_type`: How the content was determined to be relevant (e.g., "curious")
  - `relevance_explanation`: Explanation of why the content was deemed relevant
  - `research_question`: The question that guided the research (for research memories)
  - `alignment_score`: Numerical score of alignment with character (0.0-1.0)

## Technical Implementation

### Database Integration
- Qdrant for vector storage
- Supabase for metadata management
- OpenAI embeddings (text-embedding-3-small, 1536 dimensions)

### Character Alignment
- Content is evaluated for alignment with Marvin's character using two approaches:
  1. **Traditional Alignment**: Evaluates how well content matches Marvin's interests
  2. **Curious Evaluation**: Prioritizes creative interpretation and exploration
- Alignment evaluation includes:
  - Score (0.0-1.0)
  - Matched aspects
  - Explanation of alignment
- The curious evaluation can bypass the alignment score threshold
- Prompt-based guidelines stored in character/prompts/curious_eval.txt
- Higher temperature (0.9) used for more creative evaluations

### Error Handling
- Robust error handling throughout the codebase
- Fallback mechanisms for component failures
- Graceful degradation when services are unavailable
- Detailed logging for debugging and monitoring
- Zero-vector fallbacks for embedding generation failures
- Comprehensive retry logic for API calls
  - Configurable retry counts and backoff strategy
  - Different retry policies based on error type
  - Automatic recovery from transient network issues
- Improved exception handling in search functionality
  - Detailed error logging with full stack traces
  - Graceful recovery from search failures
  - Return of empty results instead of error responses
  - Individual result processing to prevent cascading failures

### Qdrant Integration
- Vector similarity search using cosine distance
- Filter structure for Qdrant queries:
  ```json
  {
    "must": [
      {
        "key": "field_name",
        "match": { "value": "field_value" }
      },
      {
        "key": "numeric_field",
        "range": { "gte": min_value, "lte": max_value }
      }
    ]
  }
  ```
- Auto-correction mechanism for filter formats
- Enhanced search reliability features:
  - Fallback to unfiltered queries when filter issues occur
  - Detailed logging of filter structures for debugging
  - Automatic filter format validation and correction
  - Progressive degradation of filter complexity on errors
  - Graceful handling of Qdrant API version incompatibilities
- Search optimization:
  - Efficient vector comparison with cosine distance
  - Proper handling of embedding dimensions (1536D)
  - Configurable search limits and thresholds

### API Endpoints
- Memory retrieval and search
- Content embedding and storage
- Memory management operations
- Tweet processing and research

### Scheduled Tasks
- Tweet processing runs every 6 hours
- Selects high-engagement tweets from tweets_cache
- Evaluates tweets using the curious evaluation approach
- Researches tweets deemed worth exploring using Perplexity AI
- Stores insights in memory with bypass_alignment_check=True
- Adds "curious" tag to memories created through this process
- Preserves research questions and relevance explanations in metadata

### UI Components
- Memory inspection and management
- Content addition and editing
- Search and filtering interface
- Centralized state management with AppState pattern
  - Singleton instance for consistent state across components
  - Caching mechanism for API responses with configurable TTL
  - Automatic cache invalidation on data changes
  - Reduced redundant API calls through shared state
- Robust async operations with AsyncManager
  - Proper event loop lifecycle management
  - Automatic retry mechanism for transient errors
  - Shared httpx client for all API calls
  - Graceful error recovery and fallback strategies

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Access to Qdrant server
- Environment variables (see .env.example)

### Running the Application
```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f
```

### Environment Configuration
Key environment variables:
- `QDRANT_HOST`: Vector database host
- `QDRANT_PORT`: Vector database port
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `PERPLEXITY_API_KEY`: Perplexity API key for research
- `SUPABASE_URL`: Supabase URL for metadata and tweets_cache
- `SUPABASE_KEY`: Supabase API key
- Additional configuration in .env file

## Best Practices

### Code Organization
- Follows SOLID principles
- Modular architecture
- Clear separation of concerns

### Memory Management
- Regular cleanup of outdated content
- Tag-based organization
- Semantic search optimization

### Performance Considerations
- Batch processing for embeddings
- Caching frequently accessed memories
- Optimized vector search queries

## Future Development

### Planned Features
1. **Enhanced Curious Evaluation**:
   - Further refinement of the curious evaluation prompts
   - Adaptive temperature settings based on content type
   - Expanded prompt bank with specialized evaluation guidelines

2. **Memory Chaining**:
   - Implementing connections between related memories
   - Creating a web of associations between curious memories
   - Exploring thematic relationships across different content types

3. **Curiosity Metrics**:
   - Tracking and visualizing the impact of curious evaluation
   - Measuring memory diversity and exploration breadth
   - Comparing traditional vs. curious memory acquisition

4. **Automated Prompt Refinement**:
   - Self-improving prompt guidelines based on memory quality
   - A/B testing of different curious evaluation approaches
   - Feedback loop from memory usage to prompt adjustment

5. **Random Exploration**:
   - Occasional random selection of content for research
   - Serendipity-driven memory acquisition
   - Controlled randomness to discover unexpected connections

### Roadmap
See `Roadmap.md` for detailed development plans and milestones.

## Troubleshooting

### Common Issues
1. Tweet processing issues
   - Check Supabase connection to tweets_cache table
   - Verify Perplexity API key and quota
   - Ensure tweets have engagement scores
   - Check scheduler is running (logs should show "Tweet processor scheduler started")
   - Look for "Starting scheduled tweet processing" in logs
   - Try manual processing with the test script or API endpoint

2. Qdrant connection timeouts
   - Verify Qdrant server accessibility
   - Check network configuration
   - Validate credentials
   - Ensure Qdrant client version compatibility (client: 1.14.1)

2. Memory retrieval problems
   - Check embedding generation
   - Verify vector database health
   - Review search parameters
   - Ensure filter format matches Qdrant expectations (see Qdrant Integration section)
   - Check logs for "Error in search with filter" messages
   - Verify the search query vector has the correct dimensions (1536)
   - Examine if fallback search without filters is working
   - Review the API response for error details in the returned JSON

3. Search returning no results
   - Verify that embeddings are being generated correctly
   - Check if the query is semantically similar to stored content
   - Examine filter conditions to ensure they're not too restrictive
   - Look for "Fallback search returned X results" in logs
   - Try searching without filters as a test
   - Verify the search endpoint is returning 200 OK (not 500)

3. Character alignment failures
   - Check character data is loaded correctly from Supabase
   - Verify alignment evaluation implementation
   - Review minimum alignment score threshold
   - Check if curious_eval.txt file exists in character/prompts directory
   - Verify the curious evaluation is working by checking logs for "Research evaluation: worth_researching=True"
   - Look for "bypass_alignment_check=True" in logs to confirm threshold bypass is working

4. NoneType errors in component interactions
   - Check for proper error handling in component interfaces
   - Verify all methods return expected values even in error cases
   - Add defensive programming with null checks

### Logging
- Application logs available via Docker
- Detailed error tracking
- Performance metrics
- Enhanced debug logging for troubleshooting:
  - Filter structure and processing
  - Character alignment evaluation
  - Embedding generation
  - API endpoint request/response
  - Search query parameters and results
  - Fallback mechanism activations
  - Event loop lifecycle events
  - API retry attempts and outcomes
- Structured logging format for easier parsing
- Comprehensive error logging with stack traces
- Log levels can be adjusted in the code
- View logs with `docker-compose logs --follow`
- Key log patterns to look for:
  - "Error in search with filter" - Indicates filter issues
  - "Fallback search returned X results" - Shows fallback mechanism working
  - "Trying without filter as fallback" - Filter bypass activated
  - "Event loop error" - UI async operation issues
  - "Retry attempt X of Y" - API retry mechanism in action
  - "Research evaluation: worth_researching=True" - Curious evaluation found value in content
  - "Relevance explanation:" - Shows reasoning behind curious evaluation
  - "Generated research question:" - Research question from curious evaluation
  - "bypass_alignment_check=True" - Alignment threshold being bypassed
  - "Created X memories with curious approach" - Successful memory creation

## Contributing
Please refer to the project's contribution guidelines for information on:
- Code style
- Pull request process
- Testing requirements
- Documentation standards
