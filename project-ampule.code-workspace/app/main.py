try:
    from .llm import LocalLLM
    from .rag import Retriever
except ImportError:
    from llm import LocalLLM
    from rag import Retriever

def run_cli():
    print("Initializing Project Ampule...")
    try:
        retriever = Retriever()
        llm = LocalLLM()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Setup error: {exc}")
        print("Run `python ingest_online.py` and `python ingest.py` from the project root, then try again.")
        return

    print("Ready. Type 'exit' to quit.\n")
    while True:
        query = input(">> ")
        if query.lower() in ["exit", "quit"]:
            break
        docs = retriever.retrieve(query)
        answer = llm.generate(query, docs)
        print("\n--- RESPONSE ---")
        print(answer)
        print("----------------\n")

def main():
    run_cli()

if __name__ == "__main__":
    main()
