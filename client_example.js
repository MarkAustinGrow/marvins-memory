/**
 * Marvin Memory API Client
 * 
 * This client provides methods for interacting with Marvin's Memory API.
 * It includes retry logic for handling timeouts and 502 errors.
 */

// Configuration
const BASE_URL = "https://memory.marvn.club/api"; // Note the /api prefix
const DEFAULT_TIMEOUT = 30000; // 30 seconds in milliseconds

class MarvinMemoryClient {
  /**
   * Initialize the client
   * 
   * @param {string} baseUrl - Base URL for the API
   * @param {number} timeout - Request timeout in milliseconds
   */
  constructor(baseUrl = BASE_URL, timeout = DEFAULT_TIMEOUT) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * List memories with pagination
   * 
   * @param {Object} options - Options for listing memories
   * @param {number} options.page - Page number (starting from 1)
   * @param {number} options.limit - Maximum number of records per page
   * @param {string} options.memoryType - Filter by memory type
   * @param {number} options.minAlignment - Minimum alignment score
   * @param {string|string[]} options.tags - Filter by tags
   * @returns {Promise<Object>} - Promise resolving to memories and pagination info
   */
  async listMemories({
    page = 1,
    limit = 50,
    memoryType = null,
    minAlignment = null,
    tags = null
  } = {}) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString()
    });

    if (memoryType) {
      params.append("memory_type", memoryType);
    }

    if (minAlignment !== null) {
      params.append("min_alignment", minAlignment.toString());
    }

    if (tags) {
      if (Array.isArray(tags)) {
        params.append("tags", tags.join(","));
      } else {
        params.append("tags", tags);
      }
    }

    return this._makeRequest("GET", "/memories/", { params });
  }

  /**
   * Search memories by semantic similarity
   * 
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @param {number} options.limit - Maximum number of results
   * @param {string} options.memoryType - Filter by memory type
   * @param {number} options.minAlignment - Minimum alignment score
   * @param {string|string[]} options.tags - Filter by tags
   * @returns {Promise<Object>} - Promise resolving to search results
   */
  async searchMemories(query, {
    limit = 5,
    memoryType = null,
    minAlignment = null,
    tags = null
  } = {}) {
    const params = new URLSearchParams({
      query,
      limit: limit.toString()
    });

    if (memoryType) {
      params.append("memory_type", memoryType);
    }

    if (minAlignment !== null) {
      params.append("min_alignment", minAlignment.toString());
    }

    if (tags) {
      if (Array.isArray(tags)) {
        params.append("tags", tags.join(","));
      } else {
        params.append("tags", tags);
      }
    }

    return this._makeRequest("GET", "/memories/search", { params });
  }

  /**
   * Create a new memory
   * 
   * @param {Object} memory - Memory to create
   * @param {string} memory.content - Memory content
   * @param {string} memory.type - Memory type
   * @param {string} memory.source - Memory source
   * @param {string[]} memory.tags - Memory tags
   * @returns {Promise<Object>} - Promise resolving to created memory ID
   */
  async createMemory({ content, type, source, tags = null }) {
    const data = {
      content,
      type,
      source
    };

    if (tags) {
      data.tags = tags;
    }

    return this._makeRequest("POST", "/memories/", { data });
  }

  /**
   * Delete a memory
   * 
   * @param {string} memoryId - Memory ID
   * @returns {Promise<Object>} - Promise resolving to deletion status
   */
  async deleteMemory(memoryId) {
    return this._makeRequest("DELETE", `/memories/${memoryId}`);
  }

  /**
   * Conduct research using Perplexity API
   * 
   * @param {string} query - Research query
   * @param {boolean} autoApprove - Whether to automatically approve insights
   * @returns {Promise<Object>} - Promise resolving to research results
   */
  async conductResearch(query, autoApprove = null) {
    const data = {
      query
    };

    if (autoApprove !== null) {
      data.auto_approve = autoApprove;
    }

    return this._makeRequest("POST", "/research/", { data });
  }

  /**
   * Get all pending research
   * 
   * @returns {Promise<Object>} - Promise resolving to pending research
   */
  async getPendingResearch() {
    return this._makeRequest("GET", "/research/");
  }

  /**
   * Get pending research by ID
   * 
   * @param {string} queryId - Research query ID
   * @returns {Promise<Object>} - Promise resolving to pending research
   */
  async getPendingResearchById(queryId) {
    return this._makeRequest("GET", `/research/${queryId}`);
  }

  /**
   * Approve selected insights for storage
   * 
   * @param {string} queryId - Research query ID
   * @param {number[]} insightIndices - Indices of insights to approve
   * @returns {Promise<Object>} - Promise resolving to approval status
   */
  async approveInsights(queryId, insightIndices) {
    const data = {
      insight_indices: insightIndices
    };

    return this._makeRequest("POST", `/research/${queryId}/approve`, { data });
  }

  /**
   * Reject and delete pending research
   * 
   * @param {string} queryId - Research query ID
   * @returns {Promise<Object>} - Promise resolving to rejection status
   */
  async rejectResearch(queryId) {
    return this._makeRequest("DELETE", `/research/${queryId}`);
  }

  /**
   * Manually trigger tweet processing
   * 
   * @param {number} limit - Maximum number of tweets to process
   * @returns {Promise<Object>} - Promise resolving to processing results
   */
  async processTweets(limit = 10) {
    const params = new URLSearchParams({
      limit: limit.toString()
    });

    return this._makeRequest("POST", "/tweets/process", { params });
  }

  /**
   * Make an HTTP request to the API with retry logic
   * 
   * @param {string} method - HTTP method
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Request options
   * @param {URLSearchParams} options.params - Query parameters
   * @param {Object} options.data - Request body
   * @param {number} options.retryCount - Number of retries
   * @param {number} options.retryDelay - Delay between retries in milliseconds
   * @returns {Promise<Object>} - Promise resolving to response JSON
   * @private
   */
  async _makeRequest(method, endpoint, {
    params = null,
    data = null,
    retryCount = 3,
    retryDelay = 1000
  } = {}) {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    
    if (params) {
      url.search = params.toString();
    }

    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    let currentRetry = 0;
    let currentDelay = retryDelay;

    while (true) {
      try {
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        options.signal = controller.signal;

        const response = await fetch(url.toString(), options);
        clearTimeout(timeoutId);

        // Check if the request was successful
        if (!response.ok) {
          // Handle 502 Bad Gateway with retry
          if (response.status === 502 && currentRetry < retryCount) {
            console.log(`Received 502 Bad Gateway. Retrying in ${currentDelay / 1000} seconds...`);
            await new Promise(resolve => setTimeout(resolve, currentDelay));
            currentRetry++;
            currentDelay *= 2;
            continue;
          }

          // Try to get error details from response
          let errorData;
          try {
            errorData = await response.json();
          } catch (e) {
            errorData = { error: response.statusText };
          }

          throw new Error(JSON.stringify({
            status: response.status,
            statusText: response.statusText,
            ...errorData
          }));
        }

        // Parse and return the response JSON
        return await response.json();

      } catch (error) {
        // Handle timeout with retry
        if (error.name === 'AbortError' && currentRetry < retryCount) {
          console.log(`Request timed out. Retrying in ${currentDelay / 1000} seconds...`);
          await new Promise(resolve => setTimeout(resolve, currentDelay));
          currentRetry++;
          currentDelay *= 2;
          continue;
        }

        // Handle other errors or max retries reached
        if (currentRetry >= retryCount) {
          console.log('Max retries reached');
        }

        return { error: error.message || 'Unknown error' };
      }
    }
  }
}

