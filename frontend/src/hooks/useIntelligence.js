import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API_BASE = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('http', 'ws') + '/ws';

const IntelligenceContext = createContext();

export const useIntelligence = () => {
  const context = useContext(IntelligenceContext);
  if (!context) {
    throw new Error('useIntelligence must be used within an IntelligenceProvider');
  }
  return context;
};

export const IntelligenceProvider = ({ children }) => {
  const [players, setPlayers] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [systemStatus, setSystemStatus] = useState({ connected: false });
  const [targetFamilies, setTargetFamilies] = useState([]);
  const [detectiveTargets, setDetectiveTargets] = useState([]);
  const [trackedPlayers, setTrackedPlayers] = useState([]);
  const [ws, setWs] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const websocket = new WebSocket(WS_URL);
        
        websocket.onopen = () => {
          console.log('🔌 WebSocket connected to intelligence dashboard');
          setSystemStatus(prev => ({ ...prev, connected: true }));
        };

        websocket.onmessage = (event) => {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        };

        websocket.onclose = () => {
          console.log('🔌 WebSocket disconnected, attempting to reconnect...');
          setSystemStatus(prev => ({ ...prev, connected: false }));
          // Reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };

        websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        setWs(websocket);

        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);

        return () => {
          clearInterval(pingInterval);
          websocket.close();
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setTimeout(connectWebSocket, 5000);
      }
    };

    const cleanup = connectWebSocket();
    return cleanup;
  }, []);

  const handleWebSocketMessage = useCallback((message) => {
    switch (message.type) {
      case 'intelligence_notification':
        setNotifications(prev => [message.data, ...prev.slice(0, 49)]); // Keep last 50
        break;
      
      case 'player_list_updated':
        setLastUpdate(new Date().toISOString());
        fetchPlayers(); // Refresh player list
        break;
      
      case 'intelligence_update':
        if (message.data.notifications) {
          setNotifications(prev => {
            const newNotifications = message.data.notifications.filter(
              newNotif => !prev.some(existing => 
                existing.username === newNotif.username && 
                existing.timestamp === newNotif.timestamp
              )
            );
            return [...newNotifications, ...prev].slice(0, 50);
          });
        }
        break;
      
      case 'detective_targets_updated':
      case 'family_targets_updated':
        fetchSystemStatus(); // Refresh status
        break;
      
      case 'pong':
        // Connection is alive
        break;
      
      default:
        console.log('Unknown WebSocket message:', message);
    }
  }, []);

  // API calls
  const apiCall = useCallback(async (endpoint, options = {}) => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API call to ${endpoint} failed:`, error);
      throw error;
    }
  }, []);

  const fetchPlayers = useCallback(async () => {
    try {
      const data = await apiCall('/players');
      setPlayers(data.players || []);
      setLastUpdate(data.last_updated);
    } catch (error) {
      console.error('Failed to fetch players:', error);
    }
  }, [apiCall]);

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await apiCall('/intelligence/notifications');
      setNotifications(data.notifications || []);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  }, [apiCall]);

  const fetchSystemStatus = useCallback(async () => {
    try {
      const data = await apiCall('/status');
      setSystemStatus(prev => ({ ...prev, ...data }));
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  }, [apiCall]);

  const fetchTargetFamilies = useCallback(async () => {
    try {
      const data = await apiCall('/families/targets');
      setTargetFamilies(data.families || []);
    } catch (error) {
      console.error('Failed to fetch target families:', error);
    }
  }, [apiCall]);

  const fetchTrackedPlayers = useCallback(async () => {
    try {
      const data = await apiCall('/intelligence/tracked-players');
      setTrackedPlayers(data.tracked_players || []);
    } catch (error) {
      console.error('Failed to fetch tracked players:', error);
    }
  }, [apiCall]);

  // Actions
  const setFamilyTargets = useCallback(async (families) => {
    try {
      await apiCall('/families/set-targets', {
        method: 'POST',
        body: JSON.stringify({ families }),
      });
      setTargetFamilies(families);
    } catch (error) {
      console.error('Failed to set family targets:', error);
      throw error;
    }
  }, [apiCall]);

  const addDetectiveTargets = useCallback(async (usernames) => {
    try {
      await apiCall('/intelligence/detective/add', {
        method: 'POST',
        body: JSON.stringify({ usernames }),
      });
      setDetectiveTargets(prev => [...new Set([...prev, ...usernames])]);
      
      // Refresh tracked players after adding
      fetchTrackedPlayers();
    } catch (error) {
      console.error('Failed to add detective targets:', error);
      throw error;
    }
  }, [apiCall, fetchTrackedPlayers]);

  const getPlayerDetails = useCallback(async (playerId) => {
    try {
      return await apiCall(`/players/${playerId}`);
    } catch (error) {
      console.error(`Failed to get player ${playerId} details:`, error);
      return null;
    }
  }, [apiCall]);

  // Initial data load
  useEffect(() => {
    fetchPlayers();
    fetchNotifications();
    fetchSystemStatus();
    fetchTargetFamilies();
  }, [fetchPlayers, fetchNotifications, fetchSystemStatus, fetchTargetFamilies]);

  // Auto-refresh players every 60 seconds as backup to WebSocket
  useEffect(() => {
    const interval = setInterval(fetchPlayers, 60000);
    return () => clearInterval(interval);
  }, [fetchPlayers]);

  const value = {
    // Data
    players,
    notifications,
    systemStatus,
    targetFamilies,
    detectiveTargets,
    lastUpdate,
    
    // Actions
    fetchPlayers,
    setFamilyTargets,
    addDetectiveTargets,
    getPlayerDetails,
    
    // WebSocket
    isConnected: systemStatus.connected,
  };

  return (
    <IntelligenceContext.Provider value={value}>
      {children}
    </IntelligenceContext.Provider>
  );
};