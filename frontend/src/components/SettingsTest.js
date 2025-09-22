import React, { useState, useEffect } from 'react';

const SettingsTest = () => {
  const [settings, setSettings] = useState({
    list_worker_interval: 3600,
    detail_worker_interval: 900,
    parallel_tabs: 5,
    cloudflare_timeout: 60
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Load current settings
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/scraping/settings`);
      const data = await response.json();
      if (data && data.settings) {
        setSettings(data.settings);
        setMessage('✅ Settings loaded successfully');
      }
    } catch (error) {
      setMessage('❌ Failed to load settings: ' + error.message);
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/scraping/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
      });
      
      const data = await response.json();
      
      if (response.ok && data) {
        setMessage('✅ Settings saved successfully! ' + (data.note || ''));
      } else {
        setMessage('❌ Failed to save settings: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      setMessage('❌ Error saving settings: ' + error.message);
    }
    
    setLoading(false);
  };

  return (
    <div className="p-6 bg-slate-800 min-h-screen text-white">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">🔧 Settings Test Page</h1>
        
        <div className="bg-slate-700 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Scraping Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                List Worker Interval (seconds)
              </label>
              <input
                type="number"
                value={settings.list_worker_interval}
                onChange={(e) => setSettings(prev => ({...prev, list_worker_interval: parseInt(e.target.value) || 30}))}
                className="w-full px-3 py-2 bg-slate-600 rounded border border-slate-500 text-white"
                min="10"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Detail Worker Interval (seconds)
              </label>
              <input
                type="number"
                value={settings.detail_worker_interval}
                onChange={(e) => setSettings(prev => ({...prev, detail_worker_interval: parseInt(e.target.value) || 90}))}
                className="w-full px-3 py-2 bg-slate-600 rounded border border-slate-500 text-white"
                min="10"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Parallel Tabs
              </label>
              <input
                type="number"
                value={settings.parallel_tabs}
                onChange={(e) => setSettings(prev => ({...prev, parallel_tabs: parseInt(e.target.value) || 1}))}
                className="w-full px-3 py-2 bg-slate-600 rounded border border-slate-500 text-white"
                min="1"
                max="10"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Cloudflare Timeout (seconds)
              </label>
              <input
                type="number"
                value={settings.cloudflare_timeout}
                onChange={(e) => setSettings(prev => ({...prev, cloudflare_timeout: parseInt(e.target.value) || 60}))}
                className="w-full px-3 py-2 bg-slate-600 rounded border border-slate-500 text-white"
                min="10"
                max="300"
              />
            </div>
          </div>
          
          <div className="mt-6 flex gap-4">
            <button
              onClick={loadSettings}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white disabled:bg-gray-600"
            >
              Load Settings
            </button>
            
            <button
              onClick={saveSettings}
              disabled={loading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-white disabled:bg-gray-600"
            >
              {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
          
          {message && (
            <div className="mt-4 p-3 rounded bg-slate-600 text-sm">
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsTest;