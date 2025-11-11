'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface AnalysisModalProps {
  isOpen: boolean;
  analysis: any;
  onClose: () => void;
}

export function AnalysisModal({ isOpen, analysis, onClose }: AnalysisModalProps) {
  if (!analysis) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 flex items-center justify-center z-50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black bg-opacity-70"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="relative bg-gray-900 text-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
            initial={{ scale: 0.9, y: 50 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 50 }}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-6 rounded-t-2xl">
              <h2 className="text-3xl font-bold">📊 Hand Analysis</h2>
              <p className="text-sm opacity-80 mt-1">Rule-based insights to improve your poker skills</p>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Hand Summary */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-xl font-semibold mb-2 text-blue-400">
                  Hand #{analysis.hand_number || 'N/A'}
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {analysis.human_action && (
                    <div>
                      <span className="text-gray-400">Your Action:</span>
                      <span className="ml-2 font-bold">{analysis.human_action}</span>
                    </div>
                  )}
                  {analysis.pot_size !== undefined && (
                    <div>
                      <span className="text-gray-400">Pot Size:</span>
                      <span className="ml-2 font-bold">${analysis.pot_size}</span>
                    </div>
                  )}
                  {analysis.human_cards && analysis.human_cards.length > 0 && (
                    <div>
                      <span className="text-gray-400">Your Cards:</span>
                      <span className="ml-2 font-bold">{analysis.human_cards.join(', ')}</span>
                    </div>
                  )}
                  {analysis.community_cards && analysis.community_cards.length > 0 && (
                    <div>
                      <span className="text-gray-400">Community:</span>
                      <span className="ml-2 font-bold">{analysis.community_cards.join(', ')}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Insights */}
              {analysis.insights && analysis.insights.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold mb-3 text-green-400">💡 Key Insights</h3>
                  <div className="space-y-2">
                    {analysis.insights.map((insight: string, i: number) => (
                      <div key={i} className="bg-gray-800 p-3 rounded-lg text-sm">
                        {insight}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tips */}
              {analysis.tips && analysis.tips.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold mb-3 text-yellow-400">🎯 Tips for Next Time</h3>
                  <div className="space-y-2">
                    {analysis.tips.map((tip: string, i: number) => (
                      <div key={i} className="bg-gray-800 p-3 rounded-lg text-sm">
                        {tip}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Thinking */}
              {analysis.ai_thinking && Object.keys(analysis.ai_thinking).length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold mb-3 text-purple-400">🤖 AI Players' Thinking</h3>
                  <div className="space-y-3">
                    {Object.entries(analysis.ai_thinking).map(([name, decision]: [string, any]) => (
                      <div key={name} className="bg-gray-800 p-3 rounded-lg">
                        <div className="font-semibold text-blue-300">{name}</div>
                        <div className="text-sm mt-1">
                          <span className="text-gray-400">Action:</span>
                          <span className="ml-2 font-bold">{decision.action}</span>
                          {decision.amount > 0 && (
                            <span className="ml-1">${decision.amount}</span>
                          )}
                        </div>
                        {decision.reasoning && (
                          <div className="text-xs text-gray-300 mt-2 italic">
                            "{decision.reasoning}"
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No insights fallback */}
              {(!analysis.insights || analysis.insights.length === 0) &&
               (!analysis.tips || analysis.tips.length === 0) && (
                <div className="text-center text-gray-400 py-8">
                  <p>No specific insights for this hand.</p>
                  <p className="text-sm mt-2">Play more hands to get detailed analysis!</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-800 p-4 rounded-b-2xl flex justify-end">
              <button
                onClick={onClose}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-2 px-6 rounded-lg"
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
