"""
Entry point for the VGK Lineup Optimizer.

Run:  python main.py
Or for dev with auto-reload:  uvicorn src.api:app --reload --port 8000

API docs auto-generated at: http://localhost:8000/docs
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
