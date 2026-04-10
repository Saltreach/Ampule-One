# Project Ampule

Project Ampule is a spin-off of [Project NOMAD](https://github.com/Crosstalk-Solutions/project-nomad) by Crosstalk Solutions. Credit and thanks to the original project for the concept of an offline-first, local LLM survival assistant.

Project Ampule extends that foundation with a full RAG pipeline, curated knowledge ingestion from Wikipedia and Ready.gov, and tuned support for small ARM devices such as Orange Pi and Raspberry Pi. It runs locally as a CLI or Tkinter GUI app with no internet connection required at runtime.

## Recommended Model

Use Qwen2.5 1.5B Instruct in GGUF format with Q4_K_M quantization. Place the file at model/model.gguf.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   If `python3 -m venv` fails, install the missing package with `sudo apt install python3-venv python3-pip`.

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   If `faiss-cpu` does not install on ARM, continue anyway. Project Ampule will use the built-in NumPy retrieval fallback.

3. Add your GGUF model to model/model.gguf.

4. Optional: add your own .txt files to data/docs. These will be imported into SQLite the next time you run the online ingestion step.

5. Sync online and local sources into the database:
   ```bash
   python ingest_online.py
   ```

6. Build the FAISS index:
   ```bash
   python ingest.py
   ```
   This also writes a NumPy embeddings cache so retrieval still works without FAISS.

7. Run the GUI:
   ```bash
   python gui.py
   ```

8. Run the CLI instead if you prefer:
   ```bash
   python main.py
   ```

9. Module-mode launchers also work:
   ```bash
   python -m app.gui
   python -m app.main
   python -m app.ingest_online
   python -m app.ingest
   ```

## What It Includes

- Local SQLite persistence with incremental updates
- Raw source caching under data/docs/cache
- Curated medical Wikipedia ingestion
- Survival and preparedness ingestion from Ready.gov pages
- NumPy cosine similarity fallback when `faiss-cpu` is unavailable
- Offline retrieval-augmented generation at runtime

## Device Notes

Project Ampule is optimized for small ARM devices such as Orange Pi and Raspberry Pi, but response speed still depends heavily on your GGUF model choice and available RAM.

## License

Copyright 2026 Saltreach. Licensed under the [Apache License, Version 2.0](LICENSE).

## Acknowledgements

Project Ampule is a spin-off of [Project NOMAD](https://github.com/Crosstalk-Solutions/project-nomad) by Crosstalk Solutions, which provided the original concept. See [NOTICE](NOTICE) for full attribution.
