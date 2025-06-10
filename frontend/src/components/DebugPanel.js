import React, { useState, useEffect } from 'react';
import { performance, debugApi } from '../services/apiClient';
import { useGame } from '../store/gameStore';
import websocketManager from '../services/websocketManager';

const DebugPanel = () => {
  const { state } = useGame();
  const [activeTab, setActiveTab] = useState('performance');
  const [apiMetrics, setApiMetrics] = useState([]);
  const [logs, setLogs] = useState([]);
  const [wsInfo, setWsInfo] = useState({});

  useEffect(() => {
    // Update metrics every second
    const interval = setInterval(() => {
      setApiMetrics(performance.getMetrics());
      setWsInfo(websocketManager.getConnectionInfo());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleGetLogs = async () => {
    try {
      const response = await debugApi.getLogs('main', 50);
      setLogs(response.split('\n').slice(0, 50));
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  };

  const handleClearCache = async () => {
    try {
      await debugApi.clearPerformanceCache();
      alert('Performance cache cleared');
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  };

  const tabs = [
    { id: 'performance', label: 'Performance' },
    { id: 'api', label: 'API Calls' },
    { id: 'websocket', label: 'WebSocket' },
    { id: 'gamestate', label: 'Game State' },
    { id: 'logs', label: 'Logs' }
  ];

  return (
    <div className="fixed top-16 right-4 w-96 max-h-96 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-40 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-700 px-4 py-2 border-b border-gray-600">
        <h3 className="text-white font-semibold text-sm">Debug Panel</h3>
      </div>

      {/* Tabs */}
      <div className="flex bg-gray-700 border-b border-gray-600">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-2 text-xs font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4 overflow-auto max-h-80">
        {activeTab === 'performance' && (
          <div className="space-y-3">
            <div>
              <p className="text-gray-300 text-xs mb-1">Average Response Time</p>
              <p className="text-white text-sm font-mono">
                {performance.getAverageResponseTime().toFixed(0)}ms
              </p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Total API Calls</p>
              <p className="text-white text-sm font-mono">{apiMetrics.length}</p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Slow Requests (>1s)</p>
              <p className="text-white text-sm font-mono">
                {performance.getSlowRequests().length}
              </p>
            </div>
            <button
              onClick={handleClearCache}
              className="w-full bg-red-600 hover:bg-red-700 text-white text-xs py-2 rounded"
            >
              Clear Cache
            </button>
          </div>
        )}

        {activeTab === 'api' && (
          <div className="space-y-2">
            {apiMetrics.slice(0, 10).map((metric, index) => (
              <div key={index} className="bg-gray-700 p-2 rounded text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-blue-400 font-mono">
                    {metric.method} {metric.url.split('/').pop()}
                  </span>
                  <span className={`font-mono ${metric.duration > 1000 ? 'text-red-400' : 'text-green-400'}`}>
                    {metric.duration}ms
                  </span>
                </div>
                <div className="text-gray-400 mt-1">
                  Status: {metric.status} | {new Date(metric.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'websocket' && (
          <div className="space-y-3">
            <div>
              <p className="text-gray-300 text-xs mb-1">Connection State</p>
              <p className={`text-sm font-mono ${
                wsInfo.state === 'connected' ? 'text-green-400' : 'text-red-400'
              }`}>
                {wsInfo.state || 'disconnected'}
              </p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Game ID</p>
              <p className="text-white text-sm font-mono break-all">
                {wsInfo.gameId || 'None'}
              </p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Reconnect Attempts</p>
              <p className="text-white text-sm font-mono">
                {wsInfo.reconnectAttempts || 0}
              </p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Queued Messages</p>
              <p className="text-white text-sm font-mono">
                {wsInfo.queuedMessages || 0}
              </p>
            </div>
          </div>
        )}

        {activeTab === 'gamestate' && (
          <div className="space-y-3">
            <div>
              <p className="text-gray-300 text-xs mb-1">Game State</p>
              <p className="text-white text-sm font-mono">{state.gameState}</p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Round State</p>
              <p className="text-white text-sm font-mono">{state.roundState}</p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Player Count</p>
              <p className="text-white text-sm font-mono">{state.players.length}</p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Pot</p>
              <p className="text-white text-sm font-mono">${state.pot}</p>
            </div>
            <div>
              <p className="text-gray-300 text-xs mb-1">Current Correlation ID</p>
              <p className="text-white text-xs font-mono break-all">
                {state.correlationId || 'None'}
              </p>
            </div>
            {state.error && (
              <div>
                <p className="text-red-400 text-xs mb-1">Error</p>
                <p className="text-red-300 text-xs">{state.error}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="space-y-2">
            <button
              onClick={handleGetLogs}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs py-2 rounded mb-2"
            >
              Fetch Latest Logs
            </button>
            <div className="space-y-1 max-h-60 overflow-auto">
              {logs.map((line, index) => (
                <div key={index} className="text-xs font-mono text-gray-300 bg-gray-900 p-1 rounded">
                  {line}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DebugPanel;