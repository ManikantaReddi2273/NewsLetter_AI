"""Database models for the Newsletter AI application."""
from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, Enum, ForeignKey, LargeBinary, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration."""
    FREE = "free"
    PREMIUM = "premium"


class ReadingLevel(str, enum.Enum):
    """Reading level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    interests = Column(Text, nullable=False)  # JSON stored as text
    reading_level = Column(Enum(ReadingLevel), nullable=False)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.FREE)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationships
    feedback = relationship("UserFeedback", back_populates="user")


class Article(Base):
    """Article model."""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    source = Column(String(255), nullable=False)
    bias_score = Column(Float, default=None)
    fact_check_status = Column(String(20), default=None)
    bias_explanation = Column(Text, default=None)
    deep_dive_content = Column(Text, default=None)
    embedding_id = Column(Integer, ForeignKey("faiss_embeddings.id"))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationships
    embedding = relationship("FAISSEmbedding", back_populates="article", uselist=False, foreign_keys="[FAISSEmbedding.article_id]")
    feedback = relationship("UserFeedback", back_populates="article")


class FAISSEmbedding(Base):
    """FAISS embedding model."""
    __tablename__ = "faiss_embeddings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding_vector = Column(LargeBinary, nullable=False)  # Serialized embedding
    article_id = Column(Integer, ForeignKey("articles.id"), unique=True, nullable=False)
    
    # Relationships
    article = relationship("Article", back_populates="embedding", foreign_keys=[article_id])


class UserFeedback(Base):
    """User feedback model."""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    rating = Column(Integer, CheckConstraint("rating >= 1 AND rating <= 5"), nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    article = relationship("Article", back_populates="feedback")
