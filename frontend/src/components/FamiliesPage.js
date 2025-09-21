import React, { useState, useMemo } from 'react';
import { useIntelligence } from '../hooks/useIntelligence';

const FamiliesPage = () => {
  const { players, targetFamilies, setFamilyTargets } = useIntelligence();
  const [selectedFamilies, setSelectedFamilies] = useState(new Set(targetFamilies));
  const [expandedFamilies, setExpandedFamilies] = useState(new Set());

  // Group players by family
  const familiesByName = useMemo(() => {
    const grouped = {};
    
    players.forEach(player => {
      const familyName = player.f_name || 'No Family';
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
          // Sort members by position (0 goes to end)
          const aPos = a.position === 0 ? 999999 : a.position;
          const bPos = b.position === 0 ? 999999 : b.position;
          return aPos - bPos;
        });
        return acc;
      }, {});

    return sortedFamilies;
  }, [players]);

  const handleFamilyToggle = (familyName) => {
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
      alert(`Target families updated: ${familiesArray.length} families selected`);
    } catch (error) {
      alert('Failed to update target families');
    }
  };

  const handleSelectAll = () => {
    const allFamilies = Object.keys(familiesByName).filter(name => name !== 'No Family');
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

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">🎯 Target Configuration Center</h1>
            <p className="text-gray-400 mt-1">Select families to monitor with enhanced intelligence tracking</p>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={handleSelectAll}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Select All
            </button>
            <button
              onClick={handleSelectNone}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Select None
            </button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">{Object.keys(familiesByName).length}</div>
            <div className="text-sm text-gray-400">Total Families</div>
          </div>
          <div className="bg-blue-900 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">{selectedFamilies.size}</div>
            <div className="text-sm text-blue-200">Selected for Tracking</div>
          </div>
          <div className="bg-green-900 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">
              {Object.entries(familiesByName)
                .filter(([name]) => selectedFamilies.has(name))
                .reduce((sum, [, members]) => sum + members.filter(m => m.status !== 3).length, 0)}
            </div>
            <div className="text-sm text-green-200">Targets (Alive)</div>
          </div>
          <div className="bg-orange-900 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">
              {Object.entries(familiesByName)
                .filter(([name]) => selectedFamilies.has(name))
                .reduce((sum, [, members]) => sum + members.filter(m => m.position > 0).length, 0)}
            </div>
            <div className="text-sm text-orange-200">Ranked Targets</div>
          </div>
        </div>

        {/* Families List */}
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {Object.entries(familiesByName).map(([familyName, members]) => {
            const stats = getFamilyStats(members);
            const isSelected = selectedFamilies.has(familyName);
            const isExpanded = expandedFamilies.has(familyName);
            
            return (
              <div
                key={familyName}
                className={`border rounded-lg transition-all ${
                  isSelected 
                    ? 'border-blue-500 bg-blue-900/20' 
                    : 'border-gray-600 bg-gray-700'
                }`}
              >
                {/* Family Header */}
                <div 
                  className="p-4 cursor-pointer hover:bg-gray-600 transition-colors"
                  onClick={() => handleFamilyToggle(familyName)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleFamilyToggle(familyName)}
                        className="w-4 h-4"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <div>
                        <h3 className="font-semibold text-white text-lg">{familyName}</h3>
                        <div className="flex space-x-4 text-sm text-gray-400">
                          <span>👥 {stats.total} members</span>
                          <span className="text-green-400">✓ {stats.alive} alive</span>
                          <span className="text-red-400">✗ {stats.dead} dead</span>
                          <span className="text-yellow-400">🏆 {stats.ranked} ranked</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {isSelected && (
                        <span className="bg-blue-600 text-white px-2 py-1 rounded-full text-xs font-medium">
                          TRACKING
                        </span>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleExpandToggle(familyName);
                        }}
                        className="text-gray-400 hover:text-white"
                      >
                        {isExpanded ? '🔽' : '▶️'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Family Members (Expanded) */}
                {isExpanded && (
                  <div className="border-t border-gray-600 p-4 bg-gray-800">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                      {members.map(member => (
                        <div
                          key={member.id}
                          className={`p-2 rounded text-sm ${
                            member.status === 3 
                              ? 'bg-red-900/30 text-red-200' 
                              : 'bg-gray-700 text-gray-200'
                          }`}
                        >
                          <div className="font-medium">{member.uname}</div>
                          <div className="text-xs opacity-75">
                            {member.rank_name} • 
                            {member.position === 0 ? ' Unranked' : ` #${member.position}`}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Action Button */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={handleSaveTargets}
            className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-medium text-lg"
          >
            🕵️ Save Target List & Start Detective Operations
          </button>
        </div>

        {/* Current Targets Summary */}
        {selectedFamilies.size > 0 && (
          <div className="mt-6 p-4 bg-blue-900/30 border border-blue-600 rounded-lg">
            <h3 className="font-semibold text-white mb-2">📋 Selected Target Families:</h3>
            <div className="flex flex-wrap gap-2">
              {Array.from(selectedFamilies).map(family => (
                <span
                  key={family}
                  className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm"
                >
                  {family}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FamiliesPage;