"""Điểm vào cho server (Procfile: uvicorn app:app).

Chạy local:  uvicorn app:app --reload --port 8001
Swagger UI:  http://localhost:8001/docs
"""
from src.presentation.api.main import create_app

app = create_app()

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
