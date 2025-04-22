# 🧠 Marvin's Memory System

A neural memory system for Marvin, powered by Qdrant vector database and OpenAI embeddings.

## Features

- 🤖 Character-aligned memory storage
- 🔍 Semantic search capabilities
- 📊 Memory analytics and visualization
- 🎯 Automatic alignment scoring
- 🏷️ Tag-based organization

## Tech Stack

- FastAPI for backend API
- Streamlit for UI
- Qdrant for vector storage
- OpenAI for embeddings
- Docker for containerization

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/marvin-memory.git
cd marvin-memory
```

2. Create a `.env` file with your configuration:
```env
QDRANT_HOST=qdrant
QDRANT_PORT=6333
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

3. Run with Docker Compose:
```bash
docker-compose up -d
```

The services will be available at:
- FastAPI: http://localhost:8000
- Streamlit UI: http://localhost:8501
- Qdrant Dashboard: http://localhost:6333/dashboard

## Development

To run locally without Docker:

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the services:
```bash
# Terminal 1 - FastAPI
uvicorn src.api.main:app --reload

# Terminal 2 - Streamlit
streamlit run src/ui/streamlit_app.py
```

## Deployment

1. SSH into your server
2. Clone the repository
3. Create `.env` file with production settings
4. Run with Docker Compose:
```bash
docker-compose up -d
```

## License

MIT License 