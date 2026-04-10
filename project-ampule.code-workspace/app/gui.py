import threading
import tkinter as tk
import tkinter.font as tkfont

try:
    from .llm import LocalLLM
    from .rag import Retriever
except ImportError:
    from llm import LocalLLM
    from rag import Retriever

# ── Palette (Anthropic-inspired dark theme) ───────────────────────────────────
BG         = "#1a1a1a"   # root / chat canvas
BG_RAISED  = "#212121"   # header and input bar
BG_ENTRY   = "#2c2c2c"   # text entry field
BORDER     = "#333333"   # dividers and entry outline
ACCENT     = "#da7756"   # Anthropic terracotta
ACCENT_HOV = "#bf6548"   # button hover / active
TEXT       = "#f0ebe4"   # primary warm white
TEXT_DIM   = "#6b6660"   # muted secondary text
TEXT_USER  = "#c5c0b9"   # user message body
DOT_IDLE   = "#4a4540"   # loading / unknown
DOT_READY  = "#5a9e6a"   # ready (green)
DOT_BUSY   = "#d49a55"   # generating (amber)


def _bind_hover(widget, fg_out, fg_in):
    widget.bind("<Enter>", lambda e: widget.configure(fg=fg_in))
    widget.bind("<Leave>", lambda e: widget.configure(fg=fg_out))


class ProjectAmpuleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Ampule")
        self.root.geometry("920x700")
        self.root.configure(bg=BG)
        self.root.minsize(640, 480)

        # Best available sans-serif face for the platform
        families = tkfont.families()
        self._face = next(
            (f for f in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu", "Helvetica")
             if f in families),
            "TkDefaultFont",
        )

        self.retriever = None
        self.llm = None

        # Pack order matters: top → bottom → fill remaining middle
        self._build_header()
        self._build_input_bar()
        self._build_chat()

        self._initialize_runtime()

    # ── Font shorthand ────────────────────────────────────────────────────────
    def _f(self, size, *style):
        return (self._face, size, *style)

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_RAISED, height=56)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=BG_RAISED)
        left.pack(side="left", fill="y", padx=(20, 0))

        self._dot = tk.Label(left, text="●", fg=DOT_IDLE, bg=BG_RAISED,
                             font=self._f(9))
        self._dot.pack(side="left", padx=(0, 10))

        tk.Label(left, text="Project Ampule", fg=TEXT, bg=BG_RAISED,
                 font=self._f(13, "bold")).pack(side="left")

        clear = tk.Button(
            header, text="Clear", fg=TEXT_DIM, bg=BG_RAISED,
            activeforeground=TEXT, activebackground=BG_RAISED,
            relief="flat", bd=0, padx=4, cursor="hand2",
            font=self._f(10), command=self._clear_chat,
        )
        clear.pack(side="right", padx=20)
        _bind_hover(clear, TEXT_DIM, TEXT)

        tk.Frame(self.root, bg=BORDER, height=1).pack(side="top", fill="x")

    def _build_input_bar(self):
        tk.Frame(self.root, bg=BORDER, height=1).pack(side="bottom", fill="x")

        bar = tk.Frame(self.root, bg=BG_RAISED, padx=24, pady=16)
        bar.pack(side="bottom", fill="x")

        # Status line
        self._status_var = tk.StringVar(value="Loading model…")
        tk.Label(bar, textvariable=self._status_var, fg=TEXT_DIM, bg=BG_RAISED,
                 font=self._f(9), anchor="w").pack(fill="x", pady=(0, 10))

        # Input row: entry + send button
        row = tk.Frame(bar, bg=BG_RAISED)
        row.pack(fill="x")

        # Entry with a focus-ring border effect via a wrapper frame
        self._entry_wrap = tk.Frame(
            row, bg=BG_ENTRY,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        self._entry_wrap.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.question_entry = tk.Entry(
            self._entry_wrap, bg=BG_ENTRY, fg=TEXT,
            insertbackground=ACCENT,
            relief="flat", bd=0,
            font=self._f(11),
        )
        self.question_entry.pack(fill="x", padx=16, ipady=11)
        self.question_entry.bind("<Return>", self.on_submit)
        self.question_entry.bind(
            "<FocusIn>",
            lambda e: self._entry_wrap.configure(highlightbackground=ACCENT))
        self.question_entry.bind(
            "<FocusOut>",
            lambda e: self._entry_wrap.configure(highlightbackground=BORDER))

        self.submit_button = tk.Button(
            row, text="Send", fg=BG, bg=ACCENT,
            activeforeground=BG, activebackground=ACCENT_HOV,
            relief="flat", bd=0,
            padx=24, pady=11,
            cursor="hand2",
            font=self._f(11, "bold"),
            command=self.on_submit,
        )
        self.submit_button.pack(side="right")

    def _build_chat(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        sb = tk.Scrollbar(
            frame, orient="vertical",
            bg=BG, troughcolor=BG,
            activebackground="#3a3a3a",
            relief="flat", bd=0, width=6,
        )
        sb.pack(side="right", fill="y", padx=(0, 2), pady=4)

        self.chat = tk.Text(
            frame, bg=BG, fg=TEXT,
            relief="flat", bd=0,
            wrap=tk.WORD,
            state=tk.DISABLED,
            cursor="arrow",
            padx=56, pady=28,
            spacing1=0, spacing2=3, spacing3=0,
            font=self._f(11),
            yscrollcommand=sb.set,
        )
        sb.configure(command=self.chat.yview)
        self.chat.pack(side="left", fill="both", expand=True)

        # Speaker labels — small, bold, terracotta
        self.chat.tag_configure(
            "speaker_you", foreground=ACCENT,
            font=self._f(9, "bold"), spacing1=24, spacing3=5)
        self.chat.tag_configure(
            "speaker_amp", foreground=ACCENT,
            font=self._f(9, "bold"), spacing1=14, spacing3=5)

        # Message bodies
        self.chat.tag_configure(
            "msg_user", foreground=TEXT_USER,
            font=self._f(11), spacing3=4)
        self.chat.tag_configure(
            "msg_amp", foreground=TEXT,
            font=self._f(11), spacing3=4)

        # System / error messages
        self.chat.tag_configure(
            "msg_system", foreground=TEXT_DIM,
            font=self._f(10, "italic"), spacing1=6, spacing3=6)

        # Exchange divider
        self.chat.tag_configure(
            "divider", foreground="#272727",
            font=self._f(5), spacing1=20, spacing3=4)

    # ── Chat helpers ──────────────────────────────────────────────────────────
    def _chat_write(self, *pairs):
        """Insert (text, tag) pairs into the chat widget."""
        self.chat.configure(state=tk.NORMAL)
        for text, tag in pairs:
            self.chat.insert(tk.END, text, tag)
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)

    def _add_question(self, query):
        self._chat_write(
            ("YOU\n",          "speaker_you"),
            (query + "\n",     "msg_user"),
        )

    def _add_answer(self, answer, is_error=False):
        tag = "msg_system" if is_error else "msg_amp"
        self._chat_write(
            ("PROJECT AMPULE\n",    "speaker_amp"),
            (answer + "\n",        tag),
            ("─" * 64 + "\n",      "divider"),
        )

    def _clear_chat(self):
        self.chat.configure(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.configure(state=tk.DISABLED)

    # ── Status helpers ────────────────────────────────────────────────────────
    def _set_status(self, text, dot=DOT_IDLE):
        self._status_var.set(text)
        self._dot.configure(fg=dot)

    # ── Runtime initialization ────────────────────────────────────────────────
    def _initialize_runtime(self):
        self.submit_button.configure(state=tk.DISABLED)
        self._set_status("Loading model…", DOT_IDLE)
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
        self._set_status("Setup required — see below for details.", DOT_IDLE)
        self._chat_write(
            (f"Setup error: {message}\n",                                  "msg_system"),
            ("Run `python ingest_online.py` and `python ingest.py`,"
             " then restart.\n",                                           "msg_system"),
        )

    def _on_load_success(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self._set_status("Ready — running fully offline", DOT_READY)
        self.submit_button.configure(state=tk.NORMAL)
        self.question_entry.focus_set()

    # ── Query ─────────────────────────────────────────────────────────────────
    def on_submit(self, event=None):
        if self.retriever is None or self.llm is None:
            return

        query = self.question_entry.get().strip()
        if not query:
            return

        self.question_entry.delete(0, tk.END)
        self.submit_button.configure(state=tk.DISABLED)
        self._set_status("Generating response…", DOT_BUSY)
        self._add_question(query)

        threading.Thread(
            target=self._run_query, args=(query,), daemon=True
        ).start()

    def _run_query(self, query):
        try:
            docs = self.retriever.retrieve(query)
            answer = self.llm.generate(query, docs)
        except Exception as exc:
            self.root.after(0, self._handle_result, f"Error: {exc}", True)
            return
        self.root.after(0, self._handle_result, answer, False)

    def _handle_result(self, answer, is_error):
        self._add_answer(answer, is_error)
        self._set_status("Ready — running fully offline", DOT_READY)
        self.submit_button.configure(state=tk.NORMAL)
        self.question_entry.focus_set()


def main():
    root = tk.Tk()
    ProjectAmpuleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
