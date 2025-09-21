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
    const interval = setInterval(fetchAnalytics, 30000); // Refresh every 30 seconds
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
      case 'kill': return 'text-red-400';
      case 'shot': return 'text-yellow-400';
      case 'plating': return 'text-blue-400';
      default: return 'text-gray-400';
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
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">📊 War Analytics Dashboard</h1>
            <p className="text-gray-400 mt-1">Real-time combat intelligence and trend analysis</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-gray-700 text-white px-4 py-2 rounded-md"
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
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md"
            >
              {loading ? '🔄' : '↻'} Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-red-900 rounded-lg p-6">
          <div className="text-3xl font-bold text-white">{totalKills}</div>
          <div className="text-red-200">Total Kills</div>
          <div className="text-sm text-red-300 mt-1">{averageKillsPerHour}/hr avg</div>
        </div>
        
        <div className="bg-yellow-900 rounded-lg p-6">
          <div className="text-3xl font-bold text-white">{totalShots}</div>
          <div className="text-yellow-200">Total Shots Fired</div>
          <div className="text-sm text-yellow-300 mt-1">
            {analyticsData.shots.length > 0 ? 
              (totalShots / Math.max(analyticsData.shots.length, 1)).toFixed(1) : 0}/hr avg
          </div>
        </div>
        
        <div className="bg-blue-900 rounded-lg p-6">
          <div className="text-3xl font-bold text-white">{analyticsData.activities.length}</div>
          <div className="text-blue-200">Intelligence Events</div>
          <div className="text-sm text-blue-300 mt-1">Last {timeRange}</div>
        </div>
        
        <div className="bg-green-900 rounded-lg p-6">
          <div className="text-3xl font-bold text-white">
            {systemStatus.scraping_service?.cached_players || 0}
          </div>
          <div className="text-green-200">Players Tracked</div>
          <div className="text-sm text-green-300 mt-1">
            Queue: {systemStatus.scraping_service?.queue_size || 0}
          </div>
        </div>
      </div>

      {/* Charts and Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Kill Trends */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">🎯 Kill Activity Trends</h3>
          
          {analyticsData.kills.length > 0 ? (
            <div className="space-y-3">
              {analyticsData.kills.slice(-10).map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                  <div className="text-sm text-gray-300">
                    {new Date(item.time).toLocaleString()}
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="text-red-400 font-bold">{item.value} kills</div>
                    <div className="w-20 bg-gray-600 rounded-full h-2">
                      <div 
                        className="bg-red-500 h-2 rounded-full" 
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
            <div className="text-center py-8 text-gray-400">
              <div className="text-4xl mb-2">📈</div>
              <div>No kill data available for selected time range</div>
            </div>
          )}
        </div>

        {/* Shot Activity */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">🔫 Shot Activity Trends</h3>
          
          {analyticsData.shots.length > 0 ? (
            <div className="space-y-3">
              {analyticsData.shots.slice(-10).map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                  <div className="text-sm text-gray-300">
                    {new Date(item.time).toLocaleString()}
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="text-yellow-400 font-bold">{item.value} shots</div>
                    <div className="w-20 bg-gray-600 rounded-full h-2">
                      <div 
                        className="bg-yellow-500 h-2 rounded-full" 
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
            <div className="text-center py-8 text-gray-400">
              <div className="text-4xl mb-2">📊</div>
              <div>No shot data available for selected time range</div>
            </div>
          )}
        </div>
      </div>

      {/* Recent Activity Feed */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">⚡ Real-Time Activity Feed</h3>
        
        {analyticsData.activities.length > 0 ? (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {analyticsData.activities.map((activity, index) => (
              <div key={index} className="flex items-center space-x-4 p-3 bg-gray-700 rounded-lg">
                <div className="text-2xl">{getActivityIcon(activity.type)}</div>
                <div className="flex-1">
                  <div className={`font-medium ${getActivityColor(activity.type)}`}>
                    {formatActivityMessage(activity)}
                  </div>
                  <div className="text-sm text-gray-400">{activity.time}</div>
                </div>
                <div className="text-xs text-gray-500">
                  {activity.family && (
                    <span className="bg-gray-600 px-2 py-1 rounded">
                      {activity.family}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <div className="text-6xl mb-4">🕵️</div>
            <div className="text-xl mb-2">Monitoring for Activity...</div>
            <div>Intelligence updates will appear here as they happen</div>
          </div>
        )}
      </div>

      {/* System Performance */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">🔧 System Performance</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-700 p-4 rounded-lg">
            <h4 className="font-medium text-white mb-2">Scraping Service</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Status:</span>
                <span className="text-green-400">
                  {systemStatus.scraping_service ? 'ACTIVE' : 'OFFLINE'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Cached Players:</span>
                <span className="text-white">{systemStatus.scraping_service?.cached_players || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Queue Size:</span>
                <span className="text-white">{systemStatus.scraping_service?.queue_size || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-700 p-4 rounded-lg">
            <h4 className="font-medium text-white mb-2">Database</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Status:</span>
                <span className="text-green-400">
                  {systemStatus.database?.connected ? 'CONNECTED' : 'OFFLINE'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Type:</span>
                <span className="text-white">MongoDB + SQLite</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-700 p-4 rounded-lg">
            <h4 className="font-medium text-white mb-2">WebSocket</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Connections:</span>
                <span className="text-white">{systemStatus.websocket_connections || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Last Update:</span>
                <span className="text-white">
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
  );
};

export default AnalyticsPage;