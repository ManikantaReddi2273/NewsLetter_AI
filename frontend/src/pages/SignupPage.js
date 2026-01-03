import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Typography,
  Box,
  Chip,
  OutlinedInput,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { signupUser, loginUser } from '../services/api';

const INTERESTS = [
  'Artificial Intelligence',
  'Technology',
  'Science',
  'Business',
  'Health',
  'Sports',
  'Entertainment',
  'Politics',
  'Environment',
  'Education',
];

const SignupPage = () => {
  const navigate = useNavigate();
  const [isLoginMode, setIsLoginMode] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    interests: [],
    reading_level: 'intermediate',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!formData.email) {
      setError('Email is required');
      return;
    }
    
    if (!isLoginMode && formData.interests.length === 0) {
      setError('Please select at least one interest');
      return;
    }

    setLoading(true);
    try {
      let response;
      
      if (isLoginMode) {
        // Login existing user
        response = await loginUser(formData.email);
        toast.success('Welcome back! 👋');
      } else {
        // Sign up new user
        response = await signupUser(formData);
        toast.success('Account created successfully! 🎉');
      }
      
      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify(response));
      
      // Navigate to dashboard
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    } catch (err) {
      console.error('Authentication error:', err);
      const errorMessage = err.response?.data?.detail || `Failed to ${isLoginMode ? 'login' : 'create account'}. Please try again.`;
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleInterestChange = (event) => {
    const {
      target: { value },
    } = event;
    setFormData({
      ...formData,
      interests: typeof value === 'string' ? value.split(',') : value,
    });
  };

  const handleRazorpayClick = () => {
    toast.info('Razorpay integration coming in Phase 3! 💳');
  };

  return (
    <Container maxWidth="sm" sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', py: 4 }}>
      <Paper elevation={10} sx={{ p: 4, width: '100%', borderRadius: 3 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary">
            📰 Newsletter AI
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {isLoginMode ? 'Welcome back! Sign in to your account' : 'Create your personalized AI-powered newsletter'}
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            margin="normal"
            required
            autoFocus
            placeholder="your.email@example.com"
          />

          {!isLoginMode && (
            <>
              <FormControl fullWidth margin="normal" required>
                <InputLabel>Interests</InputLabel>
                <Select
                  multiple
                  value={formData.interests}
                  onChange={handleInterestChange}
                  input={<OutlinedInput label="Interests" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" color="primary" />
                      ))}
                    </Box>
                  )}
                >
                  {INTERESTS.map((interest) => (
                    <MenuItem key={interest} value={interest}>
                      {interest}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl component="fieldset" margin="normal" sx={{ mt: 3 }}>
                <FormLabel component="legend">Reading Level</FormLabel>
                <RadioGroup
                  row
                  value={formData.reading_level}
                  onChange={(e) => setFormData({ ...formData, reading_level: e.target.value })}
                >
                  <FormControlLabel value="beginner" control={<Radio />} label="Beginner" />
                  <FormControlLabel value="intermediate" control={<Radio />} label="Intermediate" />
                  <FormControlLabel value="expert" control={<Radio />} label="Expert" />
                </RadioGroup>
              </FormControl>
            </>
          )}

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading}
            sx={{ mt: 3, mb: 2, py: 1.5 }}
          >
            {loading ? (isLoginMode ? 'Signing In...' : 'Creating Account...') : (isLoginMode ? 'Sign In 🚀' : 'Get Started 🚀')}
          </Button>

          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Button
              variant="text"
              onClick={() => setIsLoginMode(!isLoginMode)}
              sx={{ textTransform: 'none' }}
            >
              {isLoginMode ? "Don't have an account? Sign Up" : "Already have an account? Sign In"}
            </Button>
          </Box>

          {!isLoginMode && (
            <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100', borderRadius: 2, textAlign: 'center' }}>
              <Typography variant="body2" gutterBottom color="text.secondary">
                Want unlimited newsletters and deep dives?
              </Typography>
              <Button
                variant="outlined"
                color="primary"
                fullWidth
                onClick={handleRazorpayClick}
                sx={{ mt: 1 }}
              >
                Upgrade to Premium - ₹499/month
              </Button>
            </Box>
          )}
        </form>

        <Typography variant="caption" display="block" sx={{ mt: 3, textAlign: 'center', color: 'text.secondary' }}>
          {isLoginMode ? 'Welcome back to Newsletter AI' : 'By signing up, you agree to receive personalized newsletters'}
        </Typography>
      </Paper>
    </Container>
  );
};

export default SignupPage;
