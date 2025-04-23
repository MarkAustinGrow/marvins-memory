import streamlit as st
import httpx
import json
from datetime import datetime
import plotly.express as px
import pandas as pd
import asyncio
import time
from functools import wraps

# Configure page
st.set_page_config(
    page_title="Marvin's Neural Archive",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# STATE MANAGEMENT
# =====================================================================

class AppState:
    """Centralized state management for the application"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance"""
        if cls._instance is None:
            cls._instance = AppState()
        return cls._instance
    
    def __init__(self):
        """Initialize the application state"""
        self.async_manager = AsyncManager.get_instance()
        self.api = MemoryAPI(self.async_manager)
        
        # Cache for memory data
        self._memories_cache = None
        self._memories_timestamp = 0
        self._cache_ttl = 10  # Cache TTL in seconds
        
        # Cache for research data
        self._pending_research_cache = None
        self._pending_research_timestamp = 0
        
        # Cache for research settings
        self._research_settings_cache = None
    
    def get_memories(self, force_refresh=False):
        """Get all memories with caching"""
        current_time = time.time()
        
        # Return cached data if it's still fresh
        if not force_refresh and self._memories_cache is not None and (current_time - self._memories_timestamp) < self._cache_ttl:
            return self._memories_cache
        
        # Fetch fresh data
        try:
            memories = self.async_manager.run_async(self.api.list_memories)
            if memories and "status" not in memories:
                self._memories_cache = memories
                self._memories_timestamp = current_time
            return memories
        except Exception as e:
            print(f"Error fetching memories: {str(e)}")
            return {"memories": []} if self._memories_cache is None else self._memories_cache
    
    def get_pending_research(self, force_refresh=False):
        """Get pending research with caching"""
        current_time = time.time()
        
        # Return cached data if it's still fresh
        if not force_refresh and self._pending_research_cache is not None and (current_time - self._pending_research_timestamp) < self._cache_ttl:
            return self._pending_research_cache
        
        # Fetch fresh data
        try:
            pending = self.async_manager.run_async(self.api.get_pending_research)
            if pending and "status" not in pending:
                self._pending_research_cache = pending
                self._pending_research_timestamp = current_time
            return pending
        except Exception as e:
            print(f"Error fetching pending research: {str(e)}")
            return {"pending_research": {}} if self._pending_research_cache is None else self._pending_research_cache
    
    def get_research_settings(self):
        """Get research settings with caching"""
        if self._research_settings_cache is not None:
            return self._research_settings_cache
        
        try:
            settings = self.async_manager.run_async(self.api.get_research_settings)
            if settings and "status" not in settings:
                self._research_settings_cache = settings
            return settings
        except Exception as e:
            print(f"Error fetching research settings: {str(e)}")
            return {"auto_approve": False}
    
    def conduct_research(self, query, auto_approve=None):
        """Conduct research and invalidate caches"""
        result = self.async_manager.run_async(self.api.conduct_research, query=query, auto_approve=auto_approve)
        
        # Invalidate caches
        self._pending_research_cache = None
        self._memories_cache = None
        
        return result
    
    def approve_insights(self, query_id, insight_indices):
        """Approve insights and invalidate caches"""
        result = self.async_manager.run_async(self.api.approve_insights, query_id=query_id, insight_indices=insight_indices)
        
        # Invalidate caches
        self._pending_research_cache = None
        self._memories_cache = None
        
        return result
    
    def reject_research(self, query_id):
        """Reject research and invalidate caches"""
        result = self.async_manager.run_async(self.api.reject_research, query_id=query_id)
        
        # Invalidate caches
        self._pending_research_cache = None
        
        return result
    
    def delete_memory(self, memory_id):
        """Delete memory and invalidate caches"""
        result = self.async_manager.run_async(self.api.delete_memory, memory_id)
        
        # Invalidate caches
        self._memories_cache = None
        
        return result
    
    def search_memories(self, query, limit=5):
        """Search memories"""
        return self.async_manager.run_async(self.api.search_memories, query=query, limit=limit)


class AsyncManager:
    """Manages async operations and resources for the application"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance"""
        if cls._instance is None:
            cls._instance = AsyncManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the async manager"""
        self._client = None
        self._event_loop = None
        self._last_error_time = 0
        self._error_count = 0
        self._max_retries = 3
        
    def get_client(self):
        """Get the shared httpx client"""
        if self._client is None:
            # Create a new client with a longer timeout
            self._client = httpx.AsyncClient(
                base_url="http://localhost:8000",
                timeout=30.0
            )
        return self._client
    
    async def close_client(self):
        """Close the httpx client properly"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    def run_async(self, async_func, *args, **kwargs):
        """
        Run an async function safely in Streamlit with retry logic
        """
        retry_count = 0
        
        while retry_count <= self._max_retries:
            try:
                # Create a new event loop if needed
                if self._event_loop is None or self._event_loop.is_closed():
                    self._event_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._event_loop)
                
                # Run the async function
                result = self._event_loop.run_until_complete(async_func(*args, **kwargs))
                
                # Reset error count on success
                self._error_count = 0
                return result
                
            except httpx.HTTPStatusError as e:
                # Handle HTTP errors (e.g., 400, 500) with more detailed messages
                status_code = e.response.status_code
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get('detail', str(e))
                    error_msg = f"HTTP {status_code} Error: {error_detail}"
                except Exception:
                    error_msg = f"HTTP {status_code} Error: {str(e)}"
                
                st.error(error_msg)
                import traceback
                print(f"HTTP Error: {error_msg}")
                print(f"Traceback: {traceback.format_exc()}")
                
                # Increment retry count and wait before retrying
                retry_count += 1
                if retry_count <= self._max_retries:
                    time.sleep(1)  # Wait 1 second before retrying
                    continue
                
                # Don't raise the exception again to prevent the empty error message
                return {"status": "error", "error": error_msg}
            
            except httpx.RequestError as e:
                # Handle network/connection errors
                error_msg = f"Network Error: {str(e)}"
                st.error(error_msg)
                import traceback
                print(f"Request Error: {error_msg}")
                print(f"Traceback: {traceback.format_exc()}")
                
                # Increment retry count and wait before retrying
                retry_count += 1
                if retry_count <= self._max_retries:
                    time.sleep(1)  # Wait 1 second before retrying
                    continue
                
                return {"status": "error", "error": error_msg}
            
            except asyncio.TimeoutError:
                # Handle timeout errors
                error_msg = "The operation timed out. Please try again."
                st.error(error_msg)
                import traceback
                print(f"Timeout Error")
                print(f"Traceback: {traceback.format_exc()}")
                
                # Increment retry count and wait before retrying
                retry_count += 1
                if retry_count <= self._max_retries:
                    time.sleep(2)  # Wait 2 seconds before retrying timeout errors
                    continue
                
                return {"status": "error", "error": error_msg}
            
            except RuntimeError as e:
                # Specifically handle event loop errors
                error_str = str(e)
                if "is bound to a different event loop" in error_str or "Event loop is closed" in error_str:
                    error_msg = "Event loop error detected. Recreating event loop and retrying..."
                    print(f"Event loop error: {error_str}")
                    
                    # Reset the event loop
                    if self._event_loop and not self._event_loop.is_closed():
                        try:
                            self._event_loop.close()
                        except:
                            pass
                    self._event_loop = None
                    
                    # Increment retry count and wait before retrying
                    retry_count += 1
                    if retry_count <= self._max_retries:
                        time.sleep(0.5)  # Short wait before retrying
                        continue
                    
                    st.error("Maximum retries exceeded for event loop errors. Please refresh the page.")
                    return {"status": "error", "error": error_msg}
                else:
                    # Handle other runtime errors
                    error_msg = f"Runtime Error: {error_str}"
                    st.error(error_msg)
                    import traceback
                    print(f"Runtime error: {error_msg}")
                    print(f"Traceback: {traceback.format_exc()}")
                    return {"status": "error", "error": error_msg}
            
            except Exception as e:
                # Handle all other exceptions
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                import traceback
                error_details = traceback.format_exc()
                print(f"Unexpected error: {error_msg}")
                print(f"Traceback: {error_details}")
                
                # Increment retry count for unexpected errors
                retry_count += 1
                if retry_count <= self._max_retries:
                    time.sleep(1)  # Wait 1 second before retrying
                    continue
                
                # Don't raise the exception again to prevent the empty error message
                return {"status": "error", "error": error_msg}
        
        # This should never be reached, but just in case
        return {"status": "error", "error": "Maximum retries exceeded"}

