"""
Entry point for the project. We use uvicorn web server to run the FastAPI app defined in src/api.py.

API docs auto-generated at: http://localhost:8000/docs
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
