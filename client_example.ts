/**
 * Marvin Memory API Client - TypeScript Version
 * 
 * This client provides methods for interacting with Marvin's Memory API.
 * It includes retry logic for handling timeouts and 502 errors.
 */

// Add Node.js type declarations for runtime environment detection
declare var process: {
  versions: {
    node: string;
  };
};
declare var require: {
  main: any;
};
declare var module: any;

// Configuration
const BASE_URL = "https://memory.marvn.club/api"; // Note the /api prefix
const DEFAULT_TIMEOUT = 30000; // 30 seconds in milliseconds

// Type definitions
export interface Memory {
  id: string;
  content: string;
  type: string;
  source: string;
  timestamp: string;
  tags: string[];
  alignment_score: number;
  similarity_score?: number;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface MemoriesResponse {
  memories: Memory[];
  pagination: PaginationInfo;
  error?: string;
}

export interface SearchResponse {
  memories: Memory[];
  error?: string;
}

export interface CreateMemoryResponse {
  id: string;
  error?: string;
}

export interface DeleteMemoryResponse {
  status: string;
  error?: string;
}

export interface ResearchResponse {
  query_id: string;
  status: string;
  insights?: any[];
  error?: string;
}

export interface PendingResearchResponse {
  pending_research: any[];
  error?: string;
}

export interface ApproveInsightsResponse {
  status: string;
  memory_ids?: string[];
  error?: string;
}

export interface ProcessTweetsResponse {
  processed: number;
  stored: number;
  error?: string;
}

export interface ListMemoriesOptions {
  page?: number;
  limit?: number;
  memoryType?: string;
  minAlignment?: number;
  tags?: string[] | string;
}

export interface SearchMemoriesOptions {
  limit?: number;
  memoryType?: string;
  minAlignment?: number;
  tags?: string[] | string;
}

export interface CreateMemoryOptions {
  content: string;
  type: string;
  source: string;
  tags?: string[];
}

export interface RequestOptions {
  params?: URLSearchParams;
  data?: any;
  retryCount?: number;
  retryDelay?: number;
}

export class MarvinMemoryClient {
  private baseUrl: string;
  private timeout: number;

  /**
   * Initialize the client
   * 
   * @param baseUrl - Base URL for the API
   * @param timeout - Request timeout in milliseconds
   */
  constructor(baseUrl: string = BASE_URL, timeout: number = DEFAULT_TIMEOUT) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * List memories with pagination
   * 
   * @param options - Options for listing memories
   * @returns Promise resolving to memories and pagination info
   */
  async listMemories(options: ListMemoriesOptions = {}): Promise<MemoriesResponse> {
    const {
      page = 1,
      limit = 50,
      memoryType = null,
      minAlignment = null,
      tags = null
    } = options;

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

    return this._makeRequest<MemoriesResponse>("GET", "/memories/", { params });
  }

  /**
   * Search memories by semantic similarity
   * 
   * @param query - Search query
   * @param options - Search options
   * @returns Promise resolving to search results
   */
  async searchMemories(query: string, options: SearchMemoriesOptions = {}): Promise<SearchResponse> {
    const {
      limit = 5,
      memoryType = null,
      minAlignment = null,
      tags = null
    } = options;

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

    return this._makeRequest<SearchResponse>("GET", "/memories/search", { params });
  }

  /**
   * Create a new memory
   * 
   * @param memory - Memory to create
   * @returns Promise resolving to created memory ID
   */
  async createMemory(memory: CreateMemoryOptions): Promise<CreateMemoryResponse> {
    const { content, type, source, tags = null } = memory;

    const data: any = {
      content,
      type,
      source
    };

    if (tags) {
      data.tags = tags;
    }

    return this._makeRequest<CreateMemoryResponse>("POST", "/memories/", { data });
  }

