"""
Entry point for the RAG API server
"""

import os
from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

import uvicorn

if __name__ == "__main__":
    # Print loaded env vars for debugging
    print(
        f"[Config] GEMINI_API_KEY: {'Set' if os.getenv('GEMINI_API_KEY') else 'Not Set'}"
    )
    print(f"[Config] MONGO_DB: {os.getenv('MONGO_DB', 'Not Set')}")

    uvicorn.run("core.apis.api:app", host="0.0.0.0", port=8000, reload=True)