# =====================================================================
# API CLIENT
# =====================================================================

class MemoryAPI:
    def __init__(self, async_manager=None):
        self.async_manager = async_manager or AsyncManager.get_instance()
    
    async def create_memory(self, content, memory_type, source, tags=None):
        client = self.async_manager.get_client()
        response = await client.post("/memories/", json={
            "content": content,
            "type": memory_type,
            "source": source,
            "tags": tags or []
        })
        return response.json()
    
    async def search_memories(self, query, limit=5, memory_type=None, min_alignment=None, tags=None):
        params = {"query": query, "limit": limit}
        if memory_type:
            params["memory_type"] = memory_type
        if min_alignment:
            params["min_alignment"] = min_alignment
        if tags:
            params["tags"] = tags
        
        client = self.async_manager.get_client()
        response = await client.get("/memories/search", params=params)
        return response.json()
    
    async def list_memories(self, memory_type=None, min_alignment=None, tags=None):
        params = {}
        if memory_type:
            params["memory_type"] = memory_type
        if min_alignment:
            params["min_alignment"] = min_alignment
        if tags:
            params["tags"] = tags
        
        client = self.async_manager.get_client()
        response = await client.get("/memories/", params=params)
        return response.json()
    
    async def delete_memory(self, memory_id):
        client = self.async_manager.get_client()
        response = await client.delete(f"/memories/{memory_id}")
        return response.json()
    
    # Research methods
    async def conduct_research(self, query, auto_approve=None):
        payload = {"query": query}
        if auto_approve is not None:
            payload["auto_approve"] = auto_approve
        
        client = self.async_manager.get_client()
        response = await client.post("/research/", json=payload)
        return response.json()
    
    async def get_pending_research(self):
        client = self.async_manager.get_client()
        response = await client.get("/research/")
        return response.json()
    
    async def get_research_by_id(self, query_id):
        client = self.async_manager.get_client()
        response = await client.get(f"/research/{query_id}")
        return response.json()
    
    async def approve_insights(self, query_id, insight_indices):
        client = self.async_manager.get_client()
        response = await client.post(f"/research/{query_id}/approve", json={
            "insight_indices": insight_indices
        })
        return response.json()
    
    async def reject_research(self, query_id):
        client = self.async_manager.get_client()
        response = await client.delete(f"/research/{query_id}")
        return response.json()
    
    async def get_research_settings(self):
        client = self.async_manager.get_client()
        response = await client.get("/settings/research")
        return response.json()

