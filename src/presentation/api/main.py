from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .startup import init_app
from fastapi import Request
from fastapi.responses import JSONResponse


@app.exception_handler(FileNotFoundError)
def file_not_found_exception_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(ValueError)
def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    # Do not leak internal tracebacks in production; return generic message
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app = FastAPI(
    title="MoodBite API",
    description="Floorplan Detection & Recommendation Engine",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["predictions"])

# Initialize app state and startup wiring
init_app(app)

@app.get("/health")
def health_check():
    services = {}
    try:
        rs = getattr(app.state, "recommendation_service", None)
        services["recommendation_service"] = getattr(rs, "is_ready", False) if rs else False
        ds = getattr(app.state, "depth_estimation_service", None)
        services["depth_estimation_service"] = getattr(ds, "is_ready", False) if ds else False
        rds = getattr(app.state, "restaurant_details_service", None)
        services["restaurant_details_service"] = getattr(rds, "is_ready", False) if rds else False
    except Exception:
        services = {"error": "could not evaluate services"}

    return {"status": "ok", "services": services}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Đổi 8000 → 8001