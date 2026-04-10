import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss  # type: ignore
    HAS_FAISS = True
except ImportError:
    faiss = None
    HAS_FAISS = False

try:
    from .config import CHUNKS_PATH, EMBEDDINGS_PATH, EMBED_MODEL, INDEX_PATH, TOP_K
except ImportError:
    from config import CHUNKS_PATH, EMBEDDINGS_PATH, EMBED_MODEL, INDEX_PATH, TOP_K

def _normalize_rows(matrix):
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return matrix / norms

class Retriever:
    def __init__(self):
        if not CHUNKS_PATH.exists():
            raise FileNotFoundError(
                "Search metadata not found. Run `python ingest_online.py` "
                "and `python ingest.py` from the project root first."
            )

        self.embedder = SentenceTransformer(EMBED_MODEL)
        with open(CHUNKS_PATH, "rb") as f:
            self.chunks = pickle.load(f)

        self.use_faiss = HAS_FAISS and INDEX_PATH.exists()
        if self.use_faiss:
            self.index = faiss.read_index(str(INDEX_PATH))
            self.embeddings = None
        else:
            if not EMBEDDINGS_PATH.exists():
                raise FileNotFoundError(
                    "Search embeddings not found. Run `python ingest.py` from the project root first."
                )
            self.index = None
            self.embeddings = _normalize_rows(np.load(EMBEDDINGS_PATH))

    def retrieve(self, query):
        q_emb = self.embedder.encode([query]).astype("float32")
        if self.use_faiss:
            _, indices = self.index.search(q_emb, TOP_K)
        else:
            normalized_query = _normalize_rows(q_emb)
            scores = self.embeddings @ normalized_query[0]
            top_indices = np.argsort(scores)[-TOP_K:][::-1]
            indices = np.array([top_indices], dtype=int)

        results = [
            self.chunks[index]
            for index in indices[0]
            if 0 <= index < len(self.chunks)
        ]
        return results
