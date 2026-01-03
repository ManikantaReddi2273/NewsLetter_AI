import React, { useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useNavigate } from 'react-router-dom';

const PaymentSuccess = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Update user subscription status in localStorage
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
      user.subscription_status = 'premium';
      localStorage.setItem('user', JSON.stringify(user));
    }
  }, []);

  return (
    <Container maxWidth="sm" sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', py: 4 }}>
      <Paper elevation={10} sx={{ p: 4, width: '100%', borderRadius: 3 }}>
        <Box sx={{ textAlign: 'center' }}>
          <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
          
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary">
            Payment Successful! 🎉
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Welcome to Premium! You now have access to:
          </Typography>

          <Box sx={{ textAlign: 'left', mb: 4 }}>
            <Typography variant="body1" gutterBottom>
              ✅ Unlimited newsletter searches
            </Typography>
            <Typography variant="body1" gutterBottom>
              ✅ Deep dive analysis with arXiv papers
            </Typography>
            <Typography variant="body1" gutterBottom>
              ✅ Advanced bias detection
            </Typography>
            <Typography variant="body1" gutterBottom>
              ✅ Priority email support
            </Typography>
          </Box>

          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={() => navigate('/dashboard')}
            sx={{ mb: 2 }}
          >
            Go to Dashboard
          </Button>

          <Typography variant="caption" display="block" color="text.secondary">
            Your subscription will be billed monthly
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default PaymentSuccess;
