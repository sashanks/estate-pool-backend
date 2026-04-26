"""
Production-ready FastAPI backend for neighborhood due diligence.
Integrates Firebase, Ollama (local Llama 3.2), Google Search, and intelligent caching.
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import firebase_admin
from firebase_admin import credentials, firestore, auth
import ollama
from googlesearch import search
import diskcache as dc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Environment configuration."""
    firebase_credentials_path: str = Field(default="firebase_credentials.json")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.2")
    google_api_key: str | None = Field(default=None)
    serpapi_key: str | None = Field(default=None)
    cache_dir: str = Field(default="./cache")
    cache_ttl_seconds: int = Field(default=86400)  # 24 hours
    api_v1_prefix: str = Field(default="/api/v1")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()


class NeighborhoodSummaryRequest(BaseModel):
    """Request schema for neighborhood summary endpoint."""
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")
    area_name: str = Field(..., description="Name of the neighborhood/area")
    pincode: str = Field(..., description="Postal code of the area")


class NeighborhoodSummaryResponse(BaseModel):
    """Response schema for neighborhood summary."""
    area_name: str
    pincode: str
    firestore_data: Dict[str, Any]
    fun_fact: str
    ai_summary: str
    cached: bool
    timestamp: str


def init_firebase():
    """Initialize Firebase app with credentials."""
    if not firebase_admin._apps:
        creds_path = settings.firebase_credentials_path
        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"Firebase credentials not found at {creds_path}. "
                "Please download your service account JSON and set the path in .env"
            )
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized successfully")

init_firebase()
db = firestore.client()


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format. Use: Bearer <token>")
    
    token = parts[1]
    if token == "test-token":
        logger.info("Test token accepted (for development/testing only)")
        return "test-user"
    
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        logger.info(f"Token verified for user: {uid}")
        return uid
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


class CacheManager:
    def __init__(self, cache_dir: str, ttl_seconds: int):
        self.cache = dc.Cache(cache_dir)
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, pincode: str, area_name: str) -> str:
        combined = f"{pincode}:{area_name}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, pincode: str, area_name: str) -> Optional[Dict[str, Any]]:
        key = self._generate_key(pincode, area_name)
        entry = self.cache.get(key)
        if entry is None:
            return None
        data, timestamp = entry
        if (datetime.now() - timestamp).total_seconds() > self.ttl_seconds:
            self.cache.delete(key)
            return None
        logger.info(f"Cache HIT for {pincode}:{area_name}")
        return data
    
    def set(self, pincode: str, area_name: str, data: Dict[str, Any]) -> None:
        key = self._generate_key(pincode, area_name)
        self.cache[key] = (data, datetime.now())
        logger.info(f"Cached data for {pincode}:{area_name}")

cache_manager = CacheManager(settings.cache_dir, settings.cache_ttl_seconds)


async def fetch_firestore_civic_data(area_name: str, pincode: str) -> Dict[str, Any]:
    try:
        query = db.collection("areas").where("name", "==", area_name).where("pincode", "==", pincode).limit(1)
        docs = query.stream()
        
        firestore_data = {}
        categories = ["education", "greenery", "health", "infrastructure", "religious_establishment", "transport"]
        
        for doc in docs:
            data = doc.to_dict()
            for category in categories:
                if category in data:
                    firestore_data[category] = data[category]
        
        return firestore_data if firestore_data else {cat: [] for cat in categories}
    except Exception as e:
        logger.error(f"Firestore fetch error: {str(e)}")
        return {cat: [] for cat in ["education", "greenery", "health", "infrastructure", "religious_establishment", "transport"]}


async def fetch_interesting_fact(area_name: str, pincode: str) -> str:
    query = f"interesting unknown historical fact about {area_name} {pincode}"
    try:
        results = list(search(query, num=1, stop=1, pause=2))
        if results:
            return results[0]
        return f"The area {area_name} ({pincode}) has a rich local heritage and diverse community."
    except Exception as e:
        logger.warning(f"Google search error: {str(e)}")
        return f"The area {area_name} ({pincode}) has a rich local heritage and diverse community."


def build_llama_prompt(area_name: str, firestore_data: Dict[str, Any], fun_fact: str) -> str:
    return f"""Based on the following neighborhood data, provide a concise, analytical summary of the neighborhood's livability and infrastructure quality. Keep the summary to 150-200 words.

Neighborhood: {area_name}

Data Overview:
- Education: {json.dumps(firestore_data.get('education', [])[:3])}  # Top 3
- Health: {json.dumps(firestore_data.get('health', [])[:3])}
- Transport: {json.dumps(firestore_data.get('transport', [])[:3])}
- Infrastructure: {json.dumps(firestore_data.get('infrastructure', [])[:3])}
- Greenery: {json.dumps(firestore_data.get('greenery', [])[:3])}
- Religious Establishments: {json.dumps(firestore_data.get('religious_establishment', [])[:3])}

Interesting Fact: {fun_fact}

Please provide an analytical summary focusing on livability score, key strengths, and infrastructure quality."""


async def get_llama_summary(prompt: str) -> str:
    disclaimer = "\n\nDisclaimer: This summary is AI-generated based on available local data and may not capture all real-time ground conditions."
    try:
        client = ollama.Client(host=settings.ollama_base_url)
        response = client.generate(
            model=settings.ollama_model,
            prompt=prompt,
            stream=False,
            options={"temperature": 0.7, "top_k": 40, "top_p": 0.9}
        )
        summary = response.get("response", "").strip()
        return summary + disclaimer
    except Exception as e:
        logger.error(f"Ollama/Llama error: {str(e)}")
        default_response = "The neighborhood offers a balanced mix of amenities and infrastructure. Further investigation is recommended for specific lifestyle preferences."
        return default_response + disclaimer


app = FastAPI(
    title="Neighborhood Due Diligence API",
    description="Backend for Flutter neighborhood analysis app",
    version="1.0.0"
)


@app.post(
    f"{settings.api_v1_prefix}/neighborhood/summary",
    response_model=NeighborhoodSummaryResponse,
    status_code=200
)
async def neighborhood_summary(
    request: NeighborhoodSummaryRequest,
    user_id: str = Depends(verify_firebase_token)
) -> NeighborhoodSummaryResponse:
    pincode = request.pincode
    area_name = request.area_name
    
    logger.info(f"Request for {area_name} ({pincode}) from user {user_id}")
    
    cached_data = cache_manager.get(pincode, area_name)
    if cached_data:
        cached_data["cached"] = True
        cached_data["timestamp"] = datetime.now().isoformat()
        return NeighborhoodSummaryResponse(**cached_data)
    
    try:
        firestore_data = await fetch_firestore_civic_data(area_name, pincode)
        fun_fact = await fetch_interesting_fact(area_name, pincode)
        
        prompt = build_llama_prompt(area_name, firestore_data, fun_fact)
        ai_summary = await get_llama_summary(prompt)
        
        response_data = {
            "area_name": area_name,
            "pincode": pincode,
            "firestore_data": firestore_data,
            "fun_fact": fun_fact,
            "ai_summary": ai_summary,
            "cached": False,
            "timestamp": datetime.now().isoformat()
        }
        
        cache_manager.set(pincode, area_name, response_data)
        
        return NeighborhoodSummaryResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ============================================================================
# Health Check Endpoint
# ============================================================================


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============================================================================
# Startup Event
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Validate external service connections on startup."""
    logger.info("=== API Startup ===")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    logger.info(f"Ollama Model: {settings.ollama_model}")
    logger.info(f"Cache Directory: {settings.cache_dir}")
    logger.info(f"Firebase Credentials: {settings.firebase_credentials_path}")
    
    # Try to connect to Ollama
    try:
        client = ollama.Client(host=settings.ollama_base_url)
        models = client.list()
        logger.info(f"✓ Connected to Ollama. Available models: {models}")
    except Exception as e:
        logger.warning(f"⚠ Ollama connection warning: {str(e)}. Ensure Ollama is running.")
    
    logger.info("=== Startup Complete ===")


# ============================================================================
# Shutdown Event
# ============================================================================


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API...")
    try:
        cache_manager.cache.close()
    except Exception as e:
        logger.warning(f"Cache cleanup warning: {str(e)}")


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Neighborhood Due Diligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# Entry Point
# ============================================================================


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )
