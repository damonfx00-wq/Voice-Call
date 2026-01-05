import { useState, useEffect } from 'react';
import Header from './components/Header';
import VoiceCallInterface from './components/VoiceCallInterface';
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
    <div className="app">
      <Header onThemeToggle={toggleTheme} isDark={isDark} />
      <main className="main-content">
        <VoiceCallInterface />
      </main>
    </div>
  );
}

export default App;
