import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext

try:
    from .llm import LocalLLM
    from .rag import Retriever
except ImportError:
    from llm import LocalLLM
    from rag import Retriever

class ProjectAmpuleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Ampule")
        self.root.geometry("900x650")

        self.status_var = tk.StringVar(value="Initializing Project Ampule...")

        self.question_label = tk.Label(root, text="Ask an offline survival question:")
        self.question_label.pack(anchor="w", padx=12, pady=(12, 4))

        self.question_entry = tk.Entry(root)
        self.question_entry.pack(fill="x", padx=12)
        self.question_entry.bind("<Return>", self.on_submit)

        self.submit_button = tk.Button(root, text="Submit", command=self.on_submit)
        self.submit_button.pack(anchor="e", padx=12, pady=8)

        self.output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED)
        self.output_area.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.status_label = tk.Label(root, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill="x", padx=12, pady=(0, 12))

        self.retriever = None
        self.llm = None
        self._initialize_runtime()

    def _append_output(self, text):
        self.output_area.configure(state=tk.NORMAL)
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.see(tk.END)
        self.output_area.configure(state=tk.DISABLED)

    def _initialize_runtime(self):
        self.submit_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._load_runtime, daemon=True).start()

    def _load_runtime(self):
        try:
            retriever = Retriever()
            llm = LocalLLM()
        except (FileNotFoundError, RuntimeError) as exc:
            self.root.after(0, self._on_load_error, str(exc))
            return
        self.root.after(0, self._on_load_success, retriever, llm)

    def _on_load_error(self, message):
        self.status_var.set("Setup required before GUI can answer questions.")
        self._append_output(f"Setup error: {message}")
        self._append_output("Run `python ingest_online.py` and `python ingest.py`, then restart the GUI.")

    def _on_load_success(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self.status_var.set("Ready. Project Ampule is running fully offline.")
        self.submit_button.configure(state=tk.NORMAL)

    def on_submit(self, event=None):
        if self.retriever is None or self.llm is None:
            messagebox.showwarning("Project Ampule", "Finish setup before asking questions.")
            return

        query = self.question_entry.get().strip()
        if not query:
            return

        self.question_entry.delete(0, tk.END)
        self.submit_button.configure(state=tk.DISABLED)
        self.status_var.set("Generating response...")
        self._append_output(f">> {query}")

        worker = threading.Thread(target=self._run_query, args=(query,), daemon=True)
        worker.start()

    def _run_query(self, query):
        try:
            docs = self.retriever.retrieve(query)
            answer = self.llm.generate(query, docs)
        except Exception as exc:
            self.root.after(0, self._handle_result, f"Error: {exc}", True)
            return

        self.root.after(0, self._handle_result, answer, False)

    def _handle_result(self, result_text, is_error):
        prefix = "Project Ampule error:" if is_error else "Project Ampule:"
        self._append_output(f"{prefix}\n{result_text}\n")
        self.status_var.set("Ready. Project Ampule is running fully offline.")
        self.submit_button.configure(state=tk.NORMAL)

def main():
    root = tk.Tk()
    ProjectAmpuleGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()