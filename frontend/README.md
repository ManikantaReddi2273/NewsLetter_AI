# Newsletter AI - Frontend

React frontend for the AI-powered Newsletter platform.

## 🚀 Features

- **User Signup**: Email-based registration with interest selection
- **Semantic Search**: AI-powered article search using FAISS
- **Article Feedback**: Star rating system for personalization
- **Premium CTA**: Razorpay integration placeholder
- **Responsive Design**: Material-UI components

## 📋 Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000`

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Configure Environment** (optional):
   Create `.env` file:
   ```env
   REACT_APP_API_URL=http://localhost:8000/api/v1
   ```

## 🚀 Running the Application

### Development Mode

```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
```

## 📁 Project Structure

```
src/
├── pages/
│   ├── SignupPage.js       # User registration
│   ├── Dashboard.js        # Main dashboard with search
│   ├── FeedbackPage.js     # Article rating
│   └── PaymentSuccess.js   # Payment confirmation
├── services/
│   └── api.js              # Backend API integration
├── App.js                  # Main app with routing
└── index.js                # Entry point
```

## 🎯 Pages

### 1. Signup Page (`/signup`)
- Email input field
- Multi-select interests dropdown
- Reading level selection (beginner/intermediate/expert)
- Premium upgrade CTA (placeholder)

### 2. Dashboard (`/dashboard`)
- Semantic search bar
- Search results with article cards
- Article source badges
- Bias indicators (🟢🟡🔴)
- Feedback button for each article
- Premium upgrade banner (for free users)

### 3. Feedback Page (`/feedback/:articleId`)
- Star rating component (1-5 stars)
- Submit feedback to backend
- Improves recommendation algorithm

### 4. Payment Success (`/payment-success`)
- Confirmation page (placeholder)
- Premium features list
- Redirect to dashboard

## 🔌 API Integration

All API calls are handled through `src/services/api.js`:

- **POST /signup** - Create user account
- **POST /search_articles** - Semantic search
- **POST /feedback** - Submit article rating
- **GET /articles/:id** - Get article details
- **POST /summarize** - Get article summary

## 🎨 UI Components

Built with Material-UI:
- **TextField**: Email, search inputs
- **Select**: Multi-select for interests
- **RadioGroup**: Reading level selection
- **Card**: Article display
- **Rating**: Star rating component
- **Chip**: Tags and badges
- **AppBar**: Navigation header

## 🧪 Testing

### Manual Testing Checklist

- [ ] Sign up with valid email and interests
- [ ] Search for articles (e.g., "AI ethics")
- [ ] View article details
- [ ] Submit feedback rating
- [ ] Click Premium upgrade (shows alert)
- [ ] Logout and login flow

### API Testing

Ensure backend is running:
```bash
# In backend directory
python main.py
```

## 📝 Next Steps (Phase 2 & 3)

- [ ] Deep Dive modal for detailed analysis
- [ ] Bias explanation tooltips
- [ ] Live Razorpay payment integration
- [ ] B2B pricing page
- [ ] Email newsletter preview
- [ ] User profile settings

## 🐛 Troubleshooting

### CORS Errors
If you see CORS errors, ensure the backend has CORS enabled for `http://localhost:3000`:

```python
# In backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    ...
)
```

### API Connection Failed
1. Check backend is running on port 8000
2. Verify API URL in `package.json` proxy or `.env`
3. Check browser console for errors

### Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📄 License

MIT License
