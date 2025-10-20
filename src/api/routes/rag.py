"""RAG (Knowledge Base Search) API routes."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from ...services.rag_service import rag_service


router = APIRouter(prefix="/api/rag", tags=["Knowledge Base"])


class SearchRequest(BaseModel):
    """Request model for knowledge base search."""
    query: str
    n_results: int = 5
    category: Optional[str] = None


class SearchResult(BaseModel):
    """Single search result."""
    content: str
    category: str
    distance: float
    source_id: Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    results: List[SearchResult]
    count: int


@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """
    Search the knowledge base using semantic similarity.

    Use this endpoint to find relevant parenting information based on
    natural language queries.

    Examples:
    - "What vaccines does my 6 month old need?"
    - "Is fever normal during teething?"
    - "Activities for 2 year old"
    """
    if request.category:
        # Search within specific category
        results = rag_service.search_by_category(
            query=request.query,
            category=request.category,
            n_results=request.n_results
        )
    else:
        # Search all categories
        results = rag_service.search(
            query=request.query,
            n_results=request.n_results
        )

    # Format results
    formatted_results = []
    for doc in results:
        formatted_results.append(SearchResult(
            content=doc['content'],
            category=doc['metadata'].get('category', 'general'),
            distance=doc['distance'],
            source_id=doc.get('id')
        ))

    return SearchResponse(
        query=request.query,
        results=formatted_results,
        count=len(formatted_results)
    )


@router.get("/search", response_model=SearchResponse)
async def search_knowledge_base_get(
    q: str = Query(..., description="Search query"),
    n: int = Query(5, description="Number of results", le=20),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Search the knowledge base (GET method for simple queries).

    Query parameters:
    - q: Search query
    - n: Number of results (max 20)
    - category: Optional category filter
    """
    request = SearchRequest(query=q, n_results=n, category=category)
    return await search_knowledge_base(request)


@router.get("/categories")
async def get_categories():
    """
    Get list of available knowledge base categories.

    Returns all categories that can be used to filter search results.
    """
    categories = rag_service.get_available_categories()
    return {
        "categories": categories,
        "count": len(categories)
    }


@router.get("/info")
async def get_knowledge_base_info():
    """
    Get information about the knowledge base.

    Returns metadata about the vector database including:
    - Total number of documents
    - Collection name
    - Status
    """
    info = rag_service.get_collection_info()
    return info


@router.get("/context")
async def get_context_for_question(
    question: str = Query(..., description="Question to get context for"),
    n_results: int = Query(5, description="Number of documents to retrieve", le=10)
):
    """
    Get relevant context for answering a question.

    This endpoint retrieves and combines relevant knowledge base
    documents to provide context for an AI to answer the question.

    Used internally by the AI reasoning system.
    """
    context = rag_service.get_context_for_question(
        question=question,
        n_results=n_results
    )

    if not context:
        raise HTTPException(
            status_code=404,
            detail="No relevant context found for this question"
        )

    return {
        "question": question,
        "context": context,
        "sources": n_results
    }
