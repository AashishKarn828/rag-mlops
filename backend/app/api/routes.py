import logging
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import ChatRequest, ChatResponse, HealthResponse, IndexResponse
from app.services.document import document_service
from app.services.embedding import embedding_service
from app.services.llm import llm_service
from app.services.memory import session_memory_service
from app.services.vectordb import vectordb_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {"message": "RAG Microservice API is running", "status": "healthy"}


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    models_loaded = all(
        [
            embedding_service.is_loaded(),
            llm_service.is_loaded(),
            vectordb_service.is_connected(),
        ]
    )

    return HealthResponse(
        status="healthy" if models_loaded else "loading", models_loaded=models_loaded
    )


@router.post("/index", response_model=IndexResponse, tags=["Indexing"])
async def index_document(file: UploadFile = File(...)):
    """
    Index a document (PDF or TXT) into the vector database

    - **file**: PDF or TXT file to index
    """
    try:
        logger.info(f"Indexing file: {file.filename}")

        # Validate file type
        if not document_service.validate_file_type(file.filename):
            raise HTTPException(
                status_code=400, detail="Only PDF and TXT files are supported"
            )

        # Read file content
        content = await file.read()

        # Extract text based on file type
        if file.filename.endswith(".pdf"):
            text = document_service.extract_text_from_pdf(content)
        else:  # .txt
            text = document_service.extract_text_from_txt(content)

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found in file")

        # Chunk the text
        chunks = document_service.chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")

        # Generate embeddings
        embeddings = embedding_service.generate_embeddings(chunks)

        # Store in vector database
        num_stored = vectordb_service.store_embeddings(
            embeddings=embeddings, chunks=chunks, filename=file.filename
        )

        logger.info(f"Successfully indexed {num_stored} chunks from {file.filename}")

        return IndexResponse(
            status="success",
            filename=file.filename,
            chunks_indexed=num_stored,
            message=f"Successfully indexed {num_stored} chunks",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat endpoint that performs RAG (Retrieval-Augmented Generation) with conversation memory

    - **query**: User's question
    - **top_k**: Number of context chunks to retrieve (default: 3)
    - **session_id**: Optional session ID to maintain conversation context
    """
    try:
        logger.info(
            f"Processing query: {request.query} (session: {request.session_id})"
        )

        # Generate embedding for query
        query_embedding = embedding_service.generate_embeddings([request.query])[0]

        # Search in vector database
        search_results = vectordb_service.search(
            query_embedding=query_embedding, top_k=request.top_k
        )

        if not search_results:
            # No context found, but still maintain conversation
            answer = "I don't have enough information to answer this question. Please index some documents first."
            session_id = session_memory_service.add_message(
                request.session_id, "user", request.query
            )
            session_memory_service.add_message(session_id, "assistant", answer)

            return ChatResponse(answer=answer, sources=[], session_id=session_id)

        # Prepare context and sources
        context_parts = []
        sources = []

        for result in search_results:
            context_parts.append(result["text"])
            source = f"{result['source']} (chunk {result['chunk_id']})"
            if source not in sources:
                sources.append(source)

        context = "\n\n".join(context_parts)

        # Get conversation history for context
        conversation_history = session_memory_service.get_conversation_context(
            request.session_id, last_n=5  # Include last 5 messages for context
        )

        # Generate response using LLM with context and conversation history
        answer = llm_service.generate_response(
            query=request.query,
            context=context,
            conversation_history=conversation_history if conversation_history else None,
        )

        # Store conversation in memory
        session_id = session_memory_service.add_message(
            request.session_id, "user", request.query
        )
        session_memory_service.add_message(session_id, "assistant", answer)

        logger.info(f"Response generated successfully (session: {session_id})")

        return ChatResponse(answer=answer, sources=sources, session_id=session_id)

    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}", tags=["Memory"])
async def clear_session(session_id: str):
    """
    Clear conversation history for a specific session

    - **session_id**: Session ID to clear
    """
    try:
        session_memory_service.clear_session(session_id)
        return {"status": "success", "message": f"Session {session_id} cleared"}
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", tags=["Memory"])
async def get_session_info(session_id: str):
    """
    Get information about a conversation session

    - **session_id**: Session ID to query
    """
    try:
        info = session_memory_service.get_session_info(session_id)
        if info is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/stats", tags=["Memory"])
async def get_sessions_stats():
    """
    Get statistics about active sessions
    """
    try:
        return {
            "active_sessions": session_memory_service.get_active_sessions_count(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
