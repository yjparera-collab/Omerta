import React, { useState, useMemo, useEffect } from 'react';
import { useIntelligence } from '../hooks/useIntelligence';

const FamiliesPage = () => {
  const { players, targetFamilies, setFamilyTargets, getPlayerDetails, trackedPlayers } = useIntelligence();
  const [selectedFamilies, setSelectedFamilies] = useState(new Set(targetFamilies));
  const [expandedFamilies, setExpandedFamilies] = useState(new Set());
  const [detectiveTargets, setDetectiveTargets] = useState([]);
  const [playerDetails, setPlayerDetails] = useState({});
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Load detective targets and their details
  useEffect(() => {
    const loadDetectiveData = async () => {
      setLoadingDetails(true);
      
      // Use tracked players directly from the intelligence hook
      if (trackedPlayers.length > 0) {
        setDetectiveTargets(trackedPlayers);
        
        // Load additional details for each tracked player
        const details = {};
        for (const tracked of trackedPlayers) {
          const playerDetail = players.find(p => p.id === tracked.player_id || p.uname === tracked.username);
          if (playerDetail) {
            try {
              const detail = await getPlayerDetails(playerDetail.id);
              if (detail) {
                details[playerDetail.id] = detail;
              }
            } catch (error) {
              console.error(`Failed to load details for ${tracked.username}:`, error);
            }
          }
        }
        setPlayerDetails(details);
      }
      
      setLoadingDetails(false);
    };

    loadDetectiveData();
  }, [trackedPlayers, players, getPlayerDetails]);

  // Group players by family
  const familiesByName = useMemo(() => {
    const grouped = {};
    
    players.forEach(player => {
      const familyName = player.f_name || 'Independent';
      if (!grouped[familyName]) {
        grouped[familyName] = [];
      }
      grouped[familyName].push(player);
    });

    // Sort families by member count
    const sortedFamilies = Object.entries(grouped)
      .sort((a, b) => b[1].length - a[1].length)
      .reduce((acc, [name, members]) => {
        acc[name] = members.sort((a, b) => {
          const aPos = a.position === 0 ? 999999 : a.position;
          const bPos = b.position === 0 ? 999999 : b.position;
          return aPos - bPos;
        });
        return acc;
      }, {});

    return sortedFamilies;
  }, [players]);

  const handleFamilyToggle = (familyName) => {
    if (familyName === 'Independent') return; // Skip independents
    
    const newSelected = new Set(selectedFamilies);
    if (newSelected.has(familyName)) {
      newSelected.delete(familyName);
    } else {
      newSelected.add(familyName);
    }
    setSelectedFamilies(newSelected);
  };

  const handleExpandToggle = (familyName) => {
    const newExpanded = new Set(expandedFamilies);
    if (newExpanded.has(familyName)) {
      newExpanded.delete(familyName);
    } else {
      newExpanded.add(familyName);
    }
    setExpandedFamilies(newExpanded);
  };

  const handleSaveTargets = async () => {
    const familiesArray = Array.from(selectedFamilies);
    try {
      await setFamilyTargets(familiesArray);
      alert(`Intelligence operations updated: ${familiesArray.length} families under surveillance`);
    } catch (error) {
      alert('Failed to update surveillance targets');
    }
  };

  const handleSelectAll = () => {
    const allFamilies = Object.keys(familiesByName).filter(name => name !== 'Independent');
    setSelectedFamilies(new Set(allFamilies));
  };

  const handleSelectNone = () => {
    setSelectedFamilies(new Set());
  };

  const getFamilyStats = (members) => {
    const alive = members.filter(m => m.status !== 3).length;
    const dead = members.filter(m => m.status === 3).length;
    const ranked = members.filter(m => m.position > 0).length;
    
    return { alive, dead, ranked, total: members.length };
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    return new Intl.NumberFormat('en-US', { notation: 'compact' }).format(num);
  };

  const getPlayerStatus = (player) => {
    if (player.status === 3) return { text: 'KIA', class: 'text-red-400', bg: 'bg-red-900/30' };
    if (player.position === 0) return { text: 'UNRANKED', class: 'text-amber-400', bg: 'bg-amber-900/20' };
    return { text: 'ACTIVE', class: 'text-emerald-400', bg: 'bg-emerald-900/20' };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-8 mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-white mb-3">
                <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 text-transparent bg-clip-text">
                  Intelligence Command Center
                </span>
              </h1>
              <p className="text-slate-400 text-lg">Configure family surveillance and monitor high-value targets</p>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={handleSelectAll}
                className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Select All Families
              </button>
              <button
                onClick={handleSelectNone}
                className="bg-slate-600 hover:bg-slate-700 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200"
              >
                Clear Selection
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Left Section - Family Selection */}
          <div className="xl:col-span-2">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-slate-800/30 backdrop-blur-sm rounded-lg border border-slate-700/50 p-4">
                <div className="text-2xl font-bold text-white">{Object.keys(familiesByName).length}</div>
                <div className="text-sm text-slate-400">Total Families</div>
              </div>
              <div className="bg-blue-900/30 backdrop-blur-sm rounded-lg border border-blue-500/30 p-4">
                <div className="text-2xl font-bold text-white">{selectedFamilies.size}</div>
                <div className="text-sm text-blue-200">Under Surveillance</div>
              </div>
              <div className="bg-emerald-900/30 backdrop-blur-sm rounded-lg border border-emerald-500/30 p-4">
                <div className="text-2xl font-bold text-white">
                  {Object.entries(familiesByName)
                    .filter(([name]) => selectedFamilies.has(name))
                    .reduce((sum, [, members]) => sum + members.filter(m => m.status !== 3).length, 0)}
                </div>
                <div className="text-sm text-emerald-200">Active Targets</div>
              </div>
              <div className="bg-orange-900/30 backdrop-blur-sm rounded-lg border border-orange-500/30 p-4">
                <div className="text-2xl font-bold text-white">
                  {Object.entries(familiesByName)
                    .filter(([name]) => selectedFamilies.has(name))
                    .reduce((sum, [, members]) => sum + members.filter(m => m.position > 0).length, 0)}
                </div>
                <div className="text-sm text-orange-200">Ranked Targets</div>
              </div>
            </div>

            {/* Families List */}
            <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
              <div className="p-6 border-b border-slate-700/50">
                <h2 className="text-xl font-bold text-white">Family Networks</h2>
                <p className="text-slate-400 text-sm mt-1">Select families for enhanced intelligence gathering</p>
              </div>
              
              <div className="max-h-96 overflow-y-auto">
                <div className="space-y-2 p-4">
                  {Object.entries(familiesByName).map(([familyName, members]) => {
                    if (familyName === 'Independent') return null;
                    
                    const stats = getFamilyStats(members);
                    const isSelected = selectedFamilies.has(familyName);
                    const isExpanded = expandedFamilies.has(familyName);
                    
                    return (
                      <div
                        key={familyName}
                        className={`border rounded-lg transition-all duration-200 ${
                          isSelected 
                            ? 'border-blue-500/50 bg-blue-900/20 shadow-lg shadow-blue-500/10' 
                            : 'border-slate-600/50 bg-slate-700/20 hover:bg-slate-700/30'
                        }`}
                      >
                        {/* Family Header */}
                        <div 
                          className="p-4 cursor-pointer"
                          onClick={() => handleFamilyToggle(familyName)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => handleFamilyToggle(familyName)}
                                className="w-5 h-5 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
                                onClick={(e) => e.stopPropagation()}
                              />
                              <div>
                                <h3 className="font-bold text-white text-lg">{familyName}</h3>
                                <div className="flex space-x-4 text-sm text-slate-400 mt-1">
                                  <span className="flex items-center">
                                    <span className="mr-1">👥</span>
                                    {stats.total}
                                  </span>
                                  <span className="flex items-center text-emerald-400">
                                    <span className="mr-1">✓</span>
                                    {stats.alive}
                                  </span>
                                  <span className="flex items-center text-red-400">
                                    <span className="mr-1">✗</span>
                                    {stats.dead}
                                  </span>
                                  <span className="flex items-center text-yellow-400">
                                    <span className="mr-1">🏆</span>
                                    {stats.ranked}
                                  </span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-3">
                              {isSelected && (
                                <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-xs font-medium">
                                  SURVEILLANCE ACTIVE
                                </span>
                              )}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleExpandToggle(familyName);
                                }}
                                className="text-slate-400 hover:text-white p-1 rounded transition-colors"
                              >
                                {isExpanded ? '🔽' : '▶️'}
                              </button>
                            </div>
                          </div>
                        </div>

                        {/* Family Members (Expanded) */}
                        {isExpanded && (
                          <div className="border-t border-slate-600/30 p-4 bg-slate-800/20">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {members.slice(0, 10).map(member => {
                                const status = getPlayerStatus(member);
                                return (
                                  <div
                                    key={member.id}
                                    className={`p-3 rounded-lg border ${
                                      member.status === 3 
                                        ? 'bg-red-900/20 border-red-500/30' 
                                        : 'bg-slate-700/30 border-slate-600/30'
                                    }`}
                                  >
                                    <div className="flex justify-between items-start">
                                      <div>
                                        <div className="font-medium text-white">{member.uname}</div>
                                        <div className="text-xs text-slate-400 mt-1">
                                          {member.rank_name} • 
                                          {member.position === 0 ? ' Unranked' : ` #${member.position}`}
                                        </div>
                                      </div>
                                      <span className={`px-2 py-1 rounded text-xs font-medium ${status.class} ${status.bg}`}>
                                        {status.text}
                                      </span>
                                    </div>
                                  </div>
                                );
                              })}
                              {members.length > 10 && (
                                <div className="col-span-full text-center text-slate-400 text-sm py-2">
                                  +{members.length - 10} more members...
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Action Button */}
            <div className="mt-8 text-center">
              <button
                onClick={handleSaveTargets}
                className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white px-8 py-4 rounded-lg font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-200"
              >
                🕵️ Deploy Intelligence Operations
              </button>
            </div>
          </div>

          {/* Right Section - Detective Targets Overview */}
          <div className="space-y-6">
            <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
              <div className="p-6 border-b border-slate-700/50">
                <h2 className="text-xl font-bold text-white mb-2 flex items-center">
                  <span className="text-purple-400 mr-2">🎯</span>
                  High-Value Targets
                </h2>
                <p className="text-slate-400 text-sm">Active combatants under surveillance</p>
              </div>

              <div className="max-h-96 overflow-y-auto">
                {loadingDetails ? (
                  <div className="p-8 text-center">
                    <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                    <div className="text-slate-400">Loading intelligence data...</div>
                  </div>
                ) : detectiveTargets.length === 0 ? (
                  <div className="p-8 text-center">
                    <div className="text-4xl mb-4">🔍</div>
                    <div className="text-slate-400 text-lg font-medium mb-2">No Active Targets</div>
                    <div className="text-slate-500 text-sm">Select families to identify high-value targets</div>
                  </div>
                ) : (
                  <div className="p-4 space-y-3">
                    {detectiveTargets.map((target) => {
                      const details = playerDetails[target.id];
                      const status = getPlayerStatus(target);
                      
                      return (
                        <div
                          key={target.id}
                          className="bg-slate-700/30 border border-slate-600/30 rounded-lg p-4 hover:bg-slate-700/40 transition-all duration-200"
                        >
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <div className="font-semibold text-white text-lg">{target.uname}</div>
                              <div className="text-sm text-slate-400">
                                {target.rank_name} • {target.f_name}
                              </div>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${status.class} ${status.bg}`}>
                              {status.text}
                            </span>
                          </div>

                          {/* Combat Stats */}
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-red-900/20 border border-red-500/30 rounded p-3">
                              <div className="text-red-400 text-xs font-semibold mb-1">ELIMINATIONS</div>
                              <div className="text-white text-xl font-bold">
                                {formatNumber(details?.kills || 0)}
                              </div>
                            </div>
                            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded p-3">
                              <div className="text-yellow-400 text-xs font-semibold mb-1">SHOTS FIRED</div>
                              <div className="text-white text-xl font-bold">
                                {formatNumber(details?.bullets_shot?.total || 0)}
                              </div>
                            </div>
                          </div>

                          {/* Additional Intel */}
                          {details && (
                            <div className="mt-3 pt-3 border-t border-slate-600/30">
                              <div className="grid grid-cols-2 gap-4 text-xs">
                                <div>
                                  <span className="text-slate-400">Plating:</span>
                                  <span className="text-white ml-2">{details.plating || 'Unknown'}</span>
                                </div>
                                <div>
                                  <span className="text-slate-400">Rank:</span>
                                  <span className="text-yellow-400 ml-2">#{target.position || 'Unranked'}</span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Current Surveillance Summary */}
            {selectedFamilies.size > 0 && (
              <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 backdrop-blur-sm rounded-xl border border-blue-500/30 p-6">
                <h3 className="font-bold text-white mb-3 flex items-center">
                  <span className="text-blue-400 mr-2">📋</span>
                  Active Surveillance
                </h3>
                <div className="space-y-2">
                  {Array.from(selectedFamilies).map(family => (
                    <div key={family} className="flex justify-between items-center">
                      <span className="bg-blue-600/30 text-blue-200 px-3 py-1 rounded-full text-sm font-medium">
                        {family}
                      </span>
                      <span className="text-slate-300 text-sm">
                        {familiesByName[family]?.filter(m => m.status !== 3).length || 0} active
                      </span>
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t border-blue-500/20">
                  <div className="text-sm text-blue-200">
                    <strong>{detectiveTargets.length}</strong> high-value targets identified
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FamiliesPage;