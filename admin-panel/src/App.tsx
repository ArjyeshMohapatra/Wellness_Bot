import { Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import ForgotPassword from './components/ForgotPassword';
import DeveloperView from './components/DeveloperView';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/developer" element={<DeveloperView />} />
      <Route path="/dashboard" element={<Dashboard />} />
      {/* Add more routes later */}
    </Routes>
  );
}

export default App;