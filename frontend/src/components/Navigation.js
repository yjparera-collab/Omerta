import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useIntelligence } from '../hooks/useIntelligence';

const Navigation = () => {
  const location = useLocation();
  const { systemStatus, isConnected, notifications } = useIntelligence();

  const navItems = [
    { path: '/players', label: 'Players Dashboard', icon: '👥' },
    { path: '/families', label: 'Target Configuration', icon: '🎯' },
    { path: '/analytics', label: 'War Analytics', icon: '📊' },
  ];

  const unreadNotifications = notifications.filter(n => !n.is_read).length;

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-4">
            <div className="text-2xl">🎯</div>
            <div>
              <h1 className="text-xl font-bold text-white">Omerta Intelligence</h1>
              <p className="text-xs text-gray-400">War Dashboard v2.0</p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-6">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors
                  ${location.pathname === item.path
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </div>

          {/* Status Indicators */}
          <div className="flex items-center space-x-4">
            {/* Notification Badge */}
            {unreadNotifications > 0 && (
              <div className="flex items-center space-x-1 bg-red-600 text-white px-2 py-1 rounded-full text-xs">
                <span>🚨</span>
                <span>{unreadNotifications}</span>
              </div>
            )}

            {/* Connection Status */}
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs
              ${isConnected ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-300' : 'bg-red-300'}`}></div>
              <span>{isConnected ? 'CONNECTED' : 'DISCONNECTED'}</span>
            </div>

            {/* System Stats */}
            {systemStatus.scraping_service && (
              <div className="text-xs text-gray-400">
                <div>Players: {systemStatus.scraping_service.cached_players || 0}</div>
                <div>Queue: {systemStatus.scraping_service.queue_size || 0}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;