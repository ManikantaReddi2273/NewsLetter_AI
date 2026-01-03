"""API routes for the Newsletter AI application."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from loguru import logger

from app.database import get_db
from app.schemas import (
    UserCreate, UserResponse, UserLogin,
    SearchRequest, SearchResponse,
    SummarizeRequest, SummarizeResponse,
    FeedbackCreate, FeedbackResponse,
    ArticleResponse
)
from app.models import User, Article, FAISSEmbedding, UserFeedback
from app.services.faiss_service import faiss_service
from app.services.groq_service import groq_service
from app.services.redis_service import redis_service
from app.services.serper_service import serper_service
from app.services.resend_service import resend_service

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user object
    """
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


@router.post("/login", response_model=UserResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login an existing user.
    
    Args:
        user_data: User login data
        db: Database session
        
    Returns:
        User object
    """
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


@router.post("/search_articles", response_model=SearchResponse)
async def search_articles(
    search_data: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for articles using semantic similarity (FAISS).
    
    Args:
        search_data: Search query and parameters
        db: Database session
        
    Returns:
        List of matching articles with metadata
    """
    try:
        # Generate cache key
        cache_key = redis_service.get_cache_key(
            "search",
            query=search_data.query,
            user_id=search_data.user_id,
            top_k=search_data.top_k
        )
        
        # Try to get from cache
        cached_result = redis_service.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached search results for query: {search_data.query}")
            return SearchResponse(**cached_result)
        
        # Perform FAISS search
        search_results = faiss_service.search(search_data.query, top_k=search_data.top_k)
        
        if not search_results:
            return SearchResponse(
                articles=[],
                query=search_data.query,
                total_results=0
            )
        
        # Get article IDs
        article_ids = [article_id for article_id, _ in search_results]
        
        # Fetch articles from database
        articles = db.query(Article).filter(Article.id.in_(article_ids)).all()
        
        # Create article lookup
        article_lookup = {article.id: article for article in articles}
        
        # Sort articles by FAISS ranking
        sorted_articles = []
        for article_id, distance in search_results:
            if article_id in article_lookup:
                sorted_articles.append(article_lookup[article_id])
        
        # Format response
        article_responses = [
            ArticleResponse(
                id=article.id,
                title=article.title,
                url=article.url,
                summary=article.summary,
                source=article.source,
                bias_score=article.bias_score
            )
            for article in sorted_articles
        ]
        
        response = SearchResponse(
            articles=article_responses,
            query=search_data.query,
            total_results=len(article_responses)
        )
        
        # Cache the result
        redis_service.set(cache_key, response.model_dump(), ttl=3600)
        
        logger.info(f"Found {len(article_responses)} articles for query: {search_data.query}")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to search articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_article(
    summarize_data: SummarizeRequest,
    db: Session = Depends(get_db)
):
    """
    Summarize an article using Groq API.
    
    Args:
        summarize_data: Article URL and reading level
        db: Database session
        
    Returns:
        Article summary with bullet points
    """
    try:
        # Check if article already exists and has summary
        existing_article = db.query(Article).filter(Article.url == summarize_data.article_url).first()
        
        if existing_article and existing_article.summary:
            summary_points = json.loads(existing_article.summary)
            word_count = sum(len(point.split()) for point in summary_points)
            
            logger.info(f"Returning cached summary for: {summarize_data.article_url}")
            
            return SummarizeResponse(
                summary=summary_points,
                word_count=word_count,
                reading_level=summarize_data.reading_level.value
            )
        
        # Generate new summary
        summary_result = groq_service.summarize_from_url(
            url=summarize_data.article_url,
            reading_level=summarize_data.reading_level.value
        )
        
        # Update or create article with summary
        if existing_article:
            existing_article.summary = json.dumps(summary_result['summary'])
            db.commit()
            logger.info(f"Updated summary for existing article: {summarize_data.article_url}")
        
        response = SummarizeResponse(
            summary=summary_result['summary'],
            word_count=summary_result['word_count'],
            reading_level=summary_result['reading_level']
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to summarize article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}"
        )


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit user feedback/rating for an article.
    
    Args:
        feedback_data: User feedback data
        db: Database session
        
    Returns:
        Created feedback object
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == feedback_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify article exists
        article = db.query(Article).filter(Article.id == feedback_data.article_id).first()
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Check if feedback already exists
        existing_feedback = db.query(UserFeedback).filter(
            UserFeedback.user_id == feedback_data.user_id,
            UserFeedback.article_id == feedback_data.article_id
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.rating = feedback_data.rating
            db.commit()
            db.refresh(existing_feedback)
            
            logger.info(f"Updated feedback for user {feedback_data.user_id}, article {feedback_data.article_id}")
            
            return FeedbackResponse(
                id=existing_feedback.id,
                user_id=existing_feedback.user_id,
                article_id=existing_feedback.article_id,
                rating=existing_feedback.rating
            )
        
        # Create new feedback
        new_feedback = UserFeedback(
            user_id=feedback_data.user_id,
            article_id=feedback_data.article_id,
            rating=feedback_data.rating
        )
        
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        
        logger.info(f"New feedback created for user {feedback_data.user_id}, article {feedback_data.article_id}")
        
        # Clear recommendation cache for this user
        redis_service.clear_pattern(f"recommend:user_id:{feedback_data.user_id}:*")
        
        return FeedbackResponse(
            id=new_feedback.id,
            user_id=new_feedback.user_id,
            article_id=new_feedback.article_id,
            rating=new_feedback.rating
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """
    Get article by ID.
    
    Args:
        article_id: Article ID
        db: Database session
        
    Returns:
        Article object
    """
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        return ArticleResponse(
            id=article.id,
            title=article.title,
            url=article.url,
            summary=article.summary,
            source=article.source,
            bias_score=article.bias_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get article: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    faiss_stats = faiss_service.get_index_stats()
    
    return {
        "status": "healthy",
        "faiss_index": faiss_stats
    }


@router.get("/fetch_news")
async def fetch_news(
    query: str = None,
    user_id: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Fetch news articles using Serper API.
    If user_id provided, fetch based on user interests.
    
    Args:
        query: Search query (optional)
        user_id: User ID to fetch personalized news (optional)
        limit: Number of articles to fetch
        db: Database session
        
    Returns:
        List of news articles
    """
    try:
        articles_data = []
        
        if user_id:
            # Fetch user interests
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            interests = json.loads(user.interests)
            articles_per_interest = max(1, limit // len(interests))
            articles_data = serper_service.fetch_news_by_interests(interests, articles_per_interest)
        elif query:
            # Fetch by query
            articles_data = serper_service.fetch_news(query, limit)
        else:
            # Fetch general tech news
            articles_data = serper_service.fetch_news("technology news", limit)
        
        # Store articles in database (avoid duplicates)
        stored_articles = []
        for article_data in articles_data:
            # Check if article exists
            existing = db.query(Article).filter(Article.url == article_data["url"]).first()
            
            if not existing:
                new_article = Article(
                    title=article_data["title"],
                    url=article_data["url"],
                    content=article_data["content"],
                    source=article_data["source"]
                )
                db.add(new_article)
                db.commit()
                db.refresh(new_article)
                stored_articles.append(new_article)
            else:
                stored_articles.append(existing)
        
        # Convert to response format
        response_articles = [
            ArticleResponse(
                id=article.id,
                title=article.title,
                url=article.url,
                summary=article.summary,
                source=article.source,
                bias_score=article.bias_score
            )
            for article in stored_articles
        ]
        
        logger.info(f"Fetched and stored {len(response_articles)} articles")
        
        return {
            "articles": response_articles,
            "total": len(response_articles)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news: {str(e)}"
        )


@router.post("/generate_embeddings")
async def generate_embeddings_endpoint(
    article_ids: List[int] = None,
    db: Session = Depends(get_db)
):
    """
    Generate FAISS embeddings for articles.
    
    Args:
        article_ids: List of article IDs to generate embeddings for (optional, processes all if None)
        db: Database session
        
    Returns:
        Status and number of embeddings generated
    """
    try:
        # Get articles without embeddings
        if article_ids:
            articles = db.query(Article).filter(Article.id.in_(article_ids)).all()
        else:
            articles = db.query(Article).outerjoin(FAISSEmbedding).filter(
                FAISSEmbedding.id == None
            ).all()
        
        if not articles:
            return {
                "status": "success",
                "message": "No articles need embeddings",
                "embeddings_generated": 0
            }
        
        # Generate embeddings
        texts = [article.content for article in articles]
        article_id_list = [article.id for article in articles]
        
        embeddings = faiss_service.generate_embeddings_batch(texts)
        faiss_service.add_embeddings(embeddings, article_id_list)
        
        # Store in database
        for i, article in enumerate(articles):
            embedding_bytes = embeddings[i].tobytes()
            
            faiss_embedding = FAISSEmbedding(
                embedding_vector=embedding_bytes,
                article_id=article.id
            )
            
            db.add(faiss_embedding)
            db.commit()
            db.refresh(faiss_embedding)
            
            article.embedding_id = faiss_embedding.id
            db.commit()
        
        # Save FAISS index
        import os
        os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
        faiss_service.save_index(settings.FAISS_INDEX_PATH)
        
        logger.info(f"Generated embeddings for {len(articles)} articles")
        
        return {
            "status": "success",
            "message": f"Generated embeddings for {len(articles)} articles",
            "embeddings_generated": len(articles),
            "faiss_stats": faiss_service.get_index_stats()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )


@router.post("/send_email")
async def send_newsletter_email(
    user_id: int,
    article_ids: List[int] = None,
    subject: str = "Your AI-Curated Newsletter",
    db: Session = Depends(get_db)
):
    """
    Send newsletter email to user.
    
    Args:
        user_id: User ID
        article_ids: List of article IDs to include (optional, uses recent if None)
        subject: Email subject
        db: Database session
        
    Returns:
        Email send status
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get articles
        if article_ids:
            articles = db.query(Article).filter(Article.id.in_(article_ids)).all()
        else:
            # Get recent articles
            articles = db.query(Article).order_by(Article.created_at.desc()).limit(5).all()
        
        if not articles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No articles found to send"
            )
        
        # Convert to dict format
        articles_data = [
            {
                "title": article.title,
                "url": article.url,
                "content": article.summary if article.summary else article.content[:200] + "...",
                "source": article.source
            }
            for article in articles
        ]
        
        # Send email
        success = resend_service.send_newsletter(
            to_email=user.email,
            subject=subject,
            html_content=None,
            articles=articles_data
        )
        
        if success:
            logger.info(f"Newsletter sent to {user.email}")
            return {
                "status": "success",
                "message": f"Newsletter sent to {user.email}",
                "articles_sent": len(articles)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send newsletter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send newsletter: {str(e)}"
        )
