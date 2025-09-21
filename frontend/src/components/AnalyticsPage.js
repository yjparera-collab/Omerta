import React, { useState, useEffect } from 'react';
import { useIntelligence } from '../hooks/useIntelligence';

const AnalyticsPage = () => {
  const { systemStatus } = useIntelligence();
  const [analyticsData, setAnalyticsData] = useState({
    kills: [],
    shots: [],
    activities: []
  });
  const [timeRange, setTimeRange] = useState('24h');
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${BACKEND_URL}/api/analytics?time_range=${timeRange}`);
      
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const timeRangeOptions = [
    { value: '1h', label: 'Last Hour' },
    { value: '6h', label: 'Last 6 Hours' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' }
  ];

  const getActivityIcon = (type) => {
    switch (type) {
      case 'kill': return '🎯';
      case 'shot': return '🔫';
      case 'plating': return '🛡️';
      default: return '📊';
    }
  };

  const getActivityColor = (type) => {
    switch (type) {
      case 'kill': return 'from-red-500 to-red-600';
      case 'shot': return 'from-yellow-500 to-orange-600';
      case 'plating': return 'from-blue-500 to-blue-600';
      default: return 'from-slate-500 to-slate-600';
    }
  };

  const formatActivityMessage = (activity) => {
    switch (activity.type) {
      case 'kill':
        return `${activity.player} (${activity.family}) eliminated a target`;
      case 'shot':
        return `${activity.player} (${activity.family}) fired ${activity.shots} shots`;
      case 'plating':
        return `${activity.player} (${activity.family}) plating changed to ${activity.to}`;
      default:
        return 'Unknown activity';
    }
  };

  const totalKills = analyticsData.kills.reduce((sum, item) => sum + (item.value || 0), 0);
  const totalShots = analyticsData.shots.reduce((sum, item) => sum + (item.value || 0), 0);
  const averageKillsPerHour = analyticsData.kills.length > 0 ? 
    (totalKills / Math.max(analyticsData.kills.length, 1)).toFixed(1) : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-white mb-3">
                <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 text-transparent bg-clip-text">
                  War Analytics Center
                </span>
              </h1>
              <p className="text-slate-400 text-lg">Real-time combat intelligence and strategic analysis</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="bg-slate-700/50 text-white px-6 py-3 rounded-lg border border-slate-600/50 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 transition-all"
              >
                {timeRangeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              
              <button
                onClick={fetchAnalytics}
                disabled={loading}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl flex items-center space-x-2"
              >
                <span className={loading ? 'animate-spin' : ''}>{loading ? '🔄' : '↻'}</span>
                <span>Refresh Intel</span>
              </button>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-red-900/40 to-red-800/40 backdrop-blur-sm rounded-xl border border-red-500/30 p-6 shadow-lg shadow-red-500/10">
            <div className="flex items-center justify-between mb-4">
              <div className="text-4xl">🎯</div>
              <div className="text-red-400 text-sm font-semibold tracking-wider">ELIMINATIONS</div>
            </div>
            <div className="text-3xl font-bold text-white mb-2">{totalKills}</div>
            <div className="text-red-200 text-sm">Total Kills</div>
            <div className="text-xs text-red-300 mt-2 opacity-75">{averageKillsPerHour}/hr average</div>
          </div>
          
          <div className="bg-gradient-to-br from-yellow-900/40 to-orange-800/40 backdrop-blur-sm rounded-xl border border-yellow-500/30 p-6 shadow-lg shadow-yellow-500/10">
            <div className="flex items-center justify-between mb-4">
              <div className="text-4xl">🔫</div>
              <div className="text-yellow-400 text-sm font-semibold tracking-wider">FIREPOWER</div>
            </div>
            <div className="text-3xl font-bold text-white mb-2">{totalShots}</div>
            <div className="text-yellow-200 text-sm">Shots Fired</div>
            <div className="text-xs text-yellow-300 mt-2 opacity-75">
              {analyticsData.shots.length > 0 ? 
                (totalShots / Math.max(analyticsData.shots.length, 1)).toFixed(1) : 0}/hr rate
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/40 backdrop-blur-sm rounded-xl border border-blue-500/30 p-6 shadow-lg shadow-blue-500/10">
            <div className="flex items-center justify-between mb-4">
              <div className="text-4xl">📡</div>
              <div className="text-blue-400 text-sm font-semibold tracking-wider">INTELLIGENCE</div>
            </div>
            <div className="text-3xl font-bold text-white mb-2">{analyticsData.activities.length}</div>
            <div className="text-blue-200 text-sm">Intel Events</div>
            <div className="text-xs text-blue-300 mt-2 opacity-75">Last {timeRange} period</div>
          </div>
          
          <div className="bg-gradient-to-br from-emerald-900/40 to-emerald-800/40 backdrop-blur-sm rounded-xl border border-emerald-500/30 p-6 shadow-lg shadow-emerald-500/10">
            <div className="flex items-center justify-between mb-4">
              <div className="text-4xl">👥</div>
              <div className="text-emerald-400 text-sm font-semibold tracking-wider">SURVEILLANCE</div>
            </div>
            <div className="text-3xl font-bold text-white mb-2">
              {systemStatus.scraping_service?.cached_players || 0}
            </div>
            <div className="text-emerald-200 text-sm">Active Targets</div>
            <div className="text-xs text-emerald-300 mt-2 opacity-75">
              Queue: {systemStatus.scraping_service?.queue_size || 0}
            </div>
          </div>
        </div>

        {/* Analytics Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Kill Trends */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
            <div className="p-6 border-b border-slate-700/50">
              <h3 className="text-xl font-bold text-white mb-2 flex items-center">
                <span className="text-red-400 mr-3">🎯</span>
                Elimination Trends
              </h3>
              <p className="text-slate-400 text-sm">Combat effectiveness analysis</p>
            </div>
            
            <div className="p-6">
              {analyticsData.kills.length > 0 ? (
                <div className="space-y-4">
                  {analyticsData.kills.slice(-10).map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600/30 hover:bg-slate-700/40 transition-all">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                        <div className="text-sm text-slate-300">
                          {new Date(item.time).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-red-400 font-bold text-lg">{item.value} eliminations</div>
                        <div className="w-24 bg-slate-600 rounded-full h-3 overflow-hidden">
                          <div 
                            className="bg-gradient-to-r from-red-500 to-red-600 h-3 rounded-full transition-all duration-500" 
                            style={{
                              width: `${Math.min((item.value / Math.max(...analyticsData.kills.map(k => k.value), 1)) * 100, 100)}%`
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📈</div>
                  <div className="text-slate-400 text-lg font-medium mb-2">No Elimination Data</div>
                  <div className="text-slate-500 text-sm">Combat activity will appear here when detected</div>
                </div>
              )}
            </div>
          </div>

          {/* Shot Activity */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
            <div className="p-6 border-b border-slate-700/50">
              <h3 className="text-xl font-bold text-white mb-2 flex items-center">
                <span className="text-yellow-400 mr-3">🔫</span>
                Firepower Analysis
              </h3>
              <p className="text-slate-400 text-sm">Ammunition expenditure tracking</p>
            </div>
            
            <div className="p-6">
              {analyticsData.shots.length > 0 ? (
                <div className="space-y-4">
                  {analyticsData.shots.slice(-10).map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600/30 hover:bg-slate-700/40 transition-all">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                        <div className="text-sm text-slate-300">
                          {new Date(item.time).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-yellow-400 font-bold text-lg">{item.value} shots</div>
                        <div className="w-24 bg-slate-600 rounded-full h-3 overflow-hidden">
                          <div 
                            className="bg-gradient-to-r from-yellow-500 to-orange-600 h-3 rounded-full transition-all duration-500" 
                            style={{
                              width: `${Math.min((item.value / Math.max(...analyticsData.shots.map(s => s.value), 1)) * 100, 100)}%`
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📊</div>
                  <div className="text-slate-400 text-lg font-medium mb-2">No Firepower Data</div>
                  <div className="text-slate-500 text-sm">Shot activity will be tracked here</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recent Activity Feed */}
        <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
          <div className="p-6 border-b border-slate-700/50">
            <h3 className="text-xl font-bold text-white mb-2 flex items-center">
              <span className="text-purple-400 mr-3 animate-pulse">⚡</span>
              Real-Time Operations Feed
            </h3>
            <p className="text-slate-400 text-sm">Live intelligence stream from the battlefield</p>
          </div>
          
          <div className="p-6">
            {analyticsData.activities.length > 0 ? (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {analyticsData.activities.map((activity, index) => (
                  <div key={index} className="flex items-center space-x-4 p-4 bg-slate-700/20 rounded-lg border border-slate-600/30 hover:bg-slate-700/30 transition-all">
                    <div className={`p-3 rounded-full bg-gradient-to-r ${getActivityColor(activity.type)} shadow-lg`}>
                      <span className="text-xl">{getActivityIcon(activity.type)}</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-white text-sm leading-relaxed">
                        {formatActivityMessage(activity)}
                      </div>
                      <div className="text-xs text-slate-400 mt-1 flex items-center">
                        <span className="mr-2">⏰</span>
                        {activity.time}
                      </div>
                    </div>
                    {activity.family && (
                      <div className="text-xs">
                        <span className="bg-slate-600/50 text-slate-300 px-3 py-1 rounded-full font-medium">
                          {activity.family}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <div className="text-8xl mb-6">🕵️</div>
                <div className="text-2xl text-slate-300 font-bold mb-3">Intelligence Monitoring Active</div>
                <div className="text-slate-400 text-lg mb-6">Scanning for battlefield activity...</div>
                <div className="flex justify-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-pink-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* System Performance Dashboard */}
        <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
          <div className="p-6 border-b border-slate-700/50">
            <h3 className="text-xl font-bold text-white mb-2 flex items-center">
              <span className="text-green-400 mr-3">🔧</span>
              System Performance Matrix
            </h3>
            <p className="text-slate-400 text-sm">Real-time operational status and diagnostics</p>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-700/30 rounded-lg border border-slate-600/30 p-6">
                <h4 className="font-bold text-white mb-4 flex items-center">
                  <span className="text-blue-400 mr-2">🕸️</span>
                  Scraping Engine
                </h4>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Status:</span>
                    <span className={`font-semibold px-2 py-1 rounded text-xs ${
                      systemStatus.scraping_service ? 'text-emerald-400 bg-emerald-900/30' : 'text-red-400 bg-red-900/30'
                    }`}>
                      {systemStatus.scraping_service ? 'OPERATIONAL' : 'OFFLINE'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Cached Targets:</span>
                    <span className="text-white font-semibold">{systemStatus.scraping_service?.cached_players || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Processing Queue:</span>
                    <span className="text-white font-semibold">{systemStatus.scraping_service?.queue_size || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Families Tracked:</span>
                    <span className="text-white font-semibold">{systemStatus.scraping_service?.target_families || 0}</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-700/30 rounded-lg border border-slate-600/30 p-6">
                <h4 className="font-bold text-white mb-4 flex items-center">
                  <span className="text-purple-400 mr-2">🗄️</span>
                  Database Systems
                </h4>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">MongoDB:</span>
                    <span className={`font-semibold px-2 py-1 rounded text-xs ${
                      systemStatus.database?.connected ? 'text-emerald-400 bg-emerald-900/30' : 'text-red-400 bg-red-900/30'
                    }`}>
                      {systemStatus.database?.connected ? 'CONNECTED' : 'OFFLINE'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">User Profiles:</span>
                    <span className="text-white font-semibold">{systemStatus.database?.preferences_count || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Cache Engine:</span>
                    <span className="text-emerald-400 font-semibold">SQLite Active</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-700/30 rounded-lg border border-slate-600/30 p-6">
                <h4 className="font-bold text-white mb-4 flex items-center">
                  <span className="text-yellow-400 mr-2">📡</span>
                  Communication Hub
                </h4>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">WebSocket Clients:</span>
                    <span className="text-white font-semibold">{systemStatus.websocket_connections || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">API Status:</span>
                    <span className="text-emerald-400 font-semibold">ONLINE</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Last Sync:</span>
                    <span className="text-white font-semibold">
                      {systemStatus.scraping_service?.last_list_update ? 
                        new Date(systemStatus.scraping_service.last_list_update).toLocaleTimeString() : 
                        'Never'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;