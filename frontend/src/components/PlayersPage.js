import React, { useState, useMemo, useEffect } from 'react';
import { useIntelligence } from '../hooks/useIntelligence';

const PlayersPage = () => {
  const { players, notifications, getPlayerDetails, addDetectiveTargets } = useIntelligence();
  
  // Filters
  const [nameFilter, setNameFilter] = useState('');
  const [familyFilter, setFamilyFilter] = useState('');
  const [rankFilter, setRankFilter] = useState('');
  const [showDead, setShowDead] = useState(false);
  const [sortField, setSortField] = useState('position');
  const [sortDirection, setSortDirection] = useState('asc');
  
  // Selected players for detective tracking
  const [selectedPlayers, setSelectedPlayers] = useState(new Set());

  // Get unique families and ranks for filters
  const families = useMemo(() => {
    const uniqueFamilies = [...new Set(players.map(p => p.f_name).filter(Boolean))];
    return uniqueFamilies.sort();
  }, [players]);

  const ranks = useMemo(() => {
    const uniqueRanks = [...new Set(players.map(p => p.rank_name).filter(Boolean))];
    // Sort ranks in hierarchy order
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
      // Name filter
      if (nameFilter && !player.uname?.toLowerCase().includes(nameFilter.toLowerCase())) {
        return false;
      }
      
      // Family filter
      if (familyFilter && player.f_name !== familyFilter) {
        return false;
      }
      
      // Rank filter
      if (rankFilter && player.rank_name !== rankFilter) {
        return false;
      }
      
      // Dead players filter (status 3 = dead)
      if (!showDead && player.status === 3) {
        return false;
      }
      
      return true;
    });

    // Sort players
    filtered.sort((a, b) => {
      let aVal, bVal;
      
      switch (sortField) {
        case 'position':
          // Position 0 should go to bottom for ascending sort
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
  }, [players, nameFilter, familyFilter, rankFilter, showDead, sortField, sortDirection]);

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
    if (player.status === 3) return { text: 'DEAD', class: 'text-red-400' };
    if (player.position === 0) return { text: 'UNRANKED', class: 'text-gray-400' };
    return { text: 'ALIVE', class: 'text-green-400' };
  };

  return (
    <div className="grid grid-cols-12 gap-6 h-screen">
      {/* Control Panel - Left Column */}
      <div className="col-span-3 bg-gray-800 rounded-lg p-4">
        <h2 className="text-lg font-bold mb-4 text-white">🎛️ Control Panel</h2>
        
        {/* Search Filters */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Search Name</label>
            <input
              type="text"
              value={nameFilter}
              onChange={(e) => setNameFilter(e.target.value)}
              placeholder="Player name..."
              className="w-full px-3 py-2 bg-gray-700 text-white rounded-md text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Family</label>
            <select
              value={familyFilter}
              onChange={(e) => setFamilyFilter(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded-md text-sm"
            >
              <option value="">All Families</option>
              {families.map(family => (
                <option key={family} value={family}>{family}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Rank</label>
            <select
              value={rankFilter}
              onChange={(e) => setRankFilter(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded-md text-sm"
            >
              <option value="">All Ranks</option>
              {ranks.map(rank => (
                <option key={rank} value={rank}>{rank}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="showDead"
              checked={showDead}
              onChange={(e) => setShowDead(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="showDead" className="text-sm text-gray-300">Show Dead Players</label>
          </div>
        </div>

        {/* Detective Controls */}
        {selectedPlayers.size > 0 && (
          <div className="mt-6 p-4 bg-blue-900 rounded-lg">
            <h3 className="font-medium text-white mb-2">Detective Tracking</h3>
            <p className="text-sm text-blue-200 mb-3">{selectedPlayers.size} players selected</p>
            <button
              onClick={handleStartDetectiveTracking}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md text-sm font-medium"
            >
              🕵️ Start Tracking
            </button>
          </div>
        )}

        {/* Stats */}
        <div className="mt-6 p-4 bg-gray-700 rounded-lg">
          <h3 className="font-medium text-white mb-2">Statistics</h3>
          <div className="text-sm text-gray-300 space-y-1">
            <div>Total Players: {players.length}</div>
            <div>Filtered: {filteredPlayers.length}</div>
            <div>Alive: {players.filter(p => p.status !== 3).length}</div>
            <div>Dead: {players.filter(p => p.status === 3).length}</div>
          </div>
        </div>
      </div>

      {/* Main Players Table - Middle Column */}
      <div className="col-span-6 bg-gray-800 rounded-lg p-4">
        <h2 className="text-lg font-bold mb-4 text-white">👥 Players Overview</h2>
        
        <div className="overflow-y-auto max-h-[calc(100vh-200px)]">
          <table className="w-full text-sm">
            <thead className="bg-gray-700 sticky top-0">
              <tr>
                <th className="p-2 text-left">
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
                  />
                </th>
                <th className="p-2 text-left cursor-pointer hover:bg-gray-600" onClick={() => handleSort('position')}>
                  Pos {getSortIcon('position')}
                </th>
                <th className="p-2 text-left cursor-pointer hover:bg-gray-600" onClick={() => handleSort('name')}>
                  Name {getSortIcon('name')}
                </th>
                <th className="p-2 text-left cursor-pointer hover:bg-gray-600" onClick={() => handleSort('rank')}>
                  Rank {getSortIcon('rank')}
                </th>
                <th className="p-2 text-left cursor-pointer hover:bg-gray-600" onClick={() => handleSort('family')}>
                  Family {getSortIcon('family')}
                </th>
                <th className="p-2 text-left">Status</th>
                <th className="p-2 text-left">Intel</th>
              </tr>
            </thead>
            <tbody>
              {filteredPlayers.map((player, index) => {
                const status = getPlayerStatus(player);
                const isSelected = selectedPlayers.has(player.id);
                
                return (
                  <tr
                    key={player.id}
                    className={`border-b border-gray-700 hover:bg-gray-700 ${
                      isSelected ? 'bg-blue-900' : ''
                    }`}
                  >
                    <td className="p-2">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handlePlayerSelect(player.id)}
                      />
                    </td>
                    <td className="p-2 font-mono">
                      {player.position === 0 ? '-' : `#${player.position}`}
                    </td>
                    <td className="p-2 font-medium text-white">
                      {player.uname}
                      <div className="text-xs text-gray-400">
                        Kills: N/A • Shots: N/A
                      </div>
                    </td>
                    <td className="p-2 text-yellow-400">{player.rank_name}</td>
                    <td className="p-2 text-blue-400">{player.f_name || 'None'}</td>
                    <td className="p-2">
                      <span className={status.class}>{status.text}</span>
                    </td>
                    <td className="p-2">
                      <button
                        onClick={() => getPlayerDetails(player.id)}
                        className="text-xs bg-gray-600 hover:bg-gray-500 px-2 py-1 rounded"
                      >
                        📊
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Intelligence Feed - Right Column */}
      <div className="col-span-3 bg-gray-800 rounded-lg p-4">
        <h2 className="text-lg font-bold mb-4 text-white">🚨 Intelligence Feed</h2>
        
        <div className="overflow-y-auto max-h-[calc(100vh-200px)] space-y-2">
          {notifications.length === 0 ? (
            <p className="text-gray-400 text-sm">No intelligence notifications yet...</p>
          ) : (
            notifications.map((notification, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg text-sm ${
                  notification.type === 'plating_drop' ? 'bg-red-900 border border-red-600' :
                  notification.type === 'kill_update' ? 'bg-orange-900 border border-orange-600' :
                  notification.type === 'shot_update' ? 'bg-yellow-900 border border-yellow-600' :
                  'bg-gray-700'
                }`}
              >
                <div className="font-medium text-white mb-1">
                  {notification.message}
                </div>
                <div className="text-xs text-gray-300">
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