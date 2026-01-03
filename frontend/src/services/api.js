import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// User API
export const signupUser = async (userData) => {
  const response = await api.post('/signup', userData);
  return response.data;
};

export const loginUser = async (email) => {
  const response = await api.post('/login', { email });
  return response.data;
};

// Articles API
export const fetchNews = async (userId = null, query = null, limit = 10, applyFactCheck = false) => {
  const params = {};
  if (userId) params.user_id = userId;
  if (query) params.query = query;
  if (limit) params.limit = limit;
  if (applyFactCheck) params.apply_fact_check = true;
  
  const response = await api.get('/fetch_news', { params });
  return response.data;
};

export const searchArticles = async (searchData) => {
  const response = await api.post('/search_articles', searchData);
  return response.data;
};

export const getRecommendations = async (userId, k = 5) => {
  const response = await api.get('/recommendations', { params: { user_id: userId, k } });
  return response.data;
};

export const deepDiveArticle = async (articleId) => {
  const response = await api.get('/deep_dive', { params: { article_id: articleId } });
  return response.data;
};

export const summarizeArticle = async (articleId) => {
  const response = await api.post('/summarize', null, {
    params: { article_id: articleId }
  });
  return response.data;
};

export const getArticle = async (articleId) => {
  const response = await api.get(`/articles/${articleId}`);
  return response.data;
};

// Feedback API
export const submitFeedback = async (feedbackData) => {
  const response = await api.post('/feedback', feedbackData);
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