# Initialize application state
@st.cache_resource
def get_app_state():
    return AppState.get_instance()

# Get app state
app_state = get_app_state()

# Initialize session state for tab selection
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0  # Default to Memory Stream tab

# Title
st.title("🧠 Marvin's Neural Archive")

# Main content - Research tab first so it stays active on page reload
tab_names = ["Research", "Memory Stream", "Search", "Analytics"]
tab1, tab2, tab3, tab4 = st.tabs(tab_names)

# We don't need the JavaScript tab selection anymore since Research is the first tab

with tab1:
    st.header("Research Assistant")
    
    # Research settings
    settings = app_state.get_research_settings()
    auto_approve_default = settings.get("auto_approve", False)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        research_query = st.text_area("Research Question", height=100, 
                                      placeholder="Enter a research question for Perplexity to answer...")
    
    with col2:
        st.subheader("Settings")
        auto_approve_container = st.container()
        with auto_approve_container:
            col_toggle, col_status = st.columns([3, 1])
            with col_toggle:
                auto_approve = st.toggle("Auto-Approve Insights", value=auto_approve_default, 
                                        help="Automatically store insights without review")
            with col_status:
                if auto_approve:
                    st.markdown("✅ <span style='color:green; font-weight:bold;'>ON</span>", unsafe_allow_html=True)
                else:
                    st.markdown("❌ <span style='color:red; font-weight:bold;'>OFF</span>", unsafe_allow_html=True)
    
    if st.button("Conduct Research", type="primary"):
        if not research_query:
            st.error("Please enter a research question")
        else:
            # Set the active tab to Research (index 0 now)
            st.session_state.active_tab = 0
            
            with st.spinner("Researching..."):
                try:
                    result = app_state.conduct_research(
                        query=research_query,
                        auto_approve=auto_approve
                    )
                    
                    if result.get("status") == "error":
                        error_msg = result.get("error", "Unknown error")
                        st.error(f"Research error: {error_msg}")
                        # Log the error for debugging
                        print(f"Research API error: {error_msg}")
                    elif result.get("status") == "pending_approval":
                        st.success(f"Research complete! {len(result.get('insights', []))} insights ready for review.")
                        st.session_state.last_query_id = result.get("query_id")
                        # Ensure we stay on the Research tab
                        st.session_state.active_tab = 0
                    else:
                        st.success(f"Research complete! {result.get('stored_count', 0)} insights stored in memory.")
                        # Ensure we stay on the Research tab
                        st.session_state.active_tab = 0
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    st.error(f"Error conducting research: {str(e)}")
                    # Log the full error for debugging
                    print(f"Research exception details: {error_details}")
    
    # Pending research section
    st.subheader("Pending Research")
    
    # Add note about pending research storage
    st.markdown("""
    <div style="padding: 10px; border-radius: 5px; background-color: #f8f9fa; margin-bottom: 10px;">
        <strong>Note:</strong> Pending research is stored in memory and will be lost if the application is restarted. 
        If you don't see your research here after conducting it, it may have been auto-approved or lost due to a restart.
    </div>
    """, unsafe_allow_html=True)
    
    # Get pending research
    pending = app_state.get_pending_research(force_refresh=True)
    pending_research = pending.get("pending_research", {})
    
    if not pending_research:
        st.info("No pending research to review")
    else:
        # Create tabs for each pending research
        query_ids = list(pending_research.keys())
        
        if "last_query_id" in st.session_state and st.session_state.last_query_id in query_ids:
            # Move the last query to the front
            query_ids.remove(st.session_state.last_query_id)
            query_ids.insert(0, st.session_state.last_query_id)
        
        pending_tabs = st.tabs([f"Research {i+1}" for i in range(len(query_ids))])
        
        for i, query_id in enumerate(query_ids):
            research = pending_research[query_id]
            
            with pending_tabs[i]:
                st.subheader(f"Query: {research['query']}")
                st.write(f"*Timestamp: {research['timestamp']}*")
                
                insights = research.get("insights", [])
                
                if not insights:
                    st.warning("No insights found in this research")
                else:
                    # Create checkboxes for each insight
                    selected_insights = []
                    
                    for j, insight in enumerate(insights):
                        insight_container = st.container()
                        
                        with insight_container:
                            col1, col2 = st.columns([0.1, 0.9])
                            
                            with col1:
                                selected = st.checkbox("", key=f"{query_id}_{j}", value=True)
                                if selected:
                                    selected_insights.append(j)
                            
                            with col2:
                                st.write(insight['content'])
                                st.write(f"Confidence: {insight['confidence']:.2f} | Tags: {', '.join(insight['tags'])}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Approve Selected", key=f"approve_{query_id}"):
                            if not selected_insights:
                                st.error("No insights selected")
                            else:
                                with st.spinner("Storing insights..."):
                                    try:
                                        result = app_state.approve_insights(
                                            query_id=query_id,
                                            insight_indices=selected_insights
                                        )
                                        
                                        if result.get("status") == "error":
                                            st.error(f"Error: {result.get('error')}")
                                        else:
                                            st.success(f"{result.get('stored_count', 0)} insights stored in memory")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error approving insights: {str(e)}")
                    
                    with col2:
                        if st.button("Reject All", key=f"reject_{query_id}"):
                            try:
                                app_state.reject_research(query_id)
                                st.success("Research rejected")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error rejecting research: {str(e)}")
    
    try:
        # This is a placeholder to catch any errors in the pending research section
        pass
    except Exception as e:
        st.error(f"Error loading pending research: {str(e)}")

