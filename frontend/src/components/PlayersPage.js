import React, { useState, useMemo, useEffect } from 'react';
import { useIntelligence } from '../hooks/useIntelligence';

const PlayersPage = () => {
  const { players, notifications, getPlayerDetails, addDetectiveTargets } = useIntelligence();
  
  // Filters
  const [nameFilter, setNameFilter] = useState('');
  const [familyFilter, setFamilyFilter] = useState('');
  const [rankFilter, setRankFilter] = useState('');
  const [showDead, setShowDead] = useState(false);
  const [showTrackedOnly, setShowTrackedOnly] = useState(false);
  const [sortField, setSortField] = useState('position');
  const [sortDirection, setSortDirection] = useState('asc');
  
  // Selected players for detective tracking
  const [selectedPlayers, setSelectedPlayers] = useState(new Set());
  const [playerDetails, setPlayerDetails] = useState({});

  // Load player details for wealth/plating display
  useEffect(() => {
    const loadPlayerDetails = async () => {
      const details = {};
      for (const player of players.slice(0, 100)) { // Increased limit for better coverage
        try {
          const detail = await getPlayerDetails(player.id);
          if (detail) {
            details[player.id] = detail;
          }
        } catch (error) {
          console.error(`Failed to load details for ${player.uname}:`, error);
        }
      }
      setPlayerDetails(details);
    };

    if (players.length > 0) {
      loadPlayerDetails();
    }
  }, [players, getPlayerDetails]);

  // Get unique families and ranks for filters
  const families = useMemo(() => {
    const uniqueFamilies = [...new Set(players.map(p => p.f_name).filter(Boolean))];
    return uniqueFamilies.sort();
  }, [players]);

  const ranks = useMemo(() => {
    const uniqueRanks = [...new Set(players.map(p => p.rank_name).filter(Boolean))];
    const rankOrder = [
      "Empty-suit", "Delivery Boy", "Delivery Girl", "Picciotto", "Shoplifter", 
      "Pickpocket", "Thief", "Associate", "Mobster", "Soldier", "Swindler", 
      "Assassin", "Local Chief", "Chief", "Bruglione", "Capodecina", 
      "Godfather", "First Lady"
    ];
    return uniqueRanks.sort((a, b) => {
      const aIndex = rankOrder.indexOf(a);
      const bIndex = rankOrder.indexOf(b);
      return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex);
    });
  }, [players]);

  // Filter and sort players  
  const filteredPlayers = useMemo(() => {
    let filtered = players.filter(player => {
      if (nameFilter && !player.uname?.toLowerCase().includes(nameFilter.toLowerCase())) {
        return false;
      }
      if (familyFilter && player.f_name !== familyFilter) {
        return false;
      }
      if (rankFilter && player.rank_name !== rankFilter) {
        return false;
      }
      if (!showDead && player.status === 3) {
        return false;
      }
      // NEW: Filter for tracked players only
      if (showTrackedOnly && !playerDetails[player.id]) {
        return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      let aVal, bVal;
      
      switch (sortField) {
        case 'position':
          aVal = a.position === 0 ? 999999 : a.position;
          bVal = b.position === 0 ? 999999 : b.position;
          break;
        case 'rank':
          const rankOrder = [
            "Empty-suit", "Delivery Boy", "Delivery Girl", "Picciotto", "Shoplifter", 
            "Pickpocket", "Thief", "Associate", "Mobster", "Soldier", "Swindler", 
            "Assassin", "Local Chief", "Chief", "Bruglione", "Capodecina", 
            "Godfather", "First Lady"
          ];
          aVal = rankOrder.indexOf(a.rank_name);
          bVal = rankOrder.indexOf(b.rank_name);
          aVal = aVal === -1 ? 999 : aVal;
          bVal = bVal === -1 ? 999 : bVal;
          break;
        case 'wealth':
          aVal = playerDetails[a.id]?.wealth || 0;
          bVal = playerDetails[b.id]?.wealth || 0;
          break;
        case 'name':
          aVal = a.uname || '';
          bVal = b.uname || '';
          break;
        case 'family':
          aVal = a.f_name || '';
          bVal = b.f_name || '';
          break;
        default:
          aVal = a[sortField] || 0;
          bVal = b[sortField] || 0;
      }

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      } else {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
      }
    });

    return filtered;
  }, [players, nameFilter, familyFilter, rankFilter, showDead, showTrackedOnly, sortField, sortDirection, playerDetails]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handlePlayerSelect = (playerId) => {
    const newSelected = new Set(selectedPlayers);
    if (newSelected.has(playerId)) {
      newSelected.delete(playerId);
    } else {
      newSelected.add(playerId);
    }
    setSelectedPlayers(newSelected);
  };

  const handleStartDetectiveTracking = async () => {
    const usernames = filteredPlayers
      .filter(p => selectedPlayers.has(p.id))
      .map(p => p.uname);
    
    if (usernames.length > 0) {
      try {
        await addDetectiveTargets(usernames);
        setSelectedPlayers(new Set());
        alert(`Started detective tracking for ${usernames.length} players`);
      } catch (error) {
        alert('Failed to start detective tracking');
      }
    }
  };

  const getSortIcon = (field) => {
    if (sortField !== field) return '⚪';
    return sortDirection === 'asc' ? '🔼' : '🔽';
  };

  const getPlayerStatus = (player) => {
    if (player.status === 3) return { text: 'KIA', class: 'text-red-400 font-semibold', bg: 'bg-red-900/30' };
    if (player.position === 0) return { text: 'UNRANKED', class: 'text-amber-400 font-medium', bg: 'bg-amber-900/20' };
    return { text: 'ACTIVE', class: 'text-emerald-400 font-medium', bg: 'bg-emerald-900/20' };
  };

  const formatWealth = (wealth) => {
    if (wealth === undefined || wealth === null) return 'N/A';
    
    const wealthLevels = {
      0: "Straydog",
      1: "Poor",
      2: "Nouveau Riche", 
      3: "Rich",
      4: "Very Rich",
      5: "Too Rich to be True",
      6: "Richer than God"
    };
    
    return wealthLevels[wealth] || `Level ${wealth}`;
  };

  const getPlatingLevel = (plating) => {
    if (!plating) return { text: 'Unknown', class: 'text-gray-400', level: 0 };
    
    const level = plating.toLowerCase();
    if (level.includes('none') || level.includes('no plating')) {
      return { text: 'VULNERABLE', class: 'text-red-400 font-bold animate-pulse', level: 0 };
    }
    if (level.includes('low')) {
      return { text: 'Low', class: 'text-orange-400', level: 1 };
    }
    if (level.includes('medium')) {
      return { text: 'Medium', class: 'text-yellow-400', level: 2 };
    }
    if (level.includes('high')) {
      return { text: 'High', class: 'text-green-400', level: 3 };
    }
    if (level.includes('very high')) {
      return { text: 'Very High', class: 'text-blue-400', level: 4 };
    }
    return { text: plating, class: 'text-gray-300', level: 1 };
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Left Sidebar - Control Panel */}
      <div className="w-80 bg-slate-800/50 backdrop-blur-sm border-r border-slate-700/50 flex flex-col">
        <div className="p-6 border-b border-slate-700/50">
          <h2 className="text-xl font-bold text-white mb-2 flex items-center">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 text-transparent bg-clip-text">
              Control Center
            </span>
          </h2>
          <p className="text-slate-400 text-sm">Advanced player filtering</p>
        </div>
        
        {/* Filters */}
        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">Search Players</label>
            <div className="relative">
              <input
                type="text"
                value={nameFilter}
                onChange={(e) => setNameFilter(e.target.value)}
                placeholder="Enter player name..."
                className="w-full px-4 py-3 bg-slate-700/50 text-white rounded-lg border border-slate-600/50 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 transition-all"
              />
              <div className="absolute right-3 top-3 text-slate-400">🔍</div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">Family Filter</label>
            <select
              value={familyFilter}
              onChange={(e) => setFamilyFilter(e.target.value)}
              className="w-full px-4 py-3 bg-slate-700/50 text-white rounded-lg border border-slate-600/50 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 transition-all"
            >
              <option value="">All Families</option>
              {families.map(family => (
                <option key={family} value={family}>{family}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">Rank Filter</label>
            <select
              value={rankFilter}
              onChange={(e) => setRankFilter(e.target.value)}
              className="w-full px-4 py-3 bg-slate-700/50 text-white rounded-lg border border-slate-600/50 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 transition-all"
            >
              <option value="">All Ranks</option>
              {ranks.map(rank => (
                <option key={rank} value={rank}>{rank}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="showDead"
              checked={showDead}
              onChange={(e) => setShowDead(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
            />
            <label htmlFor="showDead" className="text-sm font-medium text-slate-300">Include KIA Players</label>
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="showTrackedOnly"
              checked={showTrackedOnly}
              onChange={(e) => setShowTrackedOnly(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
            />
            <label htmlFor="showTrackedOnly" className="text-sm font-medium text-slate-300">Tracked Players Only</label>
          </div>

          {/* Detective Controls */}
          {selectedPlayers.size > 0 && (
            <div className="p-4 rounded-lg bg-gradient-to-r from-blue-900/50 to-purple-900/50 border border-blue-500/30">
              <h3 className="font-semibold text-white mb-2 flex items-center">
                <span className="text-blue-400 mr-2">🎯</span>
                Detective Mode
              </h3>
              <p className="text-sm text-blue-200 mb-3">
                {selectedPlayers.size} target{selectedPlayers.size !== 1 ? 's' : ''} selected
              </p>
              <button
                onClick={handleStartDetectiveTracking}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-2 px-4 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                🕵️ Start Enhanced Tracking
              </button>
            </div>
          )}

          {/* Statistics Panel */}
          <div className="p-4 rounded-lg bg-slate-700/30 border border-slate-600/30">
            <h3 className="font-semibold text-white mb-3">Statistics</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Total Players:</span>
                <span className="text-white font-medium">{players.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Filtered:</span>
                <span className="text-white font-medium">{filteredPlayers.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Active:</span>
                <span className="text-emerald-400 font-medium">{players.filter(p => p.status !== 3).length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">KIA:</span>
                <span className="text-red-400 font-medium">{players.filter(p => p.status === 3).length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-slate-800/30 backdrop-blur-sm border-b border-slate-700/50 p-6">
          <h1 className="text-2xl font-bold text-white mb-2">
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 text-transparent bg-clip-text">
              Players Intelligence Overview
            </span>
          </h1>
          <p className="text-slate-400">Real-time tactical intelligence and enhanced surveillance</p>
        </div>

        {/* Players Table */}
        <div className="flex-1 p-6 overflow-hidden">
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/50 h-full flex flex-col">
            <div className="overflow-y-auto flex-1">
              <table className="w-full text-sm">
                <thead className="bg-slate-700/50 sticky top-0 backdrop-blur-sm">
                  <tr className="border-b border-slate-600/50">
                    <th className="p-3 text-left">
                      <input
                        type="checkbox"
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedPlayers(new Set(filteredPlayers.map(p => p.id)));
                          } else {
                            setSelectedPlayers(new Set());
                          }
                        }}
                        checked={selectedPlayers.size === filteredPlayers.length && filteredPlayers.length > 0}
                        className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
                      />
                    </th>
                    <th className="p-3 text-left cursor-pointer hover:bg-slate-600/30 transition-colors rounded" onClick={() => handleSort('position')}>
                      <span className="text-slate-300 font-semibold">Rank {getSortIcon('position')}</span>
                    </th>
                    <th className="p-3 text-left cursor-pointer hover:bg-slate-600/30 transition-colors rounded" onClick={() => handleSort('name')}>
                      <span className="text-slate-300 font-semibold">Player {getSortIcon('name')}</span>
                    </th>
                    <th className="p-3 text-left cursor-pointer hover:bg-slate-600/30 transition-colors rounded" onClick={() => handleSort('rank')}>
                      <span className="text-slate-300 font-semibold">Title {getSortIcon('rank')}</span>
                    </th>
                    <th className="p-3 text-left cursor-pointer hover:bg-slate-600/30 transition-colors rounded" onClick={() => handleSort('family')}>
                      <span className="text-slate-300 font-semibold">Family {getSortIcon('family')}</span>
                    </th>
                    <th className="p-3 text-left cursor-pointer hover:bg-slate-600/30 transition-colors rounded" onClick={() => handleSort('wealth')}>
                      <span className="text-slate-300 font-semibold">Wealth {getSortIcon('wealth')}</span>
                    </th>
                    <th className="p-3 text-left">
                      <span className="text-slate-300 font-semibold">Plating</span>
                    </th>
                    <th className="p-3 text-left">
                      <span className="text-slate-300 font-semibold">Status</span>
                    </th>
                    <th className="p-3 text-left">
                      <span className="text-slate-300 font-semibold">Intel</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPlayers.map((player, index) => {
                    const status = getPlayerStatus(player);
                    const isSelected = selectedPlayers.has(player.id);
                    const details = playerDetails[player.id];
                    const plating = getPlatingLevel(details?.plating);
                    
                    return (
                      <tr
                        key={player.id}
                        className={`border-b border-slate-700/30 hover:bg-slate-700/20 transition-all duration-200 ${
                          isSelected ? 'bg-blue-900/20 border-blue-500/30' : ''
                        }`}
                      >
                        <td className="p-3">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handlePlayerSelect(player.id)}
                            className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
                          />
                        </td>
                        <td className="p-3">
                          <div className="flex items-center">
                            {player.position === 0 ? (
                              <span className="text-slate-500 font-mono text-lg">—</span>
                            ) : (
                              <span className="text-amber-400 font-bold text-lg">#{player.position}</span>
                            )}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="font-semibold text-white text-base">{player.uname}</div>
                          <div className="text-xs text-slate-400 mt-1">
                            <span className="mr-3">K: {details?.kills || 'N/A'}</span>
                            <span>S: {details?.bullets_shot?.total || 'N/A'}</span>
                          </div>
                        </td>
                        <td className="p-3">
                          <span className="text-yellow-400 font-medium">{player.rank_name}</span>
                        </td>
                        <td className="p-3">
                          <span className="text-blue-400 font-medium">{player.f_name || 'Independent'}</span>
                        </td>
                        <td className="p-3">
                          <div className="text-green-400 font-semibold">
                            {formatWealth(details?.wealth)}
                          </div>
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${plating.class}`}>
                            {plating.text}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded-full text-xs ${status.class} ${status.bg}`}>
                            {status.text}
                          </span>
                        </td>
                        <td className="p-3">
                          <button
                            onClick={() => getPlayerDetails(player.id)}
                            className="px-3 py-1 bg-slate-600/50 hover:bg-slate-600 text-slate-300 hover:text-white rounded transition-colors text-xs font-medium"
                          >
                            📊 Analyze
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Intelligence Feed */}
      <div className="w-96 bg-slate-800/50 backdrop-blur-sm border-l border-slate-700/50 flex flex-col">
        <div className="p-6 border-b border-slate-700/50">
          <h2 className="text-xl font-bold text-white mb-2 flex items-center">
            <span className="text-red-400 mr-2 animate-pulse">🚨</span>
            <span className="bg-gradient-to-r from-red-400 to-orange-400 text-transparent bg-clip-text">
              Live Intelligence
            </span>
          </h2>
          <p className="text-slate-400 text-sm">Real-time tactical updates</p>
        </div>
        
        <div className="flex-1 p-6 overflow-y-auto space-y-3">
          {notifications.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎯</div>
              <div className="text-slate-400 text-lg font-medium mb-2">Monitoring...</div>
              <div className="text-slate-500 text-sm">Intelligence updates will appear here</div>
            </div>
          ) : (
            notifications.map((notification, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border transition-all duration-200 hover:scale-[1.02] ${
                  notification.type === 'plating_drop' ? 'bg-red-900/30 border-red-500/50 shadow-red-500/20' :
                  notification.type === 'kill_update' ? 'bg-orange-900/30 border-orange-500/50 shadow-orange-500/20' :
                  notification.type === 'shot_update' ? 'bg-yellow-900/30 border-yellow-500/50 shadow-yellow-500/20' :
                  'bg-slate-700/30 border-slate-600/50'
                } shadow-lg`}
              >
                <div className="font-semibold text-white mb-2 text-sm leading-relaxed">
                  {notification.message}
                </div>
                <div className="text-xs text-slate-400 flex items-center">
                  <span className="mr-2">⏰</span>
                  {new Date(notification.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayersPage;