"""Simplified FastAPI app for Phase 1 MVP - Signup, News Fetching, Search, Feedback."""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from loguru import logger
import json
import numpy as np
import requests
import pickle
from pathlib import Path

from app.database import get_db, init_db, SessionLocal
from app.models import User, Article, UserFeedback, FAISSEmbedding
from app.schemas import (
    UserCreate, UserResponse, UserLogin,
    ArticleResponse, FeedbackCreate, FeedbackResponse,
    SearchRequest, SearchResponse
)
from app.config import get_settings
from app.services.serper_service import serper_service
from app.services.groq_service import groq_service
from app.services.faiss_service import faiss_service
from app.services.fact_check_service import fact_check_service

settings = get_settings()
FAISS_INDEX_PATH = Path(__file__).resolve().parent / "data" / "faiss" / "faiss_index.pkl"


def _simple_fact_check(text: str) -> str:
    """Use real fact-check service or fallback to heuristic."""
    if not text:
        return "unknown"
    try:
        result = fact_check_service.check_article(text)
        return result.get("overall_status", "unknown")
    except Exception as e:
        logger.warning(f"Fact check failed: {e}")
        return "unknown"


def _simple_bias(text: str) -> tuple:
    """Rough bias scorer; produces varied scores for testing."""
    if not text:
        return 0.0, "No content to score"
    lowered = text.lower()
    # Left-leaning keywords
    left_keywords = ["progressive", "climate", "inequality", "social justice", "regulation", "fair wage", "labor rights"]
    # Right-leaning keywords
    right_keywords = ["market", "tax cut", "deregulation", "business", "entrepreneur", "conservative", "free market"]
    # Neutral keywords
    neutral_keywords = ["technology", "innovation", "research", "study", "data", "report", "analysis"]
    
    left_score = sum(lowered.count(kw) for kw in left_keywords)
    right_score = sum(lowered.count(kw) for kw in right_keywords)
    neutral_score = sum(lowered.count(kw) for kw in neutral_keywords)
    
    total = left_score + right_score + neutral_score
    if total == 0:
        return 0.0, "Neutral (no bias markers detected)"
    
    # Calculate bias: -1 (left) to +1 (right)
    bias_score = (right_score - left_score) / (total + 1e-6)
    bias_score = max(min(bias_score, 1.0), -1.0)
    
    if abs(bias_score) < 0.3:
        explanation = "Balanced coverage with minimal bias"
    elif bias_score > 0.3:
        explanation = "Slightly leans right (market/business focus)"
    else:
        explanation = "Slightly leans left (progressive/social focus)"
    
    return bias_score, explanation


def _persist_faiss_index():
    """Persist FAISS index to disk under backend/data/faiss/faiss_index.pkl."""
    try:
        FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss_service.save_index(str(FAISS_INDEX_PATH))
        logger.info(f"FAISS index saved to {FAISS_INDEX_PATH}")
    except Exception as exc:
        logger.warning(f"Failed to persist FAISS index: {exc}")


def _load_faiss_index():
    """Load FAISS index from disk, else rebuild from DB embeddings."""
    # Prefer on-disk index for fast startup
    if FAISS_INDEX_PATH.exists():
        try:
            faiss_service.load_index(str(FAISS_INDEX_PATH))
            logger.info(f"FAISS index loaded from {FAISS_INDEX_PATH}")
            return
        except Exception as exc:
            logger.warning(f"Failed to load FAISS index from disk, will rebuild from DB: {exc}")
    # Fallback: rebuild from stored per-article embeddings in DB
    session = SessionLocal()
    try:
        rows = session.query(FAISSEmbedding.article_id, FAISSEmbedding.embedding_vector).all()
        faiss_service.rebuild_from_embeddings(rows)
        if FAISS_INDEX_PATH.parent.exists():
            _persist_faiss_index()
    except Exception as exc:
        logger.warning(f"Skipping FAISS rebuild: {exc}")
    finally:
        session.close()

