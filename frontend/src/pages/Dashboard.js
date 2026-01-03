import React, { useState, useEffect } from 'react';
import {
  Container, Paper, TextField, Button, Typography, Box, Card,
  CardContent, CardActions, Grid, Chip, AppBar, Toolbar, IconButton,
  InputAdornment, CircularProgress, Alert, Rating, Tabs, Tab, Dialog,
  DialogTitle, DialogContent, DialogActions, Tooltip, Switch, FormControlLabel,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import LogoutIcon from '@mui/icons-material/Logout';
import ArticleIcon from '@mui/icons-material/Article';
import ScienceIcon from '@mui/icons-material/Science';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { fetchNews, searchArticles, submitFeedback, deepDiveArticle, getRecommendations } from '../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [query, setQuery] = useState('');
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [ratings, setRatings] = useState({});
  const [balancedOnly, setBalancedOnly] = useState(false);
  const [deepDiveOpen, setDeepDiveOpen] = useState(false);
  const [deepDiveContent, setDeepDiveContent] = useState('');
  const [deepDiveLoading, setDeepDiveLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      navigate('/signup');
      return;
    }
    
    const parsedUser = JSON.parse(userData);
    setUser(parsedUser);
    loadInitialNews(parsedUser);
  }, [navigate]);

  const loadInitialNews = async (userData) => {
    try {
      setLoading(true);
      const response = await fetchNews(userData.id, null, 15, true);
      setArticles(response.articles || []);

      try {
        const recRes = await getRecommendations(userData.id, 6);
        setRecommendations(recRes.articles || []);
      } catch (recErr) {
        console.warn('Recommendations unavailable', recErr);
      }
      
      if (response.articles && response.articles.length > 0) {
        toast.success(`📰 Loaded ${response.articles.length} personalized articles!`);
      }
    } catch (err) {
      console.error('Error loading news:', err);
      toast.error('Failed to load articles');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      toast.warning('Please enter a search query');
      return;
    }

    setSearching(true);
    setTabValue(1);
    
    try {
      const response = await searchArticles({ query, top_k: 15, user_id: user?.id });
      setArticles(response.articles || []);
      
      if ((response.articles || []).length === 0) {
        toast.info('No articles found. Try different keywords!');
      } else {
        toast.success(`🔍 Found ${response.articles.length} articles!`);
      }
    } catch (err) {
      console.error('Search error:', err);
      toast.error('Search failed');
      setArticles([]);
    } finally {
      setSearching(false);
    }
  };

  const handleRefresh = async () => {
    if (!user) return;
    await loadInitialNews(user);
  };

  const handleRate = async (articleId, rating) => {
    if (!user) return;
    
    try {
      await submitFeedback({
        user_id: user.id,
        article_id: articleId,
        rating: rating,
      });
      setRatings({ ...ratings, [articleId]: rating });
      toast.success(`⭐ Rated with ${rating} stars!`);
    } catch (err) {
      console.error('Feedback error:', err);
      toast.error('Failed to save rating');
    }
  };

  const handleDeepDive = async (articleId) => {
    if (!user) return;
    try {
      setDeepDiveLoading(true);
      setDeepDiveOpen(true);
      const res = await deepDiveArticle(articleId);
      setDeepDiveContent(res.deep_dive_content || 'No deep dive content yet.');
    } catch (err) {
      console.error('Deep dive error:', err);
      setDeepDiveContent('Unable to load deep dive right now.');
    } finally {
      setDeepDiveLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    toast.success('Logged out successfully');
    navigate('/signup');
  };

  const getBiasIndicator = (score) => {
    if (score === null || score === undefined) {
      return { emoji: '⚪', label: 'Unknown', color: 'default' };
    }
    const absScore = Math.abs(score);
    if (absScore < 0.3) {
      return { emoji: '🟢', label: 'Balanced', color: 'success' };
    }
    if (absScore < 0.6) {
      return { emoji: '🟡', label: 'Slightly Biased', color: 'warning' };
    }
    return { emoji: '🔴', label: 'Biased', color: 'error' };
  };

  if (!user) return null;

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            📰 Newsletter AI
          </Typography>
          <Chip
            label={user.subscription_status === 'premium' ? '⭐ Premium' : '🆓 Free'}
            color={user.subscription_status === 'premium' ? 'success' : 'default'}
            sx={{ mr: 2 }}
          />
          <IconButton color="inherit" onClick={handleLogout} title="Logout">
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={2} sx={{ p: 3, mb: 4, background: 'rgba(102, 126, 234, 0.1)', borderRadius: 2 }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
            Welcome back, {user.email}! 👋
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Interests: <strong>{user.interests.join(', ')}</strong> | Reading Level: <strong>{user.reading_level}</strong>
          </Typography>
        </Paper>

        <Paper elevation={2} sx={{ p: 3, mb: 4, borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>🔍 Search Articles</Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              placeholder="Search: AI, climate, quantum..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color="action" />
                  </InputAdornment>
                ),
              }}
              size="small"
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={searching}
              sx={{ minWidth: 100 }}
            >
              {searching ? <CircularProgress size={24} /> : 'Search'}
            </Button>
          </Box>
        </Paper>

        {user.subscription_status !== 'premium' && (
          <Alert severity="info" sx={{ mb: 4, borderRadius: 2 }}>
            🚀 Upgrade to Premium for unlimited searches!
            <Button size="small" onClick={() => toast.info('Razorpay integration coming in Phase 3!')} sx={{ mt: 1 }}>
              Upgrade Now - ₹499/month
            </Button>
          </Alert>
        )}

        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="📰 Personalized Feed" icon={<RefreshIcon />} iconPosition="start" />
            <Tab label="🔎 Search Results" />
          </Tabs>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={balancedOnly}
                onChange={(e) => setBalancedOnly(e.target.checked)}
                color="success"
              />
            }
            label="Show balanced only"
          />
          {recommendations.length > 0 && (
            <Tooltip title="Hybrid recommendations (FAISS + collaborative)">
              <Chip
                icon={<ScienceIcon />}
                label={`Recommended: ${recommendations.length}`}
                color="secondary"
              />
            </Tooltip>
          )}
        </Box>

        {loading && tabValue === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (() => {
          const filtered = balancedOnly
            ? articles.filter((a) => Math.abs(a.bias_score ?? 1) < 0.3)
            : articles;
          if (filtered.length === 0) {
            return (
              <Alert severity="info">
                {tabValue === 0 ? (
                  <>
                    No articles loaded. Try{' '}
                    <Button size="small" onClick={handleRefresh}>
                      refreshing
                    </Button>
                  </>
                ) : (
                  'No search results. Try different keywords.'
                )}
              </Alert>
            );
          }
          return (
            <Grid container spacing={3}>
              {filtered.map((article) => {
                const bias = getBiasIndicator(article.bias_score);
                return (
                  <Grid item xs={12} md={6} lg={4} key={article.id}>
                    <Card
                      elevation={2}
                      sx={{
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        transition: 'all 0.2s',
                        '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 },
                      }}
                    >
                      <CardContent sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                          {article.title}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                          <Chip label={article.source} size="small" variant="outlined" color="primary" />
                          <Tooltip title={article.bias_explanation || 'Bias heuristic'}>
                            <Chip
                              icon={<span>{bias.emoji}</span>}
                              label={bias.label}
                              size="small"
                              color={bias.color}
                            />
                          </Tooltip>
                          {article.fact_check_status && (
                            <Chip
                              icon={<ArticleIcon />}
                              label={`Fact: ${article.fact_check_status}`}
                              size="small"
                              variant="outlined"
                              color={article.fact_check_status === 'verified' ? 'success' : 'warning'}
                            />
                          )}
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {(article.summary || article.content || '').substring(0, 180)}...
                        </Typography>
                      </CardContent>
                      <CardActions sx={{ flexDirection: 'column', alignItems: 'stretch', gap: 1.2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="caption">Rate:</Typography>
                          <Rating
                            value={ratings[article.id] || 0}
                            onChange={(e, v) => handleRate(article.id, v)}
                            size="small"
                          />
                        </Box>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleDeepDive(article.id)}
                          fullWidth
                        >
                          Deep Dive
                        </Button>
                        <Button
                          size="small"
                          variant="contained"
                          href={article.url}
                          target="_blank"
                          fullWidth
                        >
                          Read Full Article →
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          );
        })()}

        {articles.length > 0 && (
          <Box sx={{ mt: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Showing {articles.length} articles{balancedOnly ? ' (balanced only)' : ''}
            </Typography>
          </Box>
        )}

        <Dialog open={deepDiveOpen} onClose={() => setDeepDiveOpen(false)} fullWidth maxWidth="md">
          <DialogTitle>Deep Dive</DialogTitle>
          <DialogContent dividers>
            {deepDiveLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {deepDiveContent}
              </Typography>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeepDiveOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
};

export default Dashboard;
