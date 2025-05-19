import requests
import json
import time

# Configuration
BASE_URL = "https://memory.marvn.club/api"  # Note the /api prefix
DEFAULT_TIMEOUT = 30  # seconds

class MarvinMemoryClient:
    """
    Client for interacting with Marvin's Memory API
    """
    
    def __init__(self, base_url=BASE_URL, timeout=DEFAULT_TIMEOUT):
        """
        Initialize the client
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
    
    def list_memories(self, page=1, limit=50, memory_type=None, min_alignment=None, tags=None):
        """
        List memories with pagination
        
        Args:
            page: Page number (starting from 1)
            limit: Maximum number of records per page
            memory_type: Filter by memory type
            min_alignment: Minimum alignment score
            tags: Filter by tags (list or comma-separated string)
            
        Returns:
            Dictionary with memories and pagination info
        """
        params = {
            "page": page,
            "limit": limit
        }
        
        if memory_type:
            params["memory_type"] = memory_type
        
        if min_alignment is not None:
            params["min_alignment"] = min_alignment
        
        if tags:
            if isinstance(tags, list):
                params["tags"] = ",".join(tags)
            else:
                params["tags"] = tags
        
        return self._make_request("GET", "/memories/", params=params)
    
    def search_memories(self, query, limit=5, memory_type=None, min_alignment=None, tags=None):
        """
        Search memories by semantic similarity
        
        Args:
            query: Search query
            limit: Maximum number of results
            memory_type: Filter by memory type
            min_alignment: Minimum alignment score
            tags: Filter by tags (list or comma-separated string)
            
        Returns:
            Dictionary with search results
        """
        params = {
            "query": query,
            "limit": limit
        }
        
        if memory_type:
            params["memory_type"] = memory_type
        
        if min_alignment is not None:
            params["min_alignment"] = min_alignment
        
        if tags:
            if isinstance(tags, list):
                params["tags"] = ",".join(tags)
            else:
                params["tags"] = tags
        
        return self._make_request("GET", "/memories/search", params=params)
    
    def create_memory(self, content, memory_type, source, tags=None):
        """
        Create a new memory
        
        Args:
            content: Memory content
            memory_type: Memory type
            source: Memory source
            tags: Memory tags (list)
            
        Returns:
            Dictionary with created memory ID
        """
        data = {
            "content": content,
            "type": memory_type,
            "source": source
        }
        
        if tags:
            data["tags"] = tags
        
        return self._make_request("POST", "/memories/", json=data)
    
    def delete_memory(self, memory_id):
        """
        Delete a memory
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Dictionary with status
        """
        return self._make_request("DELETE", f"/memories/{memory_id}")
    
    def conduct_research(self, query, auto_approve=None):
        """
        Conduct research using Perplexity API
        
        Args:
            query: Research query
            auto_approve: Whether to automatically approve insights
            
        Returns:
            Dictionary with research results
        """
        data = {
            "query": query
        }
        
        if auto_approve is not None:
            data["auto_approve"] = auto_approve
        
        return self._make_request("POST", "/research/", json=data)
    
    def get_pending_research(self):
        """
        Get all pending research
        
        Returns:
            Dictionary with pending research
        """
        return self._make_request("GET", "/research/")
    
    def get_pending_research_by_id(self, query_id):
        """
        Get pending research by ID
        
        Args:
            query_id: Research query ID
            
        Returns:
            Dictionary with pending research
        """
        return self._make_request("GET", f"/research/{query_id}")
    
    def approve_insights(self, query_id, insight_indices):
        """
        Approve selected insights for storage
        
        Args:
            query_id: Research query ID
            insight_indices: List of insight indices to approve
            
        Returns:
            Dictionary with approval status
        """
        data = {
            "insight_indices": insight_indices
        }
        
        return self._make_request("POST", f"/research/{query_id}/approve", json=data)
    
    def reject_research(self, query_id):
        """
        Reject and delete pending research
        
        Args:
            query_id: Research query ID
            
        Returns:
            Dictionary with rejection status
        """
        return self._make_request("DELETE", f"/research/{query_id}")
    
    def process_tweets(self, limit=10):
        """
        Manually trigger tweet processing
        
        Args:
            limit: Maximum number of tweets to process
            
        Returns:
            Dictionary with processing results
        """
        params = {
            "limit": limit
        }
        
        return self._make_request("POST", "/tweets/process", params=params)
    
    def _make_request(self, method, endpoint, params=None, json=None, retry_count=3, retry_delay=1):
        """
        Make an HTTP request to the API with retry logic
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body
            retry_count: Number of retries
            retry_delay: Delay between retries in seconds
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retry_count + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=self.timeout
                )
                
                # Check if the request was successful
                response.raise_for_status()
                
                # Return the response JSON
                return response.json()
            
            except requests.exceptions.Timeout:
                if attempt < retry_count:
                    print(f"Request timed out. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Increase delay for next retry
                    retry_delay *= 2
                else:
                    print("Request timed out after multiple retries.")
                    return {"error": "Request timed out"}
            
            except requests.exceptions.HTTPError as e:
                if response.status_code == 502 and attempt < retry_count:
                    print(f"Received 502 Bad Gateway. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Increase delay for next retry
                    retry_delay *= 2
                else:
                    print(f"HTTP error: {e}")
                    try:
                        return response.json()
                    except:
                        return {"error": str(e), "status_code": response.status_code}
            
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    client = MarvinMemoryClient()
    
    # Example 1: List memories with pagination
    print("\n=== Example 1: List memories with pagination ===")
    result = client.list_memories(page=1, limit=10)
    print(f"Retrieved {len(result.get('memories', []))} memories")
    print(f"Pagination info: {json.dumps(result.get('pagination', {}), indent=2)}")
    
    # Example 2: Search memories
    print("\n=== Example 2: Search memories ===")
    search_result = client.search_memories("AI consciousness", limit=3)
    print(f"Found {len(search_result.get('memories', []))} matching memories")
    
    # Example 3: Create a memory
    print("\n=== Example 3: Create a memory ===")
    create_result = client.create_memory(
        content="AI systems should be designed with ethical considerations in mind.",
        memory_type="thought",
        source="philosophical reflection",
        tags=["ethics", "AI", "philosophy"]
    )
    print(f"Created memory with ID: {create_result.get('id')}")
    
    # Example 4: Conduct research
    print("\n=== Example 4: Conduct research ===")
    research_result = client.conduct_research(
        query="What are the latest developments in AI ethics?",
        auto_approve=False
    )
    print(f"Research status: {research_result.get('status')}")
    print(f"Research ID: {research_result.get('query_id')}")
