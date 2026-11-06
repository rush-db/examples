"""
Configuration settings for the fine-tuning tutorial.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# RushDB Configuration
RUSHDB_API_KEY = os.getenv("RUSHDB_API_KEY")
RUSHDB_URL = os.getenv("RUSHDB_URL", "https://api.rushdb.com/api/v1")

# Embedding Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight model for fast demo
EMBEDDING_DIMENSIONS = 384

# Fine-tuning Configuration
FINE_TUNE_EPOCHS = 5
FINE_TUNE_LR = 2e-5
CONTRASTIVE_TEMPERATURE = 0.07
BATCH_SIZE = 16

# Graph Configuration
GRAPH_DATA = {
    "num_papers": 50,
    "num_authors": 20,
    "num_topics": 10,
    "avg_citations_per_paper": 3,
}

# Vector Index Configuration
VECTOR_INDEX_LABEL = "PAPER"
VECTOR_INDEX_PROPERTY = "abstract"
VECTOR_INDEX_SOURCE = "external"  # We provide pre-computed vectors
