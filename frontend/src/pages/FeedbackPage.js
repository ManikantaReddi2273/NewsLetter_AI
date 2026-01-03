import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Rating,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { submitFeedback } from '../services/api';

const FeedbackPage = () => {
  const { articleId } = useParams();
  const navigate = useNavigate();
  const [rating, setRating] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) {
      toast.warning('Please select a rating');
      return;
    }

    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
      toast.error('Please login first');
      navigate('/signup');
      return;
    }

    setLoading(true);
    try {
      await submitFeedback({
        user_id: user.id,
        article_id: parseInt(articleId),
        rating: rating,
      });

      toast.success('Thank you for your feedback! ⭐');
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    } catch (err) {
      console.error('Feedback error:', err);
      toast.error('Failed to submit feedback. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', py: 4 }}>
      <Paper elevation={10} sx={{ p: 4, width: '100%', borderRadius: 3 }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary">
            Rate This Article
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Your feedback helps us personalize your newsletter
          </Typography>

          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
            <Rating
              name="article-rating"
              value={rating}
              onChange={(event, newValue) => {
                setRating(newValue);
              }}
              size="large"
              sx={{ fontSize: '3rem' }}
            />
          </Box>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            {rating === 0 && 'Select a rating'}
            {rating === 1 && 'Not helpful'}
            {rating === 2 && 'Somewhat helpful'}
            {rating === 3 && 'Helpful'}
            {rating === 4 && 'Very helpful'}
            {rating === 5 && 'Extremely helpful!'}
          </Typography>

          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleSubmit}
            disabled={loading || rating === 0}
            sx={{ mt: 4 }}
          >
            {loading ? 'Submitting...' : 'Submit Feedback'}
          </Button>

          <Button
            variant="text"
            fullWidth
            onClick={() => navigate('/dashboard')}
            sx={{ mt: 2 }}
          >
            Back to Dashboard
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default FeedbackPage;
