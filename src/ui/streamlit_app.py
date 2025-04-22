import streamlit as st
import httpx
import json
from datetime import datetime
import plotly.express as px
import pandas as pd
import asyncio

# Helper function to run async functions safely in Streamlit
def run_async(async_func, *args, **kwargs):
    try:
        # Create a new event loop for each async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_func(*args, **kwargs))
    except Exception as e:
        st.error(f"Async operation error: {str(e)}")
        raise e
    finally:
        # Clean up the loop
        if loop.is_running():
            loop.stop()
        if not loop.is_closed():
            loop.close()

# Configure page
st.set_page_config(
    page_title="Marvin's Neural Archive",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API client
class MemoryAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def create_memory(self, content, memory_type, source, tags=None):
        response = await self.client.post("/memories/", json={
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
        
        response = await self.client.get("/memories/search", params=params)
        return response.json()
    
    async def list_memories(self, memory_type=None, min_alignment=None, tags=None):
        params = {}
        if memory_type:
            params["memory_type"] = memory_type
        if min_alignment:
            params["min_alignment"] = min_alignment
        if tags:
            params["tags"] = tags
        
        response = await self.client.get("/memories/", params=params)
        return response.json()
    
    async def delete_memory(self, memory_id):
        response = await self.client.delete(f"/memories/{memory_id}")
        return response.json()
    
    # Research methods
    async def conduct_research(self, query, auto_approve=None):
        payload = {"query": query}
        if auto_approve is not None:
            payload["auto_approve"] = auto_approve
            
        response = await self.client.post("/research/", json=payload)
        return response.json()
    
    async def get_pending_research(self):
        response = await self.client.get("/research/")
        return response.json()
    
    async def get_research_by_id(self, query_id):
        response = await self.client.get(f"/research/{query_id}")
        return response.json()
    
    async def approve_insights(self, query_id, insight_indices):
        response = await self.client.post(f"/research/{query_id}/approve", json={
            "insight_indices": insight_indices
        })
        return response.json()
    
    async def reject_research(self, query_id):
        response = await self.client.delete(f"/research/{query_id}")
        return response.json()
    
    async def get_research_settings(self):
        response = await self.client.get("/settings/research")
        return response.json()

# API client
@st.cache_resource
def get_api_client():
    return MemoryAPI()

# Initialize API client
api = get_api_client()

# Title
st.title("🧠 Marvin's Neural Archive")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["Memory Stream", "Search", "Research", "Analytics"])

with tab1:
    st.header("Recent Memories")
    
    # Get memories
    try:
        memories = run_async(api.list_memories)
        
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
                        run_async(api.delete_memory, memory['id'])
                        st.success("Memory deleted successfully")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error deleting memory: {str(e)}")
                st.divider()
    
    except Exception as e:
        st.error(f"Error loading memories: {str(e)}")

with tab2:
    st.header("Search Memories")
    
    search_query = st.text_input("Search Query")
    search_limit = st.number_input("Result Limit", min_value=1, value=5)
    
    if search_query:
        try:
            results = run_async(api.search_memories, query=search_query, limit=search_limit)
            
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

with tab3:
    st.header("Research Assistant")
    
    # Research settings
    try:
        settings = run_async(api.get_research_settings)
        auto_approve_default = settings.get("auto_approve", False)
    except Exception:
        auto_approve_default = False
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        research_query = st.text_area("Research Question", height=100, 
                                      placeholder="Enter a research question for Perplexity to answer...")
    
    with col2:
        st.subheader("Settings")
        auto_approve = st.toggle("Auto-Approve Insights", value=auto_approve_default, 
                                help="Automatically store insights without review")
    
    if st.button("Conduct Research", type="primary"):
        if not research_query:
            st.error("Please enter a research question")
        else:
            with st.spinner("Researching..."):
                try:
                    result = run_async(api.conduct_research,
                        query=research_query,
                        auto_approve=auto_approve
                    )
                    
                    if result.get("status") == "error":
                        st.error(f"Research error: {result.get('error')}")
                    elif result.get("status") == "pending_approval":
                        st.success(f"Research complete! {len(result.get('insights', []))} insights ready for review.")
                        st.session_state.last_query_id = result.get("query_id")
                    else:
                        st.success(f"Research complete! {result.get('stored_count', 0)} insights stored in memory.")
                except Exception as e:
                    st.error(f"Error conducting research: {str(e)}")
    
    # Pending research section
    st.subheader("Pending Research")
    
    try:
        pending = run_async(api.get_pending_research)
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
                                            result = run_async(api.approve_insights,
                                                query_id=query_id,
                                                insight_indices=selected_insights
                                            )
                                            
                                            if result.get("status") == "error":
                                                st.error(f"Error: {result.get('error')}")
                                            else:
                                                st.success(f"{result.get('stored_count', 0)} insights stored in memory")
                                                st.experimental_rerun()
                                        except Exception as e:
                                            st.error(f"Error approving insights: {str(e)}")
                        
                        with col2:
                            if st.button("Reject All", key=f"reject_{query_id}"):
                                try:
                                    run_async(api.reject_research, query_id)
                                    st.success("Research rejected")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error rejecting research: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading pending research: {str(e)}")

with tab4:
    st.header("Memory Analytics")
    
    try:
        memories = run_async(api.list_memories)
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
