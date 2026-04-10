import sqlite3
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
    from .config import (
        CHUNKS_PATH,
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        DB_PATH,
        EMBEDDINGS_PATH,
        EMBED_MODEL,
        INDEX_DIR,
        INDEX_PATH,
    )
except ImportError:
    from config import (
        CHUNKS_PATH,
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        DB_PATH,
        EMBEDDINGS_PATH,
        EMBED_MODEL,
        INDEX_DIR,
        INDEX_PATH,
    )

INDEX_DIR.mkdir(parents=True, exist_ok=True)

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start+size])
        start += size - overlap
    return chunks

def load_documents():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT content FROM documents")
    except sqlite3.OperationalError as exc:
        conn.close()
        raise RuntimeError(
            "Document database is not initialized. Run `python ingest_online.py` first."
        ) from exc

    docs = [row[0] for row in cur.fetchall() if row[0].strip()]
    conn.close()
    return docs

def main():
    model = SentenceTransformer(EMBED_MODEL)
    raw_docs = load_documents()
    if not raw_docs:
        print("No documents found. Add .txt files to data/docs or run `python ingest_online.py` first.")
        return

    chunks = []
    for doc in raw_docs:
        chunks.extend(chunk_text(doc))

    if not chunks:
        print("No text chunks were generated from the available documents.")
        return

    print(f"Total chunks: {len(chunks)}")
    embeddings = model.encode(chunks, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")
    np.save(EMBEDDINGS_PATH, embeddings)

    if HAS_FAISS:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        faiss.write_index(index, str(INDEX_PATH))
        print("Built FAISS index.")
    else:
        print("faiss-cpu is not available. Saved embeddings for NumPy cosine fallback.")

    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)
    print("Index built successfully.")

if __name__ == "__main__":
    main()
