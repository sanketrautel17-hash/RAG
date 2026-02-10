# Architecture Decision Record (ADR)

## ADR-001: Initial Technology Stack & Architecture for RAG System

### 📅 Date
2026-02-10

### 🟢 Status
Accepted

### 📝 Context
We need to build a Retrieval-Augmented Generation (RAG) system that allows users to upload various document types and query them using natural language. The system requires:
1.  Efficient handling of asynchronous I/O (file uploads, multiple users).
2.  Flexible data storage for unstructured document chunks and chat logs.
3.  A modern, responsive user interface.
4.  Cost-effective and high-performance LLM integration.

### 🏗️ Decision

We have decided to use the following stack:

#### 1. Backend: **FastAPI**
-   **Why**: FastAPI offers native async support (critical for LLM and DB IO-bound tasks), automatic Swagger documentation, and high performance compared to Flask/Django.
-   **Alternatives Considered**: Flask (too synchronous), Django (too heavy).

#### 2. Database: **MongoDB**
-   **Why**: Our data (parsed document chunks, chat history, metadata) is highly unstructured and variable. A NoSQL document store allows us to iterate on the schema without difficult migrations. The `motor` driver provides essential async capabilities.
-   **Alternatives Considered**: PostgreSQL with pgvector (good, but higher setup complexity for initial prototype), chromaDB (used for vectors, but we need a general store too).

#### 3. LLM Provider: **Google Gemini**
-   **Model**: `gemini-2.5-flash`
-   **Why**: Provides a massive context window (1M+ tokens) and high speed at a fraction of the cost of GPT-4. Essential for processing large retrieved chunks effectively.
-   **Integration**: Direct via `google-generativeai` SDK.

#### 4. Frontend: **React + Vite**
-   **Why**: React is the industry standard for dynamic UIs. Vite offers superior tailored build times compared to Create React App.
-   **State**: Local state + potential Context API for chat history.

#### 5. RAG Pipeline Strategy
-   **Ingestion**: Hybrid approach using `LlamaParse` for complex docs and standard loaders for text.
-   **Chunking**: Recursive character splitting to preserve context.
-   **Retrieval**: Semantic search (Embeddings) + potential Keyword search (Hybrid) in future iterations.

### 🔮 Consequences

#### Positive
-   **Velocity**: The "JavaScript frontend + Python backend" split allows us to use the best libraries for AI (Python) and UI (JS).
-   **Scalability**: Async Python backend handles concurrent chat requests well.
-   **Development Experience**: Hot-reloading on both ends (Uvicorn + Vite) speeds up the loop.

#### Negative
-   **Complexity**: Maintaining two separate deployment pipelines (Frontend vs Backend).
-   **Type Safety**: Connecting TypeScript frontend to Python backend requires manual type syncing (unless we use tools like openapi-typescript-codegen).

### 🔍 Future Considerations
-   Adding a dedicated Vector Database (e.g., Qdrant or converting MongoDB to use Atlas Vector Search) if local vector limitations are reached.
-   Implementing a queue system (Celery/Redis) for processing very large document uploads.
