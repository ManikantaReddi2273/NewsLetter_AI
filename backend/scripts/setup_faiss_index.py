"""Script to initialize FAISS index with sample articles."""
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from loguru import logger
import numpy as np

from app.database import SessionLocal, init_db
from app.models import Article, FAISSEmbedding
from app.services.faiss_service import faiss_service
from app.config import get_settings

settings = get_settings()


def create_sample_articles(db: Session) -> list:
    """
    Create sample articles for testing.
    
    Args:
        db: Database session
        
    Returns:
        List of created article IDs
    """
    sample_articles = [
        {
            "title": "The Future of Artificial Intelligence in Healthcare",
            "url": "https://example.com/ai-healthcare-1",
            "content": "Artificial intelligence is revolutionizing healthcare with advanced diagnostics, personalized treatment plans, and predictive analytics. Machine learning algorithms can now detect diseases earlier than traditional methods.",
            "source": "TechNews"
        },
        {
            "title": "Climate Change: Latest Research and Findings",
            "url": "https://example.com/climate-change-1",
            "content": "New research shows accelerating impacts of climate change on global ecosystems. Scientists warn of urgent need for action to reduce carbon emissions and transition to renewable energy sources.",
            "source": "ScienceDaily"
        },
        {
            "title": "Breakthrough in Quantum Computing",
            "url": "https://example.com/quantum-computing-1",
            "content": "Researchers achieve quantum supremacy with new processor design. The breakthrough could revolutionize cryptography, drug discovery, and complex simulations beyond classical computing capabilities.",
            "source": "QuantumTech"
        },
        {
            "title": "Ethics in AI Development",
            "url": "https://example.com/ai-ethics-1",
            "content": "As AI systems become more prevalent, questions about bias, privacy, and accountability grow more urgent. Experts call for comprehensive ethical frameworks and regulatory oversight.",
            "source": "AI Ethics Journal"
        },
        {
            "title": "Space Exploration: Mars Mission Updates",
            "url": "https://example.com/mars-mission-1",
            "content": "Latest data from Mars rovers reveals new evidence of ancient water systems. The findings support theories about past habitability and guide future exploration missions.",
            "source": "Space News"
        },
        {
            "title": "Renewable Energy Revolution",
            "url": "https://example.com/renewable-energy-1",
            "content": "Solar and wind power costs continue to decline, making renewable energy competitive with fossil fuels. Countries worldwide accelerate transition to clean energy infrastructure.",
            "source": "Energy Today"
        },
        {
            "title": "Advances in Gene Therapy",
            "url": "https://example.com/gene-therapy-1",
            "content": "CRISPR technology enables precise genetic modifications to treat inherited diseases. Clinical trials show promising results for previously untreatable conditions.",
            "source": "Medical Journal"
        },
        {
            "title": "Cybersecurity Threats in 2026",
            "url": "https://example.com/cybersecurity-1",
            "content": "AI-powered cyberattacks pose new challenges for digital security. Organizations invest heavily in advanced threat detection and zero-trust architectures.",
            "source": "CyberSec Weekly"
        },
        {
            "title": "The Impact of Remote Work on Productivity",
            "url": "https://example.com/remote-work-1",
            "content": "Long-term studies reveal mixed effects of remote work on employee productivity and well-being. Companies adapt with hybrid models and new management strategies.",
            "source": "Business Insights"
        },
        {
            "title": "Neuroscience Discoveries About Learning",
            "url": "https://example.com/neuroscience-1",
            "content": "Brain imaging studies uncover how neural pathways form during skill acquisition. Findings could improve educational methods and rehabilitation therapies.",
            "source": "Neuroscience Today"
        }
    ]
    
    created_ids = []
    
    for article_data in sample_articles:
        # Check if article already exists
        existing = db.query(Article).filter(Article.url == article_data["url"]).first()
        
        if not existing:
            article = Article(**article_data)
            db.add(article)
            db.commit()
            db.refresh(article)
            created_ids.append(article.id)
            logger.info(f"Created article: {article.title}")
        else:
            created_ids.append(existing.id)
            logger.info(f"Article already exists: {existing.title}")
    
    return created_ids


def generate_embeddings_for_articles(db: Session):
    """
    Generate FAISS embeddings for all articles without embeddings.
    
    Args:
        db: Database session
    """
    # Get articles without embeddings
    articles = db.query(Article).outerjoin(FAISSEmbedding).filter(FAISSEmbedding.id == None).all()
    
    if not articles:
        logger.info("No articles need embeddings")
        return
    
    logger.info(f"Generating embeddings for {len(articles)} articles...")
    
    # Prepare texts and IDs
    texts = [article.content for article in articles]
    article_ids = [article.id for article in articles]
    
    # Generate embeddings
    embeddings = faiss_service.generate_embeddings_batch(texts)
    
    # Add to FAISS index
    faiss_service.add_embeddings(embeddings, article_ids)
    
    # Store individual embeddings in database
    for i, article in enumerate(articles):
        embedding_bytes = embeddings[i].tobytes()
        
        faiss_embedding = FAISSEmbedding(
            embedding_vector=embedding_bytes,
            article_id=article.id
        )
        
        db.add(faiss_embedding)
        db.commit()
        db.refresh(faiss_embedding)
        
        # Update article with embedding_id
        article.embedding_id = faiss_embedding.id
        db.commit()
        
        logger.info(f"Stored embedding for article {article.id}")
    
    # Save FAISS index to disk
    os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
    faiss_service.save_index(settings.FAISS_INDEX_PATH)
    
    logger.info(f"Successfully generated and stored {len(articles)} embeddings")


def load_faiss_index_from_disk():
    """Load FAISS index from disk if it exists."""
    if os.path.exists(settings.FAISS_INDEX_PATH):
        logger.info(f"Loading FAISS index from {settings.FAISS_INDEX_PATH}")
        faiss_service.load_index(settings.FAISS_INDEX_PATH)
        stats = faiss_service.get_index_stats()
        logger.info(f"FAISS index loaded: {stats}")
    else:
        logger.info("No existing FAISS index found")


def main():
    """Main function to set up FAISS index."""
    logger.info("Starting FAISS index setup...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create sample articles
        logger.info("Creating sample articles...")
        article_ids = create_sample_articles(db)
        logger.info(f"Created/verified {len(article_ids)} articles")
        
        # Try to load existing index
        load_faiss_index_from_disk()
        
        # Generate embeddings
        generate_embeddings_for_articles(db)
        
        # Display final stats
        stats = faiss_service.get_index_stats()
        logger.info(f"FAISS setup complete: {json.dumps(stats, indent=2)}")
        
        # Test search
        logger.info("\nTesting semantic search...")
        test_query = "artificial intelligence in medicine"
        results = faiss_service.search(test_query, top_k=3)
        
        logger.info(f"\nSearch results for '{test_query}':")
        for article_id, distance in results:
            article = db.query(Article).filter(Article.id == article_id).first()
            if article:
                logger.info(f"  - {article.title} (distance: {distance:.4f})")
        
    except Exception as e:
        logger.error(f"Error during FAISS setup: {e}")
        raise
    finally:
        db.close()
    
    logger.info("\nFAISS index setup completed successfully!")


if __name__ == "__main__":
    main()
