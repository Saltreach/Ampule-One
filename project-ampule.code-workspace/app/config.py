from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data"
DOCS_DIR     = DATA_DIR / "docs"
CACHE_DIR    = DOCS_DIR / "cache"
INDEX_DIR    = DATA_DIR / "index"
INDEX_PATH   = INDEX_DIR / "index.faiss"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
CHUNKS_PATH  = INDEX_DIR / "chunks.pkl"
DB_PATH      = DATA_DIR / "db.sqlite"
MODEL_DIR    = PROJECT_ROOT / "model"

EMBED_MODEL   = "all-MiniLM-L6-v2"
CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50
TOP_K         = 4

# Fixed inference knobs (not tier-specific)
LLM_TEMPERATURE  = 0.2
LLM_USE_MMAP     = True
LLM_USE_MLOCK    = False
LLM_N_GPU_LAYERS = 0

# ── Model tiers ────────────────────────────────────────────────────────────────
# Ordered highest → lowest.  Each entry names the GGUF file expected in
# model/ and carries matching inference parameters for that size class.
# The first tier whose min_ram_gb ≤ detected RAM *and* whose GGUF is
# present on disk is selected automatically at start-up.
_MODEL_TIERS = [
    {
        "min_ram_gb":  32,
        "model_file":  "qwen2.5-32b-instruct-q4_k_m.gguf",
        "recommended": "Qwen2.5-32B-Instruct (Q4_K_M)",
        "label":       "Overkill — 32 B",
        "n_ctx":       8192,
        "n_threads":   8,
        "n_batch":     512,
        "max_tokens":  2048,
    },
    {
        "min_ram_gb":  16,
        "model_file":  "qwen2.5-14b-instruct-q4_k_m.gguf",
        "recommended": "Qwen2.5-14B-Instruct (Q4_K_M)",
        "label":       "High — 14 B",
        "n_ctx":       6144,
        "n_threads":   8,
        "n_batch":     512,
        "max_tokens":  1536,
    },
    {
        "min_ram_gb":  12,
        "model_file":  "qwen2.5-7b-instruct-q8_0.gguf",
        "recommended": "Qwen2.5-7B-Instruct (Q8_0)",
        "label":       "Mid-High — 7 B Q8",
        "n_ctx":       4096,
        "n_threads":   6,
        "n_batch":     512,
        "max_tokens":  1024,
    },
    {
        "min_ram_gb":  8,
        "model_file":  "qwen2.5-7b-instruct-q4_k_m.gguf",
        "recommended": "Qwen2.5-7B-Instruct (Q4_K_M)",
        "label":       "Mid — 7 B",
        "n_ctx":       4096,
        "n_threads":   6,
        "n_batch":     512,
        "max_tokens":  1024,
    },
    # Ternary Bonsai 8B uses ~1.58-bit weights (~2 GB model size) so an 8B
    # architecture fits into 6 GB — preferred over standard 3B when present.
    # Expected filename: ternary-bonsai-8b.gguf  (verify against your download)
    {
        "min_ram_gb":  6,
        "model_file":  "ternary-bonsai-8b.gguf",
        "recommended": "Ternary Bonsai 8B (1.58-bit)",
        "label":       "Low-Mid — Bonsai 8B ternary",
        "n_ctx":       4096,
        "n_threads":   6,
        "n_batch":     512,
        "max_tokens":  1024,
    },
    {
        "min_ram_gb":  6,
        "model_file":  "qwen2.5-3b-instruct-q4_k_m.gguf",
        "recommended": "Qwen2.5-3B-Instruct (Q4_K_M)",
        "label":       "Low-Mid — 3 B",
        "n_ctx":       2048,
        "n_threads":   4,
        "n_batch":     256,
        "max_tokens":  512,
    },
    {
        "min_ram_gb":  4,
        "model_file":  "qwen3-1.7b-q4_k_m.gguf",
        "recommended": "Qwen3-1.7B (Q4_K_M)",
        "label":       "Low — 1.7 B",
        "n_ctx":       2048,
        "n_threads":   4,
        "n_batch":     256,
        "max_tokens":  512,
    },
    {
        "min_ram_gb":  0,
        "model_file":  "qwen3-0.6b-q4_k_m.gguf",
        "recommended": "Qwen3-0.6B (Q4_K_M)",
        "label":       "Floor — 0.6 B",
        "n_ctx":       1024,
        "n_threads":   2,
        "n_batch":     128,
        "max_tokens":  256,
    },
]


def _get_ram_gb():
    """Return total system RAM in gigabytes, cross-platform best-effort."""
    # 1. psutil — most reliable when installed
    try:
        import psutil
        return psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        pass

    # 2. /proc/meminfo — Linux / Android
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / (1024 ** 2)
    except OSError:
        pass

    # 3. sysctl hw.memsize — macOS / BSD
    try:
        import subprocess
        out = subprocess.check_output(
            ["sysctl", "-n", "hw.memsize"], stderr=subprocess.DEVNULL
        )
        return int(out.strip()) / (1024 ** 3)
    except Exception:
        pass

    # 4. GlobalMemoryStatusEx — Windows
    try:
        import ctypes

        class _MEMSTATUS(ctypes.Structure):
            _fields_ = [
                ("dwLength",                ctypes.c_ulong),
                ("dwMemoryLoad",            ctypes.c_ulong),
                ("ullTotalPhys",            ctypes.c_ulonglong),
                ("ullAvailPhys",            ctypes.c_ulonglong),
                ("ullTotalPageFile",        ctypes.c_ulonglong),
                ("ullAvailPageFile",        ctypes.c_ulonglong),
                ("ullTotalVirtual",         ctypes.c_ulonglong),
                ("ullAvailVirtual",         ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        ms = _MEMSTATUS()
        ms.dwLength = ctypes.sizeof(ms)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
        return ms.ullTotalPhys / (1024 ** 3)
    except Exception:
        pass

    # 5. Conservative fallback — assume a constrained device
    return 4.0


def _select_tier(ram_gb, model_dir):
    """
    Pick the best model tier for the detected RAM.

    Walk tiers from highest to lowest; return the first whose GGUF file
    exists on disk and is non-empty.  If no file matches, return the
    highest eligible tier so the GUI can show the user what to download.
    """
    eligible = [t for t in _MODEL_TIERS if t["min_ram_gb"] <= ram_gb]
    if not eligible:
        eligible = [_MODEL_TIERS[-1]]   # floor — handle < 2 GB edge case

    for tier in eligible:
        path = model_dir / tier["model_file"]
        if path.exists() and path.stat().st_size > 0:
            return tier

    # No model file present yet — return best eligible as the download target
    return eligible[0]


# ── Resolved at import time ────────────────────────────────────────────────────
SYSTEM_RAM_GB = _get_ram_gb()
_TIER = _select_tier(SYSTEM_RAM_GB, MODEL_DIR)

MODEL_PATH        = MODEL_DIR / _TIER["model_file"]
RECOMMENDED_MODEL = _TIER["recommended"]
MODEL_LABEL       = _TIER["label"]

LLM_N_CTX     = _TIER["n_ctx"]
LLM_N_THREADS = _TIER["n_threads"]
LLM_N_BATCH   = _TIER["n_batch"]
LLM_MAX_TOKENS = _TIER["max_tokens"]


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