  /**
   * Delete a memory
   * 
   * @param memoryId - Memory ID
   * @returns Promise resolving to deletion status
   */
  async deleteMemory(memoryId: string): Promise<DeleteMemoryResponse> {
    return this._makeRequest<DeleteMemoryResponse>("DELETE", `/memories/${memoryId}`);
  }

  /**
   * Conduct research using Perplexity API
   * 
   * @param query - Research query
   * @param autoApprove - Whether to automatically approve insights
   * @returns Promise resolving to research results
   */
  async conductResearch(query: string, autoApprove: boolean | null = null): Promise<ResearchResponse> {
    const data: any = {
      query
    };

    if (autoApprove !== null) {
      data.auto_approve = autoApprove;
    }

    return this._makeRequest<ResearchResponse>("POST", "/research/", { data });
  }

  /**
   * Get all pending research
   * 
   * @returns Promise resolving to pending research
   */
  async getPendingResearch(): Promise<PendingResearchResponse> {
    return this._makeRequest<PendingResearchResponse>("GET", "/research/");
  }

  /**
   * Get pending research by ID
   * 
   * @param queryId - Research query ID
   * @returns Promise resolving to pending research
   */
  async getPendingResearchById(queryId: string): Promise<ResearchResponse> {
    return this._makeRequest<ResearchResponse>("GET", `/research/${queryId}`);
  }

  /**
   * Approve selected insights for storage
   * 
   * @param queryId - Research query ID
   * @param insightIndices - Indices of insights to approve
   * @returns Promise resolving to approval status
   */
  async approveInsights(queryId: string, insightIndices: number[]): Promise<ApproveInsightsResponse> {
    const data = {
      insight_indices: insightIndices
    };

    return this._makeRequest<ApproveInsightsResponse>("POST", `/research/${queryId}/approve`, { data });
  }

  /**
   * Reject and delete pending research
   * 
   * @param queryId - Research query ID
   * @returns Promise resolving to rejection status
   */
  async rejectResearch(queryId: string): Promise<{ status: string; error?: string }> {
    return this._makeRequest<{ status: string; error?: string }>("DELETE", `/research/${queryId}`);
  }

  /**
   * Manually trigger tweet processing
   * 
   * @param limit - Maximum number of tweets to process
   * @returns Promise resolving to processing results
   */
  async processTweets(limit: number = 10): Promise<ProcessTweetsResponse> {
    const params = new URLSearchParams({
      limit: limit.toString()
    });

    return this._makeRequest<ProcessTweetsResponse>("POST", "/tweets/process", { params });
  }

  /**
   * Make an HTTP request to the API with retry logic
   * 
   * @param method - HTTP method
   * @param endpoint - API endpoint
   * @param options - Request options
   * @returns Promise resolving to response JSON
   * @private
   */
  private async _makeRequest<T>(
    method: string,
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      params = null,
      data = null,
      retryCount = 3,
      retryDelay = 1000
    } = options;

    const url = new URL(`${this.baseUrl}${endpoint}`);
    
    if (params) {
      url.search = params.toString();
    }

    const fetchOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    };

    if (data) {
      fetchOptions.body = JSON.stringify(data);
    }

    let currentRetry = 0;
    let currentDelay = retryDelay;

    while (true) {
      try {
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        fetchOptions.signal = controller.signal;

        const response = await fetch(url.toString(), fetchOptions);
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
          let errorData: any;
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
        return await response.json() as T;

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

        return { error: error.message || 'Unknown error' } as unknown as T;
      }
    }
  }
}

// Example usage
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

// Only run examples if this file is executed directly (not imported)
// Check for Node.js environment
if (typeof process !== 'undefined' && process.versions && process.versions.node) {
  try {
    // We're in Node.js - check if this file is being run directly
    if (require.main === module) {
      runExamples().catch(console.error);
    }
  } catch (e) {
    // Ignore errors in environment detection
    console.error("Error in Node.js environment detection:", e);
  }
}

// Export for module usage
export default MarvinMemoryClient;
