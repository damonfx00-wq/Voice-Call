import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Header from './components/Header';
import VoiceCallInterface from './components/VoiceCallInterface';
import AdminDashboard from './pages/AdminDashboard';
import './App.css';

function App() {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches);
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  return (
    <Router>
      <Routes>
        {/* Admin Dashboard Route */}
        <Route path="/admin" element={<AdminDashboard />} />

        {/* Main Voice Call Interface */}
        <Route
          path="/"
          element={
            <div className="app">
              <Header onThemeToggle={toggleTheme} isDark={isDark} />
              <main className="main-content">
                <VoiceCallInterface />
              </main>
            </div>
          }
        />

        {/* Redirect any unknown routes to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
