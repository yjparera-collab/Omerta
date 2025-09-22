import React, { useState, useEffect } from 'react';
import { useIntelligence } from '../hooks/useIntelligence';

const SettingsPage = () => {
  const { apiCall } = useIntelligence();
  
  // Settings state
  const [settings, setSettings] = useState({
    list_worker_interval: 3600, // 1 hour in seconds
    detail_worker_interval: 900, // 15 minutes in seconds
    parallel_tabs: 5,
    cloudflare_timeout: 60
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Load current settings
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await apiCall('/api/scraping/settings');
      if (response && !response.error) {
        setSettings(response.settings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const response = await apiCall('/api/scraping/settings', {
        method: 'POST',
        body: JSON.stringify(settings)
      });
      
      if (response && !response.error) {
        setMessage('✅ Settings saved successfully! Changes will apply on next scraper restart.');
      } else {
        setMessage('❌ Failed to save settings');
      }
    } catch (error) {
      setMessage('❌ Error saving settings');
    }
    
    setLoading(false);
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const presetIntervals = [
    { label: '15 seconds', value: 15 },
    { label: '30 seconds', value: 30 },
    { label: '1 minute', value: 60 },
    { label: '5 minutes', value: 300 },
    { label: '15 minutes', value: 900 },
    { label: '30 minutes', value: 1800 },
    { label: '1 hour', value: 3600 },
    { label: '2 hours', value: 7200 },
  ];

  return (
    <div className="p-6 bg-slate-800 min-h-screen">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Scraping Settings</h1>
          <p className="text-slate-400">Configure intelligence gathering intervals and performance</p>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">⏱️ Timing Configuration</h2>
          
          {/* List Worker Settings */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              List Worker Interval (General Players)
            </label>
            <p className="text-xs text-slate-400 mb-3">
              How often to scrape the general player list (~1670 players)
            </p>
            
            <div className="grid grid-cols-4 gap-2 mb-3">
              {presetIntervals.map(preset => (
                <button
                  key={preset.value}
                  onClick={() => setSettings(prev => ({...prev, list_worker_interval: preset.value}))}
                  className={`px-3 py-2 rounded text-xs transition-colors ${
                    settings.list_worker_interval === preset.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-600 text-slate-300 hover:bg-slate-500'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            
            <div className="flex items-center gap-4">
              <input
                type="number"
                value={settings.list_worker_interval}
                onChange={(e) => setSettings(prev => ({...prev, list_worker_interval: parseInt(e.target.value) || 30}))}
                className="px-3 py-2 bg-slate-600 text-white rounded border border-slate-500 focus:border-blue-400 w-24"
                min="10"
              />
              <span className="text-slate-400 text-sm">
                seconds ({formatTime(settings.list_worker_interval)})
              </span>
            </div>
          </div>

          {/* Detail Worker Settings */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Detail Worker Interval (Detective Targets)
            </label>
            <p className="text-xs text-slate-400 mb-3">
              How often to scrape detective targets for detailed combat stats
            </p>
            
            <div className="grid grid-cols-4 gap-2 mb-3">
              {presetIntervals.slice(0, 6).map(preset => (
                <button
                  key={preset.value}
                  onClick={() => setSettings(prev => ({...prev, detail_worker_interval: preset.value}))}
                  className={`px-3 py-2 rounded text-xs transition-colors ${
                    settings.detail_worker_interval === preset.value
                      ? 'bg-green-600 text-white'
                      : 'bg-slate-600 text-slate-300 hover:bg-slate-500'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            
            <div className="flex items-center gap-4">
              <input
                type="number"
                value={settings.detail_worker_interval}
                onChange={(e) => setSettings(prev => ({...prev, detail_worker_interval: parseInt(e.target.value) || 90}))}
                className="px-3 py-2 bg-slate-600 text-white rounded border border-slate-500 focus:border-blue-400 w-24"
                min="10"
              />
              <span className="text-slate-400 text-sm">
                seconds ({formatTime(settings.detail_worker_interval)})
              </span>
            </div>
          </div>
        </div>

        {/* Performance Settings */}
        <div className="bg-slate-700/50 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">🚀 Performance Configuration</h2>
          
          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Parallel Browser Tabs
            </label>
            <p className="text-xs text-slate-400 mb-3">
              Number of simultaneous browser tabs for detective target scraping
            </p>
            
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="1"
                max="10"
                value={settings.parallel_tabs}
                onChange={(e) => setSettings(prev => ({...prev, parallel_tabs: parseInt(e.target.value)}))}
                className="flex-1 max-w-xs"
              />
              <div className="flex items-center gap-2">
                <span className="text-white font-semibold text-lg">{settings.parallel_tabs}</span>
                <span className="text-slate-400 text-sm">tabs</span>
              </div>
            </div>
            <div className="text-xs text-slate-500 mt-2">
              More tabs = faster scraping, but higher CPU/memory usage
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Cloudflare Timeout
            </label>
            <p className="text-xs text-slate-400 mb-3">
              Maximum seconds to wait for Cloudflare bypass
            </p>
            
            <div className="flex items-center gap-4">
              <input
                type="number"
                value={settings.cloudflare_timeout}
                onChange={(e) => setSettings(prev => ({...prev, cloudflare_timeout: parseInt(e.target.value) || 60}))}
                className="px-3 py-2 bg-slate-600 text-white rounded border border-slate-500 focus:border-blue-400 w-24"
                min="10"
                max="300"
              />
              <span className="text-slate-400 text-sm">seconds</span>
            </div>
          </div>
        </div>

        {/* Current Status */}
        <div className="bg-slate-700/50 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">📊 Current Status</h2>
          
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-slate-400 mb-1">List Worker</div>
              <div className="text-lg text-white">Every {formatTime(settings.list_worker_interval)}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">Detail Worker</div>
              <div className="text-lg text-white">Every {formatTime(settings.detail_worker_interval)}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">Parallel Tabs</div>
              <div className="text-lg text-white">{settings.parallel_tabs} simultaneous</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">Cloudflare Timeout</div>
              <div className="text-lg text-white">{settings.cloudflare_timeout}s</div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-slate-400">
            Changes require scraper restart to take effect
          </div>
          
          <button
            onClick={saveSettings}
            disabled={loading}
            className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
              loading 
                ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {loading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>

        {message && (
          <div className="mt-4 p-3 rounded-lg bg-slate-600 text-white text-sm">
            {message}
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsPage;