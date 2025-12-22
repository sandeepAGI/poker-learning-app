'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

interface SessionAnalysisModalProps {
  isOpen: boolean;
  analysis: any;
  isLoading: boolean;
  error: string | null;
  onClose: () => void;
  onAnalyze: (depth: 'quick' | 'deep') => void;
  currentDepth: 'quick' | 'deep';
  handsAnalyzed?: number;
}

export function SessionAnalysisModal({
  isOpen,
  analysis,
  isLoading,
  error,
  onClose,
  onAnalyze,
  currentDepth,
  handsAnalyzed
}: SessionAnalysisModalProps) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black bg-opacity-70 pointer-events-none"
          />

          {/* Modal */}
          <motion.div
            className="relative bg-gray-900 text-white rounded-2xl shadow-2xl max-w-4xl w-full mx-4 max-h-[85vh] overflow-y-auto pointer-events-auto z-10"
            initial={{ scale: 0.9, y: 50 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 50 }}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 rounded-t-2xl">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-3xl font-bold">📈 Session Analysis</h2>
                  <p className="text-sm opacity-80 mt-1">
                    AI-powered insights across {handsAnalyzed || 'your'} hands
                  </p>
                </div>
                {/* Quick/Deep Toggle */}
                <div className="flex gap-2">
                  <button
                    onClick={() => onAnalyze('quick')}
                    disabled={isLoading}
                    className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                      currentDepth === 'quick'
                        ? 'bg-white text-indigo-600'
                        : 'bg-indigo-800 bg-opacity-50 hover:bg-opacity-70'
                    } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    Quick
                  </button>
                  <button
                    onClick={() => onAnalyze('deep')}
                    disabled={isLoading}
                    className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                      currentDepth === 'deep'
                        ? 'bg-white text-purple-600'
                        : 'bg-purple-800 bg-opacity-50 hover:bg-opacity-70'
                    } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    Deep Dive
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Loading State */}
              {isLoading && (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
                  <p className="mt-4 text-gray-400">Analyzing your session...</p>
                  <p className="text-sm text-gray-500 mt-2">
                    {currentDepth === 'deep' ? 'Deep analysis may take 5-10 seconds' : 'This will take 2-3 seconds'}
                  </p>
                </div>
              )}

              {/* Error State */}
              {error && !isLoading && (
                <div className="bg-red-900 bg-opacity-30 border border-red-500 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-red-400">Analysis Failed</h3>
                  <p className="text-sm text-red-300 mt-2">{error}</p>
                </div>
              )}

              {/* Analysis Content */}
              {analysis && !isLoading && !error && (
                <>
                  {/* Session Summary */}
                  {analysis.session_summary && (
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-lg font-semibold text-indigo-300">{analysis.session_summary}</p>
                    </div>
                  )}

                  {/* Overall Stats */}
                  {analysis.overall_stats && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3 text-blue-400">📊 Session Statistics</h3>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <div className="bg-gray-800 p-4 rounded-lg">
                          <div className="text-gray-400 text-sm">Win Rate</div>
                          <div className="text-2xl font-bold text-green-400">
                            {analysis.overall_stats.win_rate?.toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {analysis.overall_stats.hands_won}/{analysis.hands_analyzed} hands
                          </div>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-lg">
                          <div className="text-gray-400 text-sm">VPIP</div>
                          <div className="text-2xl font-bold text-blue-400">
                            {analysis.overall_stats.vpip?.toFixed(1)}%
                          </div>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-lg">
                          <div className="text-gray-400 text-sm">PFR</div>
                          <div className="text-2xl font-bold text-purple-400">
                            {analysis.overall_stats.pfr?.toFixed(1)}%
                          </div>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-lg">
                          <div className="text-gray-400 text-sm">Net Profit</div>
                          <div className={`text-2xl font-bold ${analysis.overall_stats.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            ${analysis.overall_stats.net_profit}
                          </div>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-lg">
                          <div className="text-gray-400 text-sm">Biggest Win</div>
                          <div className="text-2xl font-bold text-green-400">
                            ${analysis.overall_stats.biggest_win}
                          </div>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-lg">
                          <div className="text-gray-400 text-sm">Biggest Loss</div>
                          <div className="text-2xl font-bold text-red-400">
                            ${Math.abs(analysis.overall_stats.biggest_loss)}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Top Strengths */}
                  {analysis.top_3_strengths && analysis.top_3_strengths.length > 0 && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3 text-green-400">💪 Your Strengths</h3>
                      <div className="space-y-3">
                        {analysis.top_3_strengths.map((strength: any, i: number) => (
                          <div key={i} className="bg-gray-800 p-4 rounded-lg border-l-4 border-green-500">
                            <div className="font-semibold text-green-300">{strength.strength}</div>
                            <div className="text-sm text-gray-300 mt-1">{strength.evidence}</div>
                            {strength.keep_doing && (
                              <div className="text-xs text-gray-400 mt-2 italic">
                                ✓ {strength.keep_doing}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Top Leaks */}
                  {analysis.top_3_leaks && analysis.top_3_leaks.length > 0 && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3 text-yellow-400">🔧 Areas to Improve</h3>
                      <div className="space-y-3">
                        {analysis.top_3_leaks.map((leak: any, i: number) => (
                          <div key={i} className="bg-gray-800 p-4 rounded-lg border-l-4 border-yellow-500">
                            <div className="font-semibold text-yellow-300">{leak.leak}</div>
                            <div className="text-sm text-gray-300 mt-1">{leak.evidence}</div>
                            {leak.cost_estimate !== undefined && (
                              <div className="text-xs text-red-400 mt-1">
                                Estimated cost: ${Math.abs(leak.cost_estimate)}
                              </div>
                            )}
                            {leak.fix && (
                              <div className="text-sm text-green-300 mt-2 bg-gray-900 p-2 rounded">
                                💡 Fix: {leak.fix}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommended Adjustments */}
                  {analysis.recommended_adjustments && analysis.recommended_adjustments.length > 0 && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3 text-blue-400">🎯 Recommended Adjustments</h3>
                      <div className="space-y-2">
                        {analysis.recommended_adjustments.map((adj: any, i: number) => (
                          <div key={i} className="bg-gray-800 p-3 rounded-lg">
                            <div className="font-semibold text-blue-300">{adj.adjustment}</div>
                            <div className="text-sm text-gray-400 mt-1">{adj.reason}</div>
                            {adj.action && (
                              <div className="text-sm text-green-300 mt-1">→ {adj.action}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Concepts to Study */}
                  {analysis.concepts_to_study && analysis.concepts_to_study.length > 0 && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3 text-purple-400">📚 Study These Concepts</h3>
                      <div className="space-y-2">
                        {analysis.concepts_to_study.map((concept: any, i: number) => (
                          <div key={i} className="bg-gray-800 p-3 rounded-lg">
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-semibold text-purple-300">{concept.concept}</div>
                                <div className="text-sm text-gray-400 mt-1">{concept.why_relevant}</div>
                              </div>
                              <div className="bg-purple-900 bg-opacity-50 text-purple-300 px-2 py-1 rounded text-xs">
                                Priority {concept.priority}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Overall Assessment */}
                  {analysis.overall_assessment && (
                    <div className="bg-indigo-900 bg-opacity-30 border border-indigo-500 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold text-indigo-300 mb-2">Coach's Assessment</h3>
                      <p className="text-gray-300">{analysis.overall_assessment}</p>
                      {analysis.encouragement && (
                        <p className="text-green-300 mt-2 italic">"{analysis.encouragement}"</p>
                      )}
                    </div>
                  )}

                  {/* Empty State */}
                  {!analysis.session_summary && !analysis.overall_stats && (
                    <div className="text-center text-gray-400 py-8">
                      <p>No session data available.</p>
                      <p className="text-sm mt-2">Play at least 10 hands to get session analysis!</p>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-800 p-4 rounded-b-2xl flex justify-between items-center">
              <div className="text-sm text-gray-400">
                {currentDepth === 'quick' && '⚡ Quick Analysis (~2s, $0.02)'}
                {currentDepth === 'deep' && '🔬 Deep Dive (~5s, $0.03)'}
              </div>
              <button
                onClick={onClose}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-2 px-6 rounded-lg"
              >
                Close
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
