from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"
CACHE_DIR = DOCS_DIR / "cache"
INDEX_DIR = DATA_DIR / "index"
INDEX_PATH = INDEX_DIR / "index.faiss"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
CHUNKS_PATH = INDEX_DIR / "chunks.pkl"
DB_PATH = DATA_DIR / "db.sqlite"
MODEL_PATH = PROJECT_ROOT / "model" / "model.gguf"
MODEL_DIR = PROJECT_ROOT / "model"

EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 4

RECOMMENDED_MODEL = "Qwen2.5-1.5B-Instruct GGUF (Q4_K_M)"

# Inference settings.
# These defaults target a modern PC or an Orange Pi 5 with 4 GB+ RAM.
# For a Raspberry Pi 3/4 or other constrained device, reduce
# LLM_N_CTX to 1024, LLM_MAX_TOKENS to 180, and LLM_N_THREADS to 2.
LLM_N_CTX = 2048
LLM_N_THREADS = 4
LLM_N_BATCH = 256
LLM_MAX_TOKENS = 512
LLM_TEMPERATURE = 0.2
LLM_USE_MMAP = True
LLM_USE_MLOCK = False
LLM_N_GPU_LAYERS = 0

def ensure_runtime_directories():
	for path in (DATA_DIR, DOCS_DIR, CACHE_DIR, INDEX_DIR, MODEL_DIR):
		path.mkdir(parents=True, exist_ok=True)

ensure_runtime_directories()

SYSTEM_PROMPT = """You are Project Ampule, an offline survival assistant.

Rules:
- Give clear, practical, step-by-step instructions
- If unsure, say you are unsure
- Prioritize safety and conservative guidance
- Do not hallucinate unknown facts
"""
