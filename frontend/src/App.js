import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import PlayersPage from './components/PlayersPage';
import FamiliesPage from './components/FamiliesPage';
import AnalyticsPage from './components/AnalyticsPage';
import SettingsPage from './components/SettingsPage';
import SettingsTest from './components/SettingsTest';
import Navigation from './components/Navigation';
import { IntelligenceProvider } from './hooks/useIntelligence';

function App() {
  return (
    <IntelligenceProvider>
      <Router>
        <div className="App min-h-screen bg-gray-900 text-white">
          <Navigation />
          <main className="container mx-auto px-4 py-6">
            <Routes>
              <Route path="/" element={<PlayersPage />} />
              <Route path="/players" element={<PlayersPage />} />
              <Route path="/families" element={<FamiliesPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/test-settings" element={<SettingsTest />} />
            </Routes>
          </main>
        </div>
      </Router>
    </IntelligenceProvider>
  );
}

export default App;