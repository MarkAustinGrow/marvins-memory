from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "172.236.2.45")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "marvin_memory"
VECTOR_SIZE = 1536  # OpenAI text-embedding-3-small dimension

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Marvin Configuration
MARVIN_ID = "af871ddd-febb-4454-9171-080450357b8c"

# Memory Configuration
MIN_ALIGNMENT_SCORE = 0.7
MEMORY_TYPES = ["tweet", "research", "thought", "output", "quote"] 