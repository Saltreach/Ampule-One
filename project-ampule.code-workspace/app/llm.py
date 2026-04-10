from llama_cpp import Llama
try:
    from .config import (
        MODEL_PATH,
        RECOMMENDED_MODEL,
        SYSTEM_PROMPT,
        LLM_N_BATCH,
        LLM_N_CTX,
        LLM_N_GPU_LAYERS,
        LLM_N_THREADS,
        LLM_MAX_TOKENS,
        LLM_TEMPERATURE,
        LLM_USE_MLOCK,
        LLM_USE_MMAP,
    )
except ImportError:
    from config import (
        MODEL_PATH,
        RECOMMENDED_MODEL,
        SYSTEM_PROMPT,
        LLM_N_BATCH,
        LLM_N_CTX,
        LLM_N_GPU_LAYERS,
        LLM_N_THREADS,
        LLM_MAX_TOKENS,
        LLM_TEMPERATURE,
        LLM_USE_MLOCK,
        LLM_USE_MMAP,
    )

class LocalLLM:
    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PATH}. "
                f"Recommended model: {RECOMMENDED_MODEL}."
            )

        self.llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=LLM_N_CTX,
            n_threads=LLM_N_THREADS,
            n_batch=LLM_N_BATCH,
            n_gpu_layers=LLM_N_GPU_LAYERS,
            use_mmap=LLM_USE_MMAP,
            use_mlock=LLM_USE_MLOCK,
            verbose=False,
        )

    def generate(self, query, context_chunks):
        context = "\n\n".join(context_chunks)
        prompt = f"""{SYSTEM_PROMPT}

Context:
{context}

User question:
{query}

Answer:"""
        output = self.llm(
            prompt,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            stop=["User:"],
        )
        return output["choices"][0]["text"].strip()
