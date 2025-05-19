# Marvin's Memory API Client

This directory contains client examples for connecting to Marvin's Memory API. These clients demonstrate how to properly interact with the API, including handling authentication, pagination, and error recovery.

## Key Changes Made to the API

1. **Added Pagination Support**:
   - The `/memories/` endpoint now supports pagination with `page` and `limit` parameters
   - The response includes pagination metadata (total count, total pages)

2. **Improved Error Handling**:
   - API endpoints now return more detailed error information
   - Search endpoints return empty results instead of errors when no matches are found

3. **Fixed Qdrant Filter Issues**:
   - Added better handling of filter formats for compatibility with the Qdrant server
   - Implemented fallback mechanisms when filters cause errors

## Client Examples

### Python Client (`client_example.py`)

A Python client that demonstrates how to connect to the API with proper error handling and retry logic.

```python
from client_example import MarvinMemoryClient

# Initialize the client
client = MarvinMemoryClient()

# List memories with pagination
memories = client.list_memories(page=1, limit=10)
print(f"Retrieved {len(memories.get('memories', []))} memories")

# Search memories
results = client.search_memories("AI consciousness", limit=3)
print(f"Found {len(results.get('memories', []))} matching memories")
```

### JavaScript Client (`client_example.js`)

A JavaScript client that can be used in both browser and Node.js environments.

```javascript
// In a browser
const client = new MarvinMemoryClient();

// List memories with pagination
client.listMemories({ page: 1, limit: 10 })
  .then(result => {
    console.log(`Retrieved ${result.memories?.length || 0} memories`);
  })
  .catch(error => {
    console.error("Error:", error);
  });

// In Node.js
const { MarvinMemoryClient } = require('./client_example.js');
const client = new MarvinMemoryClient();

async function main() {
  const result = await client.listMemories({ page: 1, limit: 10 });
  console.log(`Retrieved ${result.memories?.length || 0} memories`);
}

main().catch(console.error);
```

### TypeScript Client (`client_example.ts`)

A TypeScript client with full type definitions for better development experience.

```typescript
import MarvinMemoryClient from './client_example';

// Initialize the client
const client = new MarvinMemoryClient();

// List memories with pagination
async function getMemories() {
  const result = await client.listMemories({ page: 1, limit: 10 });
  console.log(`Retrieved ${result.memories?.length || 0} memories`);
  
  // TypeScript provides type safety
  result.memories.forEach(memory => {
    console.log(`Memory ID: ${memory.id}, Type: ${memory.type}`);
  });
}

getMemories().catch(console.error);
```

## Important API URL

The API is accessible at:

```
https://memory.marvn.club/api/
```

Note the `/api/` prefix which is required for all API endpoints.

## Common API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/memories/` | GET | List memories with pagination |
| `/api/memories/search` | GET | Search memories by semantic similarity |
| `/api/memories/` | POST | Create a new memory |
| `/api/memories/{id}` | DELETE | Delete a memory |
| `/api/research/` | POST | Conduct research using Perplexity |
| `/api/research/` | GET | Get all pending research |
| `/api/research/{id}` | GET | Get specific research by ID |
| `/api/research/{id}/approve` | POST | Approve selected insights |
| `/api/tweets/process` | POST | Manually trigger tweet processing |

## Error Handling

All clients include robust error handling with:

1. **Automatic Retries**: For transient errors like timeouts and 502 Bad Gateway responses
2. **Exponential Backoff**: Increasing delay between retry attempts
3. **Detailed Error Information**: Error responses include status codes and messages
4. **Graceful Degradation**: Returning partial results when possible

## Pagination

When listing memories, use pagination to avoid timeouts:

```javascript
// JavaScript example
async function getAllMemories() {
  let page = 1;
  const limit = 50;
  let allMemories = [];
  let hasMore = true;
  
  while (hasMore) {
    const result = await client.listMemories({ page, limit });
    allMemories = allMemories.concat(result.memories || []);
    
    // Check if we've reached the last page
    hasMore = result.pagination && 
              result.pagination.page < result.pagination.pages;
    page++;
  }
  
  return allMemories;
}
```

## Troubleshooting

If you encounter issues:

1. **Check the URL**: Ensure you're using the `/api/` prefix
2. **Verify Pagination**: Use reasonable page sizes (10-50 items)
3. **Handle Timeouts**: Implement retry logic for large requests
4. **Check Network**: Ensure you have connectivity to memory.marvn.club
