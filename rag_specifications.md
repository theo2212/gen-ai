# MISSION SPECIFICATION : Legal RAG Pipeline (Engineer 2)

## 1. Context & Objective
You are acting as the lead data engineer for a Legal Agentics AI Proof of Concept. 
Your specific mission is to build a flawless, lightweight Retrieval-Augmented Generation (RAG) pipeline to ingest cleaned commercial leases (.txt files) and expose a retriever for the orchestrator.

## 2. Technical Stack (STRICT - DO NOT DEVIATE)
* **Language:** Python 3.10+
* **Framework:** LangChain (`langchain`, `langchain-community`, `langchain-openai`)
* **Embeddings:** OpenAI `text-embedding-3-small`
* **Vector Database:** ChromaDB (Local persistence only, NO cloud databases)

## 3. Core Requirements & Tasks

### Task 1: Data Ingestion
* Create a pipeline to load raw `.txt` files from a local directory (e.g., `./data/contracts/`).
* The data provided will be pre-cleaned. Do not build complex PDF parsers or OCR tools. Use LangChain's basic `TextLoader`.

### Task 2: Chunking Strategy (Crucial)
* Implement a `RecursiveCharacterTextSplitter`.
* **Parameters:** Set `chunk_size` to 1000 and `chunk_overlap` to 200.
* **Code Requirement:** You MUST include comprehensive inline comments explaining *why* these parameters were chosen (e.g., "Preserves legal clauses intact, overlap prevents losing context for numerical values like indexation rates"). This is required for our technical report.

### Task 3: Vectorization & Storage
* Embed the chunks using `text-embedding-3-small`.
* Initialize and persist a local ChromaDB instance (e.g., in `./chroma_db`).

### Task 4: Exposing the Retriever (The "Wow" Factor)
* Create a callable function `get_contract_retriever(contract_id)`.
* The retriever must not only return the embedded text but MUST guarantee that the `page_content` and metadata (source chunk ID/filename) are easily accessible. 
* This is mandatory so Engineer 1 (UI) can display the exact extracted quote side-by-side with the LLM JSON output.

## 4. Expected Deliverables
Write a clean, modular Python script (e.g., `rag_engine.py`) containing at least these two functions:
1.  `build_vector_db(data_directory: str)` -> Processes files and builds the local ChromaDB.
2.  `get_retriever()` -> Returns the LangChain retriever object configured to fetch the top 3 most relevant chunks (`k=3`).

## 5. Constraints
* Do not write any Streamlit UI code (that is Engineer 1's job).
* Do not write the LLM generation or tool-calling logic.
* Keep dependencies to an absolute minimum.