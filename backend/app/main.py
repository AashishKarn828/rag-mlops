"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.routes import router
from app.services.embedding import embedding_service
from app.services.llm import llm_service
from app.services.vectordb import vectordb_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="A production-grade RAG system with Qwen LLM and BGE embeddings"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    logger.info("=" * 50)
    logger.info("Starting RAG Microservice API")
    logger.info("=" * 50)
    
    # Load embedding model
    logger.info("Loading embedding model...")
    embedding_service.load_model()
    
    # Load LLM model
    logger.info("Loading LLM model...")
    llm_service.load_model()
    
    # Connect to Qdrant
    logger.info("Connecting to vector database...")
    vectordb_service.connect()
    
    logger.info("=" * 50)
    logger.info("Startup complete! All services ready.")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RAG Microservice API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)