# Initialize FastAPI app
app = FastAPI(
    title="Newsletter AI - Phase 1 MVP",
    description="Signup, News Fetching, Semantic Search, Feedback",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("🚀 Starting Newsletter AI - Phase 1 MVP")
    init_db()
    logger.info("✅ Database initialized")
    _load_faiss_index()

# Health check
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mode": "phase1-mvp", "features": ["signup", "login", "fetch_news", "search", "feedback"]}

# Signup endpoint
@app.post("/api/v1/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account."""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        new_user = User(
            email=user_data.email,
            interests=json.dumps(user_data.interests),
            reading_level=user_data.reading_level
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user created: {new_user.email}")
        
        # Format response
        response = UserResponse(
            id=new_user.id,
            email=new_user.email,
            interests=json.loads(new_user.interests),
            reading_level=new_user.reading_level.value,
            subscription_status=new_user.subscription_status.value
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

# Login endpoint
@app.post("/api/v1/login", response_model=UserResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login an existing user."""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please sign up first."
            )
        
        logger.info(f"User logged in: {user.email}")
        
        # Format response
        response = UserResponse(
            id=user.id,
            email=user.email,
            interests=json.loads(user.interests),
            reading_level=user.reading_level.value,
            subscription_status=user.subscription_status.value
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to login user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to login user: {str(e)}"
        )


# Fetch News endpoint
@app.get("/api/v1/fetch_news")
async def fetch_news(
    user_id: int = Query(None),
    query: str = Query(None),
    limit: int = Query(10),
    apply_fact_check: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Fetch news articles based on user interests or search query.
    
    Args:
        user_id: User ID to fetch personalized news
        query: Search query
        limit: Number of articles
        db: Database session
        
    Returns:
        List of articles
    """
    try:
        articles_data = []
        
        if user_id:
            # Fetch user and their interests
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            interests = json.loads(user.interests)
            articles_per_interest = max(1, limit // len(interests)) if interests else limit
            articles_data = serper_service.fetch_news_by_interests(interests, articles_per_interest)
        elif query:
            articles_data = serper_service.fetch_news(query, limit)
        else:
            articles_data = serper_service.fetch_news("technology news", limit)
        
        # Store articles in database (avoid duplicates)
        stored_articles = []
        for article_data in articles_data:
            existing = db.query(Article).filter(Article.url == article_data["url"]).first()
            
            if not existing:
                fact_status = None
                bias_score = None
                bias_explanation = None
                if apply_fact_check:
                    fact_status = _simple_fact_check(article_data.get("content", ""))
                    bias_score, bias_explanation = _simple_bias(article_data.get("content", ""))
                new_article = Article(
                    title=article_data["title"],
                    url=article_data["url"],
                    content=article_data["content"],
                    source=article_data["source"],
                    fact_check_status=fact_status,
                    bias_score=bias_score,
                    bias_explanation=bias_explanation
                )
                db.add(new_article)
                db.commit()
                db.refresh(new_article)
                stored_articles.append(new_article)
            else:
                stored_articles.append(existing)
        
        logger.info(f"✅ Fetched {len(stored_articles)} articles")
        
        return {
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "url": a.url,
                    "content": a.content,
                    "summary": a.summary,
                    "source": a.source,
                    "bias_score": a.bias_score if a.bias_score is not None else 0.0,
                    "fact_check_status": a.fact_check_status,
                    "bias_explanation": a.bias_explanation
                }
                for a in stored_articles
            ],
            "total": len(stored_articles)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news: {str(e)}"
        )


# Summarize endpoint
@app.post("/api/v1/summarize")
async def summarize(article_id: int, db: Session = Depends(get_db)):
    """
    Summarize an article using Groq AI.
    
    Args:
        article_id: Article ID to summarize
        db: Database session
        
    Returns:
        Summary and reading level adaptation
    """
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Use Groq to summarize (with graceful fallback)
        summary = groq_service.summarize(article.content, "intermediate") if article.content else article.content[:200]
        
        # Update article with summary
        article.summary = summary
        db.commit()
        
        logger.info(f"✅ Summarized article {article_id}")
        
        return {
            "article_id": article.id,
            "title": article.title,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to summarize: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize: {str(e)}"
        )


# Helper function to calculate relevance score (Google-like matching)
def _calculate_relevance_score(article: Article, query: str) -> float:
    """
    Calculate relevance score like Google - stricter matching.
    Only returns articles that actually contain the search terms.
    """
    query_lower = query.lower()
    keywords = [k.strip() for k in query_lower.split() if k.strip()]
    
    if not keywords:
        return 0.0
    
    title_lower = (article.title or "").lower()
    content_lower = (article.content or "").lower()
    source_lower = (article.source or "").lower()
    
    score = 0.0
    matched_keywords = 0
    
    # Count how many keywords appear in title
    title_matches = sum(1 for keyword in keywords if keyword in title_lower)
    
    # Count how many keywords appear anywhere
    total_matches = sum(1 for keyword in keywords if keyword in title_lower or keyword in content_lower or keyword in source_lower)
    
    # Only return articles where at least one keyword matches AND
    # at least 50% of keywords are found across all fields
    if total_matches == 0:
        return 0.0  # No match at all
    
    match_ratio = total_matches / len(keywords)
    
    if match_ratio < 0.5:  # Less than 50% keywords matched
        return 0.0
    
    # Scoring: title matches weighted heavily
    score += title_matches * 10
    
    # Content/source matches weighted lower
    content_matches = sum(1 for keyword in keywords if keyword in content_lower)
    source_matches = sum(1 for keyword in keywords if keyword in source_lower)
    
    score += content_matches * 2
    score += source_matches * 3
    
    return score


# Search articles (Real-time fetch from Serper API)
@app.post("/api/v1/search_articles")
async def search_articles(search_data: SearchRequest, db: Session = Depends(get_db)):
    """
    Real-time search - fetches fresh articles from Serper API.
    1. Fetches latest articles from Serper for the search query
    2. Stores new articles in database
    3. Applies bias scoring and fact-checking
    4. Returns only relevant results
    
    Args:
        search_data: Search query and user preferences
        db: Database session
        
    Returns:
        List of fresh, relevant articles
    """
    try:
        query = search_data.query
        limit = search_data.top_k or 10
        
        if not query or len(query.strip()) < 2:
            return {
                "query": query,
                "articles": [],
                "total": 0,
                "message": "Please enter at least 2 characters"
            }
        
        logger.info(f"🔍 Real-time search for: '{query}'")
        
        # Step 1: Fetch fresh articles from Serper API
        try:
            serper_results = serper_service.search_news(query, num=limit)
            news_items = serper_results.get("news", [])
            logger.info(f"📰 Serper API returned {len(news_items)} fresh articles")
        except Exception as e:
            logger.error(f"Serper API failed: {e}")
            news_items = []
        
        # Step 2: Process and store new articles
        new_articles = []
        for item in news_items:
            try:
                # Check if article already exists
                existing = db.query(Article).filter(Article.url == item.get("link")).first()
                if existing:
                    new_articles.append(existing)
                    continue
                
                # Extract article data
                title = item.get("title", "Untitled")
                url = item.get("link", "")
                snippet = item.get("snippet", "")
                source = item.get("source", "Unknown")
                
                # Generate summary with Groq
                try:
                    summary = groq_service.summarize(snippet)
                except Exception as e:
                    logger.warning(f"Groq summarization failed: {e}")
                    summary = snippet[:200]
                
                # Calculate bias score
                bias_score = _simple_bias(snippet)
                bias_label = "balanced" if abs(bias_score) < 0.3 else ("slightly biased" if abs(bias_score) < 0.6 else "biased")
                bias_explanation = f"{bias_label.capitalize()}: {bias_score:.2f}"
                
                # Fact-check the article
                try:
                    fact_result = fact_check_service.check_article(snippet)
                    fact_status = fact_result.get("overall_status", "unknown")
                except Exception as e:
                    logger.warning(f"Fact-check failed: {e}")
                    fact_status = "unknown"
                
                # Create new article
                article = Article(
                    title=title,
                    url=url,
                    content=snippet,
                    summary=summary,
                    source=source,
                    bias_score=bias_score,
                    bias_explanation=bias_explanation,
                    fact_check_status=fact_status
                )
                
                db.add(article)
                db.commit()
                db.refresh(article)
                
                new_articles.append(article)
                logger.info(f"✅ Stored new article: {title[:50]}...")
                
            except Exception as e:
                logger.error(f"Failed to process article: {e}")
                db.rollback()
                continue
        
        # Step 3: Filter by relevance
        relevant_articles = []
        for article in new_articles:
            score = _calculate_relevance_score(article, query)
            if score > 0:
                relevant_articles.append((article, score))
        
        # Sort by relevance
        relevant_articles.sort(key=lambda x: x[1], reverse=True)
        final_results = [a for a, _ in relevant_articles[:limit]]
        
        logger.info(f"✅ Returning {len(final_results)} relevant articles for: '{query}'")
        
        response = {
            "query": query,
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "url": a.url,
                    "summary": a.summary or a.content[:200],
                    "source": a.source,
                    "bias_score": a.bias_score or 0.5,
                    "fact_check_status": a.fact_check_status,
                    "bias_explanation": a.bias_explanation,
                    "deep_dive_content": a.deep_dive_content
                }
                for a in final_results
            ],
            "total": len(final_results)
        }
        
        if len(final_results) == 0:
            response["message"] = f"No relevant articles found for '{query}'."
        
        return response
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# Generate embeddings for stored articles and rebuild FAISS index
@app.post("/api/v1/generate_embeddings")
async def generate_embeddings(limit: int = Query(50), db: Session = Depends(get_db)):
    try:
        articles = db.query(Article).limit(limit).all()
        vectors = []
        ids = []
        for art in articles:
            if not art.content:
                continue
            embedding = faiss_service.generate_embedding(art.content)
            vectors.append(embedding)
            ids.append(art.id)
            # Persist per-article embedding for reloads
            existing = db.query(FAISSEmbedding).filter(FAISSEmbedding.article_id == art.id).first()
            payload = pickle.dumps(embedding)
            if existing:
                existing.embedding_vector = payload
            else:
                db.add(FAISSEmbedding(article_id=art.id, embedding_vector=payload))
        if vectors:
            matrix = np.vstack(vectors).astype("float32")
            faiss_service.add_embeddings(matrix, ids)
            _persist_faiss_index()
        db.commit()
        return {"indexed": len(ids), "total_vectors": faiss_service.get_index_stats().get("total_vectors", 0)}
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")


def _content_based_recs(user_id: int, top_k: int, db: Session):
    liked = db.query(UserFeedback).filter(UserFeedback.user_id == user_id, UserFeedback.rating >= 4).all()
    if not liked:
        return []
    embeddings = []
    for fb in liked:
        emb_row = db.query(FAISSEmbedding).filter(FAISSEmbedding.article_id == fb.article_id).first()
        if emb_row and emb_row.embedding_vector:
            try:
                vec = pickle.loads(emb_row.embedding_vector)
                embeddings.append(vec)
            except Exception:
                continue
    if not embeddings:
        return []
    mean_vec = np.mean(np.vstack(embeddings), axis=0)
    return faiss_service.search_by_embedding(mean_vec, top_k=top_k)


def _collaborative_recs(user_id: int, top_k: int, db: Session):
    rows = db.query(UserFeedback).all()
    if not rows:
        return []
    users = sorted({r.user_id for r in rows})
    articles = sorted({r.article_id for r in rows})
    user_index = {u: i for i, u in enumerate(users)}
    article_index = {a: i for i, a in enumerate(articles)}
    if user_id not in user_index:
        return []
    matrix = np.zeros((len(users), len(articles)))
    for r in rows:
        matrix[user_index[r.user_id], article_index[r.article_id]] = r.rating
    target = matrix[user_index[user_id]]  # shape: (num_articles,)
    norms = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(target) + 1e-6) + 1e-6
    sims = (matrix @ target) / norms  # shape: (num_users,)
    scores_vec = sims @ matrix  # shape: (num_articles,)
    # zero out already-rated articles for this user
    for r in rows:
        if r.user_id == user_id and r.article_id in article_index:
            scores_vec[article_index[r.article_id]] = 0
    top_indices = scores_vec.argsort()[::-1][:top_k]
    return [articles[i] for i in top_indices if scores_vec[i] > 0]


@app.get("/api/v1/recommendations")
async def hybrid_recommendations(user_id: int = Query(...), k: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    """Hybrid recommendations: 70% FAISS content, 30% collaborative."""
    try:
        content_recs = _content_based_recs(user_id, k, db)
        collab_recs = _collaborative_recs(user_id, k, db)
        # content_recs returns list of tuples; collab list of article ids
        content_ids = [a for a, _dist in content_recs]
        combined = set(content_ids + collab_recs)
        if not combined:
            articles = db.query(Article).order_by(Article.created_at.desc()).limit(k).all()
        else:
            scores = {}
            for aid in combined:
                scores[aid] = 0
                if aid in content_ids:
                    scores[aid] += 0.7
                if aid in collab_recs:
                    scores[aid] += 0.3
            ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:k]
            articles = db.query(Article).filter(Article.id.in_(ranked_ids)).all()
        return {
            "user_id": user_id,
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "url": a.url,
                    "summary": a.summary or a.content[:200],
                    "source": a.source,
                    "bias_score": a.bias_score,
                    "fact_check_status": a.fact_check_status
                }
                for a in articles
            ],
            "total": len(articles)
        }
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@app.get("/api/v1/deep_dive")
async def deep_dive(article_id: int, db: Session = Depends(get_db)):
    """Deep dive using arXiv + Groq (placeholder with graceful fallbacks)."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    try:
        raw_summary = groq_service.summarize(article.content, "beginner") if article.content else ""
        if isinstance(raw_summary, dict) and raw_summary.get("summary"):
            bullet_points = raw_summary["summary"]
            if isinstance(bullet_points, list):
                summary = "\n".join([f"• {pt}" for pt in bullet_points])
            else:
                summary = str(bullet_points)
        else:
            summary = str(raw_summary)
    except Exception as exc:
        summary = f"Summary unavailable: {str(exc)[:100]}"
    deep_dive_text = summary
    article.deep_dive_content = deep_dive_text
    db.commit()
    return {"article_id": article.id, "deep_dive_content": deep_dive_text}


# Feedback endpoint
@app.post("/api/v1/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(feedback_data: FeedbackCreate, db: Session = Depends(get_db)):
    """
    Submit user feedback (rating) for an article.
    
    Args:
        feedback_data: User ID, article ID, and rating
        db: Database session
        
    Returns:
        Feedback confirmation
    """
    try:
        # Verify user and article exist
        user = db.query(User).filter(User.id == feedback_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        article = db.query(Article).filter(Article.id == feedback_data.article_id).first()
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Create feedback
        feedback = UserFeedback(
            user_id=feedback_data.user_id,
            article_id=feedback_data.article_id,
            rating=feedback_data.rating
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        logger.info(f"✅ Feedback created: user {feedback_data.user_id} rated article {feedback_data.article_id} with {feedback_data.rating} stars")
        
        return {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "article_id": feedback.article_id,
            "rating": feedback.rating,
            "timestamp": feedback.timestamp.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
