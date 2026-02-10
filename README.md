# RAG Project

A specialized Retrieval-Augmented Generation (RAG) application designed for intelligent document processing and querying. This project combines a high-performance FastAPI backend with a modern React frontend to allow users to ingest documents (PDF, Text, Web) and chat with them using Google's Gemini LLM.

## 🚀 Features

-   **Multi-Source Ingestion**: Support for uploading PDFs, plain text, and web scraping.
-   **Advanced RAG Pipeline**: Uses vector search to find relevant context before generating answers.
-   **Smart Caching & History**: Maintains conversation history for context-aware follow-up questions.
-   **Modern UI**: Clean, responsive interface built with React and Vite.
-   **Robust Backend**: Async FastAPI server with MongoDB persistence.

## 🛠️ Tech Stack

### Backend
-   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
-   **Server**: Uvicorn
-   **Database**: MongoDB (via `motor` async driver)
-   **LLM Service**: Google Gemini (`gemini-2.5-flash`)
-   **Embeddings**: Sentence Transformers / Google Generative AI
-   **Document Processing**: LlamaParse / Unstructured

### Frontend
-   **Framework**: [React](https://react.dev/)
-   **Build Tool**: [Vite](https://vitejs.dev/)
-   **Styling**: CSS Modules
-   **State Management**: React Hooks

## 📋 Prerequisites

-   Python 3.9+
-   Node.js 16+
-   MongoDB (Local or Atlas)
-   Google Gemini API Key

## ⚡ Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd rag_project
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 4. Environment Configuration
Create a `.env` file in the root directory:
```ini
GEMINI_API_KEY=your_api_key_here
MONGO_DB=mongodb://localhost:27017
DB_NAME=rag_db
```

## 🏃‍♂️ Running the Application

### Start the Backend
```bash
# From the root directory
python main.py
```
The API will be available at `http://localhost:8000`.
API Documentation: `http://localhost:8000/docs`.

### Start the Frontend
Open a new terminal:
```bash
cd frontend
npm run dev
```
The UI will be available at `http://localhost:5173` (or similar).

## 🧬 Architecture Overview

For a detailed breakdown of architectural decisions, see [ADR.md](./ADR.md).
