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
    /* Import futuristic fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&family=Rajdhani:wght@300;400;500;700&display=swap');
    
    /* Dark theme with enhanced glitch aesthetic */
    .stApp {
        background-color: #0a0a0a;
        color: #00f7ff;
        background-image: 
            radial-gradient(circle at 25% 25%, rgba(5, 5, 30, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(20, 0, 50, 0.2) 0%, transparent 50%),
            repeating-linear-gradient(rgba(60, 60, 60, 0.05) 0px, rgba(60, 60, 60, 0.05) 1px, transparent 1px, transparent 2px);
    }
    
    /* Scanline effect for the entire app */
    .stApp:after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
        background-size: 100% 4px;
        z-index: 999;
        opacity: 0.15;
    }
    
    /* Enhanced memory card with holographic styling */
    .memory-card {
        background-color: rgba(17, 17, 17, 0.8);
        border: 1px solid;
        border-image: linear-gradient(135deg, #00f7ff, #ff00e6, #00f7ff) 1;
        border-radius: 5px;
        padding: 1.2rem;
        margin: 1.2rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 15px rgba(0, 247, 255, 0.15), 
                    inset 0 0 10px rgba(255, 0, 230, 0.05);
        transition: all 0.3s ease;
    }
    
    /* Hover effect for memory cards */
    .memory-card:hover {
        box-shadow: 0 0 20px rgba(0, 247, 255, 0.3), 
                    inset 0 0 15px rgba(255, 0, 230, 0.1);
        transform: translateY(-2px);
    }
    
    /* Multiple glitch line animations */
    .memory-card:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00f7ff, #ff00e6, transparent);
        animation: glitch-line-horizontal 4s infinite;
    }
    
    .memory-card:after {
        content: '';
        position: absolute;
        top: -100%;
        left: 0;
        width: 2px;
        height: 100%;
        background: linear-gradient(180deg, transparent, #ff00e6, #00f7ff, transparent);
        animation: glitch-line-vertical 5s infinite;
        animation-delay: 2s;
    }
    
    /* Error message styling */
    .element-container div[data-testid="stAlert"] {
        background: rgba(30, 0, 0, 0.7) !important;
        border: 1px solid #ff3366 !important;
        color: #ff6699 !important;
        text-shadow: 0 0 5px #ff3366;
    }
    
    /* Success message styling */
    .element-container div[data-testid="stAlert"][data-baseweb="notification"] {
        background: rgba(0, 30, 15, 0.7) !important;
        border: 1px solid #00ff99 !important;
        color: #00ffaa !important;
        text-shadow: 0 0 5px #00ff99;
    }
    
    /* Animations for glitch effects */
    @keyframes glitch-line-horizontal {
        0% { left: -100%; }
        40% { left: 100%; }
        100% { left: 100%; }
    }
    
    @keyframes glitch-line-vertical {
        0% { top: -100%; }
        40% { top: 100%; }
        100% { top: 100%; }
    }
    
    /* Enhanced button styling */
    .stButton button {
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(20, 20, 40, 0.8));
        color: #00f7ff;
        border: 1px solid;
        border-image: linear-gradient(135deg, #00f7ff, #ff00e6) 1;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 500;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .stButton button:hover {
        box-shadow: 0 0 15px rgba(0, 247, 255, 0.4);
        text-shadow: 0 0 5px rgba(0, 247, 255, 0.7);
    }
    
    .stButton button:active {
        background: linear-gradient(135deg, rgba(20, 20, 40, 0.8), rgba(0, 0, 0, 0.8));
    }
    
    /* Primary button with special styling */
    .stButton button[data-baseweb="button"][kind="primary"] {
        background: linear-gradient(135deg, rgba(0, 80, 80, 0.8), rgba(80, 0, 80, 0.8));
        border: 1px solid #00f7ff;
        box-shadow: 0 0 10px rgba(0, 247, 255, 0.3);
    }
    
    .stButton button[data-baseweb="button"][kind="primary"]:hover {
        background: linear-gradient(135deg, rgba(0, 100, 100, 0.8), rgba(100, 0, 100, 0.8));
        box-shadow: 0 0 20px rgba(0, 247, 255, 0.5);
    }
    
    /* Form input styling */
    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stNumberInput input {
        background-color: rgba(17, 17, 17, 0.7);
        color: #00f7ff;
        border: 1px solid;
        border-image: linear-gradient(135deg, #00f7ff, #ff00e6) 1;
        font-family: 'Rajdhani', sans-serif;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border: 1px solid #00f7ff;
        box-shadow: 0 0 10px rgba(0, 247, 255, 0.3);
    }
    
    /* Checkbox styling */
    .stCheckbox label span[data-baseweb="checkbox"] div[data-testid="stCheckbox"] {
        border-color: #00f7ff !important;
    }
    
    .stCheckbox label span[data-baseweb="checkbox"] div[data-testid="stCheckbox"] svg {
        fill: #ff00e6 !important;
    }
    
    /* Toggle styling */
    label[data-testid="stWidgetLabel"] span[data-baseweb="checkbox"] {
        background-color: rgba(17, 17, 17, 0.7) !important;
    }
    
    label[data-testid="stWidgetLabel"] span[data-baseweb="checkbox"] div {
        background-color: #ff00e6 !important;
    }
    
    /* Typography styling */
    h1, h2, h3 {
        color: #00f7ff !important;
        font-family: 'Orbitron', sans-serif;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    h4, h5, h6 {
        color: #ff00e6 !important;
        font-family: 'Rajdhani', sans-serif;
        letter-spacing: 0.5px;
    }
    
    p, li, span {
        font-family: 'Rajdhani', sans-serif;
    }
    
    /* Enhanced glitch text effect */
    .glitch-text {
        font-family: 'Orbitron', sans-serif;
        position: relative;
        text-shadow: 
            0.05em 0 0 rgba(255, 0, 230, 0.75),
            -0.025em -0.05em 0 rgba(0, 247, 255, 0.75),
            0.025em 0.05em 0 rgba(255, 255, 0, 0.75);
        animation: enhanced-glitch 1s infinite;
        letter-spacing: 2px;
    }
    
    .glitch-text:before,
    .glitch-text:after {
        content: attr(data-text);
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
    
    .glitch-text:before {
        left: 2px;
        text-shadow: -2px 0 #ff00e6;
        animation: glitch-anim-1 2s infinite linear alternate-reverse;
    }
    
    .glitch-text:after {
        left: -2px;
        text-shadow: 2px 0 #00f7ff;
        animation: glitch-anim-2 3s infinite linear alternate-reverse;
    }
    
    @keyframes enhanced-glitch {
        0% { text-shadow: 0.05em 0 0 rgba(255, 0, 230, 0.75), -0.05em -0.025em 0 rgba(0, 247, 255, 0.75), -0.025em 0.05em 0 rgba(255, 255, 0, 0.75); }
        14% { text-shadow: 0.05em 0 0 rgba(255, 0, 230, 0.75), -0.05em -0.025em 0 rgba(0, 247, 255, 0.75), -0.025em 0.05em 0 rgba(255, 255, 0, 0.75); }
        15% { text-shadow: -0.05em -0.025em 0 rgba(255, 0, 230, 0.75), 0.025em 0.025em 0 rgba(0, 247, 255, 0.75), -0.05em -0.05em 0 rgba(255, 255, 0, 0.75); }
        49% { text-shadow: -0.05em -0.025em 0 rgba(255, 0, 230, 0.75), 0.025em 0.025em 0 rgba(0, 247, 255, 0.75), -0.05em -0.05em 0 rgba(255, 255, 0, 0.75); }
        50% { text-shadow: 0.025em 0.05em 0 rgba(255, 0, 230, 0.75), 0.05em 0 0 rgba(0, 247, 255, 0.75), 0 -0.05em 0 rgba(255, 255, 0, 0.75); }
        99% { text-shadow: 0.025em 0.05em 0 rgba(255, 0, 230, 0.75), 0.05em 0 0 rgba(0, 247, 255, 0.75), 0 -0.05em 0 rgba(255, 255, 0, 0.75); }
        100% { text-shadow: -0.025em 0 0 rgba(255, 0, 230, 0.75), -0.025em -0.025em 0 rgba(0, 247, 255, 0.75), -0.025em -0.05em 0 rgba(255, 255, 0, 0.75); }
    }
    
    @keyframes glitch-anim-1 {
        0% { clip-path: inset(20% 0 80% 0); }
        20% { clip-path: inset(60% 0 40% 0); }
        40% { clip-path: inset(40% 0 60% 0); }
        60% { clip-path: inset(80% 0 20% 0); }
        80% { clip-path: inset(10% 0 90% 0); }
        100% { clip-path: inset(30% 0 70% 0); }
    }
    
    @keyframes glitch-anim-2 {
        0% { clip-path: inset(10% 0 90% 0); }
        20% { clip-path: inset(30% 0 70% 0); }
        40% { clip-path: inset(50% 0 50% 0); }
        60% { clip-path: inset(70% 0 30% 0); }
        80% { clip-path: inset(90% 0 10% 0); }
        100% { clip-path: inset(5% 0 95% 0); }
    }
    
    /* Street art elements */
    .stSidebar {
        position: relative;
    }
    
    .stSidebar:before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='rgba(255,0,230,0.05)' fill-opacity='0.1' fill-rule='evenodd'/%3E%3C/svg%3E"),
                    url("data:image/svg+xml,%3Csvg width='52' height='26' viewBox='0 0 52 26' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%230ff7ff' fill-opacity='0.05'%3E%3Cpath d='M10 10c0-2.21-1.79-4-4-4-3.314 0-6-2.686-6-6h2c0 2.21 1.79 4 4 4 3.314 0 6 2.686 6 6 0 2.21 1.79 4 4 4 3.314 0 6 2.686 6 6 0 2.21 1.79 4 4 4v2c-3.314 0-6-2.686-6-6 0-2.21-1.79-4-4-4-3.314 0-6-2.686-6-6zm25.464-1.95l8.486 8.486-1.414 1.414-8.486-8.486 1.414-1.414z' /%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.3;
        z-index: -1;
    }
    
    /* Tab styling */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: rgba(0, 247, 255, 0.7) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 1px !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00f7ff !important;
        text-shadow: 0 0 5px rgba(0, 247, 255, 0.5);
        font-weight: 700 !important;
    }
    
    [data-testid="stTabsContent"] {
        background: rgba(10, 10, 10, 0.3);
        border: 1px solid;
        border-image: linear-gradient(135deg, rgba(0, 247, 255, 0.3), rgba(255, 0, 230, 0.3)) 1;
        padding: 1rem;
        border-radius: 0 5px 5px 5px;
    }
    
    /* Dripping paint effect for section dividers */
    hr {
        height: 6px;
        border: none;
        background-image: linear-gradient(90deg, 
            transparent 0%, rgba(0, 247, 255, 0.2) 20%, 
            rgba(0, 247, 255, 0.8) 50%,
            rgba(255, 0, 230, 0.8) 50%, 
            rgba(255, 0, 230, 0.2) 80%, transparent 100%);
        position: relative;
        overflow: visible;
    }
    
    hr:after {
        content: '';
        position: absolute;
        height: 15px;
        width: 100%;
        top: 6px;
        left: 0;
        background-image: 
            radial-gradient(circle at 20% 0, rgba(0, 247, 255, 0.8) 0, rgba(0, 247, 255, 0) 15px),
            radial-gradient(circle at 50% 0, rgba(255, 0, 230, 0.8) 0, rgba(255, 0, 230, 0) 15px),
            radial-gradient(circle at 80% 0, rgba(0, 247, 255, 0.8) 0, rgba(0, 247, 255, 0) 15px);
    }
    
    /* Error message styling */
    .stAlert {
        border-radius: 5px;
        border-left: 4px solid #ff3366 !important;
    }
    
    /* Success message styling */
    .stAlert[data-baseweb="notification"] {
        border-radius: 5px;
        border-left: 4px solid #00ff99 !important;
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

# Title with enhanced glitch effect
st.markdown("<h1 class='glitch-text' data-text='🧠 Marvin&#39;s Neural Archive'>🧠 Marvin's Neural Archive</h1>", unsafe_allow_html=True)

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
tab1, tab2, tab3, tab4 = st.tabs(["Memory Stream", "Search", "Research", "Analytics"])

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
    st.markdown("### Research Assistant")
    
    # Research settings
    try:
        settings = asyncio.run(api.get_research_settings())
        auto_approve_default = settings.get("auto_approve", False)
    except Exception:
        auto_approve_default = False
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        research_query = st.text_area("Research Question", height=100, 
                                      placeholder="Enter a research question for Perplexity to answer...")
    
    with col2:
        st.markdown("### Settings")
        auto_approve = st.toggle("Auto-Approve Insights", value=auto_approve_default, 
                                help="Automatically store insights without review")
    
    if st.button("Conduct Research", type="primary"):
        if not research_query:
            st.error("Please enter a research question")
        else:
            with st.spinner("Researching..."):
                try:
                    result = asyncio.run(api.conduct_research(
                        query=research_query,
                        auto_approve=auto_approve
                    ))
                    
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
    st.markdown("### Pending Research")
    
    try:
        pending = asyncio.run(api.get_pending_research())
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
                    st.markdown(f"### Query: {research['query']}")
                    st.markdown(f"*Timestamp: {research['timestamp']}*")
                    
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
                                    st.markdown(f"""
                                        <div class='memory-card'>
                                            <p>{insight['content']}</p>
                                            <p><small>Confidence: {insight['confidence']:.2f} | Tags: {', '.join(insight['tags'])}</small></p>
                                        </div>
                                    """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Approve Selected", key=f"approve_{query_id}"):
                                if not selected_insights:
                                    st.error("No insights selected")
                                else:
                                    with st.spinner("Storing insights..."):
                                        try:
                                            result = asyncio.run(api.approve_insights(
                                                query_id=query_id,
                                                insight_indices=selected_insights
                                            ))
                                            
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
                                    asyncio.run(api.reject_research(query_id))
                                    st.success("Research rejected")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error rejecting research: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading pending research: {str(e)}")

with tab4:
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
