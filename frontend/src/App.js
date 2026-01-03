import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import SignupPage from './pages/SignupPage';
import Dashboard from './pages/Dashboard';
import FeedbackPage from './pages/FeedbackPage';
import PaymentSuccess from './pages/PaymentSuccess';

function App() {
  return (
    <Router>
      <div className="App">
        <ToastContainer
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
        <Routes>
          <Route path="/" element={<Navigate to="/signup" replace />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/feedback/:articleId" element={<FeedbackPage />} />
          <Route path="/payment-success" element={<PaymentSuccess />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