// Example usage (for Node.js)
if (typeof require !== 'undefined') {
  // This code will only run in Node.js
  async function runExamples() {
    const client = new MarvinMemoryClient();
    
    try {
      // Example 1: List memories with pagination
      console.log("\n=== Example 1: List memories with pagination ===");
      const result = await client.listMemories({ page: 1, limit: 10 });
      console.log(`Retrieved ${result.memories?.length || 0} memories`);
      console.log(`Pagination info:`, result.pagination);
      
      // Example 2: Search memories
      console.log("\n=== Example 2: Search memories ===");
      const searchResult = await client.searchMemories("AI consciousness", { limit: 3 });
      console.log(`Found ${searchResult.memories?.length || 0} matching memories`);
      
      // Example 3: Create a memory
      console.log("\n=== Example 3: Create a memory ===");
      const createResult = await client.createMemory({
        content: "AI systems should be designed with ethical considerations in mind.",
        type: "thought",
        source: "philosophical reflection",
        tags: ["ethics", "AI", "philosophy"]
      });
      console.log(`Created memory with ID: ${createResult.id}`);
      
      // Example 4: Conduct research
      console.log("\n=== Example 4: Conduct research ===");
      const researchResult = await client.conductResearch(
        "What are the latest developments in AI ethics?",
        false
      );
      console.log(`Research status: ${researchResult.status}`);
      console.log(`Research ID: ${researchResult.query_id}`);
      
    } catch (error) {
      console.error("Error running examples:", error);
    }
  }
  
  // Run the examples
  runExamples().catch(console.error);
}

// Export for browser or module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MarvinMemoryClient };
} else if (typeof window !== 'undefined') {
  window.MarvinMemoryClient = MarvinMemoryClient;
}