with tab2:
    st.header("Recent Memories")
    
    # Get memories
    try:
        memories = app_state.get_memories(force_refresh=True)
        
        if not memories.get("memories"):
            st.info("No memories found.")
        else:
            for memory in memories["memories"]:
                st.write(f"**{memory['type'].upper()} | {memory['timestamp']}**")
                st.write(memory['content'])
                st.write(f"Tags: {', '.join(memory['tags'])}")
                st.write(f"Alignment: {memory['alignment_score']:.2f}")
                
                if st.button(f"Delete Memory {memory['id']}", key=memory['id']):
                    try:
                        app_state.delete_memory(memory['id'])
                        st.success("Memory deleted successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting memory: {str(e)}")
                st.divider()
    
    except Exception as e:
        st.error(f"Error loading memories: {str(e)}")

with tab3:
    st.header("Search Memories")
    
    search_query = st.text_input("Search Query")
    search_limit = st.number_input("Result Limit", min_value=1, value=5)
    
    if search_query:
        try:
            results = app_state.search_memories(query=search_query, limit=search_limit)
            
            if not results.get("memories"):
                st.info("No matching memories found.")
            else:
                for memory in results["memories"]:
                    st.write(f"**{memory['type'].upper()} | {memory['timestamp']}**")
                    st.write(memory['content'])
                    st.write(f"Tags: {', '.join(memory['tags'])}")
                    st.write(f"Alignment: {memory['alignment_score']:.2f} | Similarity: {memory['similarity_score']:.2f}")
                    st.divider()
        
        except Exception as e:
            st.error(f"Error searching memories: {str(e)}")

with tab4:
    st.header("Memory Analytics")
    
    try:
        memories = app_state.get_memories(force_refresh=True)
        if memories.get("memories"):
            df = pd.DataFrame(memories["memories"])
            
            # Memory type distribution
            fig1 = px.pie(
                df, 
                names='type', 
                title='Memory Type Distribution',
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig1)
            
            # Alignment score distribution
            fig2 = px.histogram(
                df, 
                x='alignment_score',
                title='Alignment Score Distribution',
                color_discrete_sequence=['#00f7ff']
            )
            st.plotly_chart(fig2)
            
            # Memory timeline
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig3 = px.scatter(
                df,
                x='timestamp',
                y='alignment_score',
                color='type',
                title='Memory Timeline',
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig3)
            
            # Tag cloud
            all_tags = [tag for tags in df['tags'] for tag in tags]
            tag_counts = pd.Series(all_tags).value_counts()
            fig4 = px.bar(
                x=tag_counts.index,
                y=tag_counts.values,
                title='Most Common Tags',
                color_discrete_sequence=['#00f7ff']
            )
            st.plotly_chart(fig4)
        
        else:
            st.info("No memories available for analysis.")
    
    except Exception as e:
        st.error(f"Error generating analytics: {str(e)}")
