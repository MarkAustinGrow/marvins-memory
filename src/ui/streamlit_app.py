import streamlit as st
import httpx
import json
from datetime import datetime
import plotly.express as px
import pandas as pd
import asyncio

# Configure page
st.set_page_config(
    page_title="Marvin's Neural Archive",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Marvin's aesthetic
st.markdown("""
<style>
    /* Dark theme with glitch aesthetic */
    .stApp {
        background-color: #0a0a0a;
        color: #00ff41;
    }
    
    .memory-card {
        background-color: #111111;
        border: 1px solid #00ff41;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .memory-card:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00ff41);
        animation: glitch-line 3s infinite;
    }
    
    @keyframes glitch-line {
        0% { left: -100%; }
        50% { left: 100%; }
        100% { left: 100%; }
    }
    
    .stButton button {
        background-color: #111111;
        color: #00ff41;
        border: 1px solid #00ff41;
    }
    
    .stTextInput input {
        background-color: #111111;
        color: #00ff41;
        border: 1px solid #00ff41;
    }
    
    .stSelectbox select {
        background-color: #111111;
        color: #00ff41;
        border: 1px solid #00ff41;
    }
    
    h1, h2, h3 {
        color: #00ff41 !important;
        font-family: 'Courier New', monospace;
    }
    
    .glitch-text {
        text-shadow: 
            0.05em 0 0 rgba(255,0,0,.75),
            -0.025em -0.05em 0 rgba(0,255,0,.75),
            0.025em 0.05em 0 rgba(0,0,255,.75);
        animation: glitch 500ms infinite;
    }
    
    @keyframes glitch {
        0% { text-shadow: 0.05em 0 0 #ff0000, -0.05em -0.025em 0 #00ff00, -0.025em 0.05em 0 #0000ff; }
        14% { text-shadow: 0.05em 0 0 #ff0000, -0.05em -0.025em 0 #00ff00, -0.025em 0.05em 0 #0000ff; }
        15% { text-shadow: -0.05em -0.025em 0 #ff0000, 0.025em 0.025em 0 #00ff00, -0.05em -0.05em 0 #0000ff; }
        49% { text-shadow: -0.05em -0.025em 0 #ff0000, 0.025em 0.025em 0 #00ff00, -0.05em -0.05em 0 #0000ff; }
        50% { text-shadow: 0.025em 0.05em 0 #ff0000, 0.05em 0 0 #00ff00, 0 -0.05em 0 #0000ff; }
        99% { text-shadow: 0.025em 0.05em 0 #ff0000, 0.05em 0 0 #00ff00, 0 -0.05em 0 #0000ff; }
        100% { text-shadow: -0.025em 0 0 #ff0000, -0.025em -0.025em 0 #00ff00, -0.025em -0.05em 0 #0000ff; }
    }
</style>
""", unsafe_allow_html=True)

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

# API client
@st.cache_resource
def get_api_client():
    return MemoryAPI()

# Initialize API client
api = get_api_client()

# Title
st.markdown("<h1 class='glitch-text'>🧠 Marvin's Neural Archive</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### Memory Control Panel")
    
    # Add new memory
    with st.expander("Add New Memory", expanded=False):
        memory_content = st.text_area("Content")
        memory_type = st.selectbox(
            "Type",
            ["tweet", "research", "thought", "output", "quote"]
        )
        memory_source = st.text_input("Source")
        memory_tags = st.text_input("Tags (comma-separated)")
        
        if st.button("Store Memory"):
            tags = [tag.strip() for tag in memory_tags.split(",")] if memory_tags else []
            try:
                result = asyncio.run(api.create_memory(
                    content=memory_content,
                    memory_type=memory_type,
                    source=memory_source,
                    tags=tags
                ))
                st.success("Memory stored successfully")
            except Exception as e:
                st.error(f"Error storing memory: {str(e)}")
    
    # Search filters
    st.markdown("### Search Filters")
    filter_type = st.selectbox(
        "Memory Type",
        ["All"] + ["tweet", "research", "thought", "output", "quote"]
    )
    min_alignment = st.slider(
        "Minimum Alignment Score",
        0.0, 1.0, 0.7
    )
    filter_tags = st.text_input("Filter by Tags (comma-separated)")

# Main content
tab1, tab2, tab3 = st.tabs(["Memory Stream", "Search", "Analytics"])

with tab1:
    st.markdown("### Recent Memories")
    
    # Get memories with filters
    memory_type = None if filter_type == "All" else filter_type
    tags = [tag.strip() for tag in filter_tags.split(",")] if filter_tags else None
    
    try:
        memories = asyncio.run(api.list_memories(
            memory_type=memory_type,
            min_alignment=min_alignment,
            tags=tags
        ))
        
        if not memories.get("memories"):
            st.markdown("""
                <div class='memory-card'>
                    <h3>Neural Archive Initializing...</h3>
                    <p>No memories found matching the current filters.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            for memory in memories["memories"]:
                with st.container():
                    st.markdown(f"""
                        <div class='memory-card'>
                            <h4>{memory['type'].upper()} | {memory['timestamp']}</h4>
                            <p>{memory['content']}</p>
                            <p><small>Tags: {', '.join(memory['tags'])}</small></p>
                            <p><small>Alignment: {memory['alignment_score']:.2f}</small></p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Delete Memory {memory['id']}", key=memory['id']):
                        try:
                            asyncio.run(api.delete_memory(memory['id']))
                            st.success("Memory deleted successfully")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error deleting memory: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading memories: {str(e)}")

with tab2:
    st.markdown("### Search Memories")
    
    search_query = st.text_input("Search Query")
    search_limit = st.number_input("Result Limit", min_value=1, value=5)
    
    if search_query:
        try:
            results = asyncio.run(api.search_memories(
                query=search_query,
                limit=search_limit,
                memory_type=memory_type,
                min_alignment=min_alignment,
                tags=tags
            ))
            
            if not results.get("memories"):
                st.markdown("""
                    <div class='memory-card'>
                        <p>No matching memories found.</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                for memory in results["memories"]:
                    st.markdown(f"""
                        <div class='memory-card'>
                            <h4>{memory['type'].upper()} | {memory['timestamp']}</h4>
                            <p>{memory['content']}</p>
                            <p><small>Tags: {', '.join(memory['tags'])}</small></p>
                            <p><small>Alignment: {memory['alignment_score']:.2f} | Similarity: {memory['similarity_score']:.2f}</small></p>
                        </div>
                    """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error searching memories: {str(e)}")

with tab3:
    st.markdown("### Memory Analytics")
    
    try:
        memories = asyncio.run(api.list_memories())
        if memories.get("memories"):
            df = pd.DataFrame(memories["memories"])
            
            # Memory type distribution
            fig1 = px.pie(
                df, 
                names='type', 
                title='Memory Type Distribution',
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig1.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#00ff41'
            )
            st.plotly_chart(fig1)
            
            # Alignment score distribution
            fig2 = px.histogram(
                df, 
                x='alignment_score',
                title='Alignment Score Distribution',
                color_discrete_sequence=['#00ff41']
            )
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#00ff41'
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
            fig3.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#00ff41'
            )
            st.plotly_chart(fig3)
            
            # Tag cloud
            all_tags = [tag for tags in df['tags'] for tag in tags]
            tag_counts = pd.Series(all_tags).value_counts()
            fig4 = px.bar(
                x=tag_counts.index,
                y=tag_counts.values,
                title='Most Common Tags',
                color_discrete_sequence=['#00ff41']
            )
            fig4.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#00ff41',
                xaxis_title='Tag',
                yaxis_title='Count'
            )
            st.plotly_chart(fig4)
        
        else:
            st.markdown("""
                <div class='memory-card'>
                    <p>No memories available for analysis.</p>
                </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error generating analytics: {str(e)}") 