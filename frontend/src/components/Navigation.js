import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useIntelligence } from '../hooks/useIntelligence';

const Navigation = () => {
  const location = useLocation();
  const { systemStatus, isConnected, notifications } = useIntelligence();
  
  // Force recompile - test timestamp: 1234567890

  const navItems = [
    { 
      path: '/players', 
      label: 'Intelligence Overview', 
      icon: '🎯',
      description: 'Live player surveillance'
    },
    { 
      path: '/families', 
      label: 'Command Center', 
      icon: '🏛️',
      description: 'Target configuration'
    },
    { 
      path: '/analytics', 
      label: 'War Analytics', 
      icon: '📊',
      description: 'Combat intelligence'
    },
    { 
      path: '/settings', 
      label: 'TEST SETTINGS', 
      icon: '🔧',
      description: 'Test configuration'
    },
  ];

  const unreadNotifications = notifications.filter(n => !n.is_read).length;

  return (
    <nav className="bg-slate-900/95 backdrop-blur-xl border-b border-slate-700/50 shadow-2xl">
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-20">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="text-3xl animate-pulse">🎯</div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-ping"></div>
            </div>
            <div>
              <h1 className="text-2xl font-bold">
                <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 text-transparent bg-clip-text">
                  OMERTA
                </span>
                <span className="text-white ml-2">INTELLIGENCE</span>
              </h1>
              <p className="text-xs text-slate-400 font-medium tracking-wider">
                TACTICAL WARFARE DASHBOARD v2.0
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`group relative flex items-center space-x-3 px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-400/30 shadow-lg shadow-blue-500/20'
                      : 'text-slate-300 hover:text-white hover:bg-slate-700/50 border border-transparent'
                  }`}
                >
                  <span className={`text-xl transition-transform duration-200 ${
                    isActive ? 'scale-110' : 'group-hover:scale-105'
                  }`}>
                    {item.icon}
                  </span>
                  <div>
                    <div className="text-sm font-semibold">{item.label}</div>
                    <div className="text-xs opacity-70">{item.description}</div>
                  </div>
                  {isActive && (
                    <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    </div>
                  )}
                </Link>
              );
            })}
          </div>

          {/* Status Panel */}
          <div className="flex items-center space-x-4">
            {/* Critical Alerts Badge */}
            {unreadNotifications > 0 && (
              <div className="relative">
                <div className="flex items-center space-x-2 bg-gradient-to-r from-red-600 to-red-700 text-white px-4 py-2 rounded-lg font-semibold text-sm shadow-lg">
                  <span className="animate-pulse">🚨</span>
                  <span>ALERTS</span>
                  <div className="bg-white/20 text-white px-2 py-1 rounded-full text-xs font-bold min-w-[1.5rem] text-center">
                    {unreadNotifications}
                  </div>
                </div>
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-400 rounded-full animate-ping"></div>
              </div>
            )}

            {/* Connection Status */}
            <div className={`flex items-center space-x-3 px-4 py-2 rounded-lg border font-medium text-sm transition-all duration-200 ${
              isConnected 
                ? 'bg-emerald-900/30 border-emerald-500/50 text-emerald-300 shadow-emerald-500/20' 
                : 'bg-red-900/30 border-red-500/50 text-red-300 shadow-red-500/20 animate-pulse'
            } shadow-lg`}>
              <div className="relative">
                <div className={`w-3 h-3 rounded-full ${
                  isConnected ? 'bg-emerald-400' : 'bg-red-400'
                }`}></div>
                <div className={`absolute inset-0 w-3 h-3 rounded-full animate-ping ${
                  isConnected ? 'bg-emerald-400' : 'bg-red-400'
                }`}></div>
              </div>
              <div>
                <div className="font-bold">
                  {isConnected ? 'SYSTEM ONLINE' : 'CONNECTION LOST'}
                </div>
                <div className="text-xs opacity-75">
                  Intelligence Network
                </div>
              </div>
            </div>

            {/* System Statistics */}
            {systemStatus.scraping_service && (
              <div className="bg-slate-800/50 border border-slate-600/50 rounded-lg px-4 py-2">
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="text-center">
                    <div className="text-white font-bold text-lg">
                      {systemStatus.scraping_service.cached_players || 0}
                    </div>
                    <div className="text-slate-400 font-medium">TARGETS</div>
                  </div>
                  <div className="text-center">
                    <div className="text-white font-bold text-lg">
                      {systemStatus.scraping_service.queue_size || 0}
                    </div>
                    <div className="text-slate-400 font-medium">QUEUE</div>
                  </div>
                </div>
              </div>
            )}

            {/* Operations Status */}
            <div className="flex flex-col items-end">
              <div className="text-xs text-slate-400 font-medium">OPS STATUS</div>
              <div className={`text-xs font-bold ${isConnected ? 'text-emerald-400' : 'text-red-400'}`}>
                {isConnected ? 'ACTIVE SURVEILLANCE' : 'SYSTEMS OFFLINE'}
              </div>
            </div>
          </div>
        </div>

        {/* Status Bar */}
        <div className="border-t border-slate-700/50 px-6 py-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-6 text-slate-400">
              <div className="flex items-center space-x-2">
                <span>🗄️</span>
                <span>Database: {systemStatus.database?.connected ? 'Connected' : 'Offline'}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span>⚡</span>
                <span>WebSocket: {systemStatus.websocket_connections || 0} active</span>
              </div>
              {systemStatus.scraping_service?.last_list_update && (
                <div className="flex items-center space-x-2">
                  <span>🔄</span>
                  <span>
                    Last Update: {new Date(systemStatus.scraping_service.last_list_update).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-4 text-slate-400">
              <div className="bg-slate-700/50 px-2 py-1 rounded text-xs font-mono">
                API: localhost:8001
              </div>
              <div className="bg-slate-700/50 px-2 py-1 rounded text-xs font-mono">
                SCRAPER: localhost:5001
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;