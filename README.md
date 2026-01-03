# 📰 NewsLetterAI - AI-Powered News Aggregator

An intelligent news aggregation platform that fetches, analyzes, and delivers personalized news with bias detection, fact-checking, and AI-powered insights.

## ✨ Features

### Phase 1: Core Functionality
- 🔍 **Real-time News Search** - Fetch latest news using Serper API
- 📊 **Bias Detection** - Automated political bias scoring
- ✅ **Fact-Checking** - Google Fact Check API integration with heuristic fallback
- 🤖 **AI Summarization** - Article summaries using Groq LLM (Llama 3.1)
- ⭐ **User Ratings** - Rate and save favorite articles

### Phase 2: Advanced Features
- 🎯 **Hybrid Recommendations** - Combines content-based (FAISS) + collaborative filtering
- 🔬 **Deep Dive Analysis** - AI-generated in-depth article analysis
- 🎨 **Bias Filtering** - Filter news by balanced/biased content
- 🧠 **Semantic Search** - FAISS vector database for intelligent search

### Tech Stack

**Backend:**
- FastAPI (Python 3.9+)
- MySQL Database
- FAISS (Vector similarity search)
- Groq API (LLM)
- Serper API (News search)
- Google Fact Check API

**Frontend:**
- React.js
- Material-UI
- Axios

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Node.js 16+ and npm
- MySQL Server
- API Keys:
  - Serper API key (https://serper.dev)
  - Groq API key (https://console.groq.com)
  - Google Fact Check API key (optional - https://console.cloud.google.com)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/NewsLetterAi.git
cd NewsLetterAi
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Copy .env.example to .env and fill in your API keys
```

**Backend `.env` Configuration:**

```env
# Database
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/newsletterai

# API Keys
SERPER_API_KEY=your_serper_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_FACT_CHECK_API_KEY=your_google_api_key_here  # Optional

# Server
HOST=0.0.0.0
PORT=8000
```

**Create MySQL Database:**

```sql
CREATE DATABASE newsletterai;
```

#### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will run on http://localhost:3000

#### 4. Start Backend Server

```bash
# From backend directory
cd backend
python main_simple.py
```

Backend API will run on http://localhost:8000

## 📖 Usage

### 1. Search for News
- Enter a search query (e.g., "climate change", "technology")
- Click **SEARCH** to fetch real-time news articles
- Articles are automatically analyzed for bias and fact-checked

### 2. Filter by Bias
- Toggle **"Show balanced only"** to filter articles by bias level
- 🟢 Balanced (bias < 0.3)
- 🟡 Slightly Biased (0.3 - 0.6)
- 🔴 Biased (> 0.6)

### 3. Deep Dive Analysis
- Click **"Deep Dive"** on any article card
- AI generates comprehensive analysis with bullet points

### 4. Rate Articles
- Click stars to rate articles (1-5 stars)
- Ratings power the hybrid recommendation system

### 5. Get Recommendations
- After rating articles, click **"Recommended: 6"** chip
- View personalized article recommendations

## 🗂️ Project Structure

```
NewsLetterAi/
├── backend/
│   ├── app/
│   │   ├── models.py          # Database models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── config.py          # Configuration
│   │   └── services/
│   │       ├── serper_service.py      # News API
│   │       ├── groq_service.py        # LLM service
│   │       ├── faiss_service.py       # Vector search
│   │       └── fact_check_service.py  # Fact-checking
│   ├── main_simple.py         # Main API server
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
│
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/
│   │   │   └── Dashboard.js   # Main dashboard
│   │   └── services/
│   │       └── api.js         # API client
│   ├── package.json
│   └── .env
│
├── .gitignore
└── README.md
```

## 🔧 API Endpoints

### News & Search
- `GET /api/v1/fetch_news` - Fetch news from Serper API
- `POST /api/v1/search_articles` - Real-time search with Serper

### AI Features
- `GET /api/v1/deep_dive` - Generate deep analysis
- `GET /api/v1/recommendations` - Get personalized recommendations
- `POST /api/v1/generate_embeddings` - Build FAISS index

### User Interaction
- `POST /api/v1/feedback` - Submit article rating

## 🌟 Key Features Explained

### Bias Detection
Uses keyword-based heuristics to detect political bias:
- Left-leaning keywords: progressive, climate, inequality, regulation
- Right-leaning keywords: market, tax cut, deregulation, business
- Neutral keywords: technology, innovation, research, data

### Fact-Checking
1. **Google Fact Check API** - Primary method (requires API key)
2. **Heuristic Fallback** - Scans for risky keywords (rumor, fake, conspiracy)

### Hybrid Recommendations
- **70% Content-based** - FAISS semantic similarity on articles you liked
- **30% Collaborative** - What similar users rated highly

### Deep Dive
Uses Groq's Llama 3.1 model to generate:
- Comprehensive summary
- Key points in bullet format
- Related context and insights

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | MySQL connection string |
| `SERPER_API_KEY` | Yes | Serper API for news search |
| `GROQ_API_KEY` | Yes | Groq for AI summarization |
| `GOOGLE_FACT_CHECK_API_KEY` | No | Google Fact Check (optional) |

## 🛠️ Development

### Run Backend in Development Mode

```bash
cd backend
uvicorn main_simple:app --reload --host 0.0.0.0 --port 8000
```

### Run Frontend in Development Mode

```bash
cd frontend
npm start
```

### Build Frontend for Production

```bash
cd frontend
npm run build
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI, React, and AI**
