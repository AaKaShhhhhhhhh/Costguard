import os
import logging
import traceback
from fastapi import FastAPI, Depends, HTTPException, Security, status, Request
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from backend.api.v1.routes import router as v1_router

app = FastAPI(
    title="CostGuard API",
    description="Backend API for CostGuard cost monitoring and optimization.",
    version="1.0.0"
)

logger = logging.getLogger("backend")
logging.basicConfig(level=logging.INFO)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Global error: %s", exc)
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )

# --- Authentication ---

API_KEY = os.getenv("API_KEY", "default_secret_key")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True) # auto_error=True makes Swagger UI mandatory

async def get_api_key(
    header_api_key: str = Security(api_key_header)
):
    if header_api_key == API_KEY:
        return header_api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )

# --- Routing ---

# Include v1 router with global auth dependency
app.include_router(v1_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Welcome to CostGuard API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
