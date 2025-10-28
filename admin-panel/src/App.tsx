import { Routes, Route } from 'react-router-dom';
import { Suspense, lazy } from 'react';

// Lazy load components for code splitting
const Login = lazy(() => import('./components/Login'));
const ForgotPassword = lazy(() => import('./components/ForgotPassword'));
const DeveloperView = lazy(() => import('./components/DeveloperView'));
const Dashboard = lazy(() => import('./components/Dashboard'));

function App() {
  return (
    <Suspense fallback={<div className="d-flex justify-content-center align-items-center min-vh-100">
      <div className="spinner-border text-primary" role="status">
        <span className="visually-hidden">Loading...</span>
      </div>
    </div>}>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/developer" element={<DeveloperView />} />
        <Route path="/dashboard" element={<Dashboard />} />
        {/* Add more routes later */}
      </Routes>
    </Suspense>
  );
}

export default App;