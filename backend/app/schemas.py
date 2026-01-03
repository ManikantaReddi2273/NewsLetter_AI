"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from enum import Enum


class ReadingLevelEnum(str, Enum):
    """Reading level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class SubscriptionStatusEnum(str, Enum):
    """Subscription status enumeration."""
    FREE = "free"
    PREMIUM = "premium"


# User Schemas
class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    interests: List[str] = Field(..., min_items=1, max_items=10)
    reading_level: ReadingLevelEnum


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    interests: List[str]
    reading_level: str
    subscription_status: str
    
    class Config:
        from_attributes = True


# Article Schemas
class ArticleCreate(BaseModel):
    """Schema for creating an article."""
    title: str = Field(..., max_length=500)
    url: str = Field(..., max_length=500)
    content: str
    source: str = Field(..., max_length=255)


class ArticleResponse(BaseModel):
    """Schema for article response."""
    id: int
    title: str
    url: str
    summary: Optional[str] = None
    source: str
    bias_score: Optional[float] = None
    fact_check_status: Optional[str] = None
    bias_explanation: Optional[str] = None
    deep_dive_content: Optional[str] = None
    
    class Config:
        from_attributes = True


# Search Schemas
class SearchRequest(BaseModel):
    """Schema for search request."""
    query: str = Field(..., min_length=1, max_length=500)
    user_id: int
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResponse(BaseModel):
    """Schema for search response."""
    articles: List[ArticleResponse]
    query: str
    total_results: int


# Summarization Schemas
class SummarizeRequest(BaseModel):
    """Schema for summarization request."""
    article_url: str
    reading_level: ReadingLevelEnum = ReadingLevelEnum.INTERMEDIATE


class SummarizeResponse(BaseModel):
    """Schema for summarization response."""
    summary: List[str]
    word_count: int
    reading_level: str


# Feedback Schemas
class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    user_id: int
    article_id: int
    rating: int = Field(..., ge=1, le=5)


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    user_id: int
    article_id: int
    rating: int
    
    class Config:
        from_attributes = True


# Recommendation Schemas
class RecommendationResponse(BaseModel):
    """Schema for hybrid recommendations."""
    user_id: int
    articles: List[ArticleResponse]
    total: int


# Fact check / bias detection schemas
class FactCheckResult(BaseModel):
    """Schema for fact-check results."""
    article_id: int
    status: str
    bias_score: Optional[float] = None
    bias_explanation: Optional[str] = None


class DeepDiveResponse(BaseModel):
    """Schema for deep dive content."""
    article_id: int
    deep_dive_content: str
