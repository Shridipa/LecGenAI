import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Results from './pages/Results';
import History from './pages/History';
import Settings from './pages/Settings';
import Pricing from './pages/Pricing';
import PYQAnalytics from './pages/PYQAnalytics';
import { SettingsProvider } from './context/SettingsContext';
import './index.css';

const App = () => {
  return (
    <SettingsProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/results" element={<Results />} />
          <Route path="/history" element={<History />} />
          <Route path="/pyq-analysis" element={<PYQAnalytics />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/pricing" element={<Pricing />} />
          {/* Fallback to home */}
          <Route path="*" element={<Home />} />
        </Routes>
      </Router>
    </SettingsProvider>
  );
};

export default App;
