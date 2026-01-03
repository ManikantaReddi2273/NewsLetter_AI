# Newsletter AI Backend

AI-powered newsletter generation with semantic search, personalization, and summarization.

## 🚀 Features

- **User Signup**: Create accounts with email, interests, and reading level preferences
- **Semantic Search**: FAISS-powered vector search for article discovery
- **AI Summarization**: Groq API for intelligent article summarization
- **Redis Caching**: High-performance caching for search results
- **RESTful API**: FastAPI-based backend with comprehensive documentation

## 📋 Prerequisites

- Python 3.9+
- MySQL 8.0+
- Redis (optional, for caching)
- API Keys:
  - Groq API key (for summarization)
  - Serper API key (for news fetching - Phase 2)

## 🛠️ Installation

### 1. Clone the repository

```bash
cd backend
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=newsletter_db

# API Keys
GROQ_API_KEY=your_groq_api_key_here

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 5. Set up MySQL database

```sql
CREATE DATABASE newsletter_db;
```

The tables will be created automatically when you run the application.

### 6. Initialize FAISS index with sample data

```bash
python scripts/setup_faiss_index.py
```

This will:
- Create sample articles in the database
- Generate embeddings using `all-MiniLM-L6-v2`
- Build FAISS index
- Save index to `./data/faiss_index.pkl`

## 🚀 Running the Application

### Development mode (with auto-reload)

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### User Management

#### POST `/api/v1/signup`
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "interests": ["AI", "Technology", "Science"],
  "reading_level": "intermediate"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "interests": ["AI", "Technology", "Science"],
  "reading_level": "intermediate",
  "subscription_status": "free"
}
```

### Search

#### POST `/api/v1/search_articles`
Semantic search for articles using FAISS.

**Request:**
```json
{
  "query": "AI ethics",
  "user_id": 1,
  "top_k": 5
}
```

**Response:**
```json
{
  "articles": [
    {
      "id": 4,
      "title": "Ethics in AI Development",
      "url": "https://example.com/ai-ethics-1",
      "summary": null,
      "source": "AI Ethics Journal",
      "bias_score": null
    }
  ],
  "query": "AI ethics",
  "total_results": 1
}
```

### Summarization

#### POST `/api/v1/summarize`
Summarize an article using Groq API.

**Request:**
```json
{
  "article_url": "https://example.com/article",
  "reading_level": "beginner"
}
```

**Response:**
```json
{
  "summary": [
    "Article introduces key concept of AI in simple terms",
    "Discusses practical applications in everyday life",
    "Explains future implications and benefits"
  ],
  "word_count": 45,
  "reading_level": "beginner"
}
```

### Feedback

#### POST `/api/v1/feedback`
Submit user rating for an article.

**Request:**
```json
{
  "user_id": 1,
  "article_id": 4,
  "rating": 5
}
```

### Health Check

#### GET `/api/v1/health`
Check API health and FAISS index status.

**Response:**
```json
{
  "status": "healthy",
  "faiss_index": {
    "total_vectors": 10,
    "dimension": 384,
    "index_type": "IndexFlatL2",
    "articles_indexed": 10
  }
}
```

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database connection
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── routes.py           # API endpoints
│   └── services/
│       ├── __init__.py
│       ├── faiss_service.py    # FAISS vector search
│       ├── groq_service.py     # Groq summarization
│       └── redis_service.py    # Redis caching
├── scripts/
│   └── setup_faiss_index.py    # Initialize FAISS
├── data/                   # FAISS index storage
├── logs/                   # Application logs
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## 🧪 Testing

### Test semantic search

```bash
# After running setup_faiss_index.py
curl -X POST http://localhost:8000/api/v1/search_articles \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence healthcare",
    "user_id": 1,
    "top_k": 3
  }'
```

### Test summarization

```bash
curl -X POST http://localhost:8000/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "article_url": "https://example.com/ai-healthcare-1",
    "reading_level": "beginner"
  }'
```

## 🔧 Configuration

### FAISS Settings

- **Dimension**: 384 (for all-MiniLM-L6-v2)
- **Index Type**: IndexFlatL2 (exact L2 distance)
- **Top K Results**: 5 (default, configurable)

### Redis Caching

- **Cache TTL**: 3600 seconds (1 hour)
- **Cached Data**: Search results, recommendations

### Database Indexes

For optimal performance, create these indexes:

```sql
CREATE INDEX idx_articles_embedding ON articles(embedding_id);
CREATE INDEX idx_user_feedback_rating ON user_feedback(user_id, article_id, rating);
CREATE INDEX idx_users_email ON users(email);
```

## 📝 Next Steps

### Phase 2: Advanced Personalization
- Hybrid recommendations (FAISS + collaborative filtering)
- Misinformation detection (Google Fact Check API)
- Bias analysis (Gemini)
- Deep dive mode (arXiv integration)

### Phase 3: Monetization
- Razorpay integration
- Subscription tiers
- B2B SaaS features

### Phase 4: Deployment
- Docker containerization
- AWS ECS deployment
- S3 for FAISS persistence
- CloudFront CDN

## 🐛 Troubleshooting

### Database Connection Error

```bash
# Check MySQL is running
mysql -u root -p

# Create database if needed
CREATE DATABASE newsletter_db;
```

### Redis Connection Warning

If Redis is not available, the app will still work but without caching:
```
Could not connect to Redis: Error connecting to localhost:6379. Caching will be disabled.
```

### FAISS Index Not Found

Run the setup script:
```bash
python scripts/setup_faiss_index.py
```

## 📄 License

MIT License

## 👥 Contributors

- Your Name

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- FAISS for vector similarity search
- Groq for LLM API
- Sentence Transformers for embeddings
