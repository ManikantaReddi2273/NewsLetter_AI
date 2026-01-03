"""Initialize database tables."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, engine
from app.models import User, Article, FAISSEmbedding, UserFeedback
from sqlalchemy import text

print("🚀 Initializing database tables...")

try:
    # Drop all tables first to ensure clean state
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(text("DROP TABLE IF EXISTS user_feedback"))
        conn.execute(text("DROP TABLE IF EXISTS faiss_embeddings"))
        conn.execute(text("DROP TABLE IF EXISTS articles"))
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
    
    print("✅ Dropped existing tables")
    
    # Create all tables
    init_db()
    
    print("✅ Database tables created successfully!")
    print("\n📋 Tables created:")
    print("  - users")
    print("  - articles")
    print("  - faiss_embeddings")
    print("  - user_feedback")
    
    print("\n✅ Database is ready for use!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
