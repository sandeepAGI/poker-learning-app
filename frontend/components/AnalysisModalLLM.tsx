'use client';

/**
 * Enhanced Analysis Modal with LLM Support (Phase 4.5)
 *
 * Features:
 * - Quick Analysis only (Haiku 4.5) - simplified from Phase 4
 * - Renders comprehensive LLM analysis (round-by-round, tips, concepts)
 * - Falls back to rule-based analysis
 * - Clean UX without cost/technical details
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { pokerApi } from '../lib/api';

interface AnalysisModalLLMProps {
  isOpen: boolean;
  onClose: () => void;
  gameId: string;
  ruleBasedAnalysis?: any; // Fallback rule-based analysis
}

export function AnalysisModalLLM({ isOpen, onClose, gameId, ruleBasedAnalysis }: AnalysisModalLLMProps) {
  const [llmAnalysis, setLlmAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [cost, setCost] = useState(0);
  const [modelUsed, setModelUsed] = useState('');
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    setLoading(true);
    setError('');

    try {
      const result = await pokerApi.getHandAnalysisLLM(gameId);

      if (result.error) {
        setError(result.error);
        setModelUsed(result.model_used);
      } else {
        setLlmAnalysis(result.analysis);
        setCost(result.cost);
        setModelUsed(result.model_used);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze hand');
      console.error('LLM analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

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
            className="absolute inset-0 bg-black bg-opacity-70 pointer-events-auto"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="relative bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-2xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden pointer-events-auto z-10"
            initial={{ scale: 0.9, y: 50 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 50 }}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-green-700 to-green-600 p-6">
              <h2 className="text-2xl font-bold">🎓 Hand Analysis & Coaching</h2>
              <p className="text-green-100 mt-1">
                {llmAnalysis
                  ? 'AI-powered coaching insights'
                  : 'Choose your analysis type below'
                }
              </p>
            </div>

            {/* Content */}
            <div className="overflow-y-auto max-h-[calc(90vh-180px)]">
              {!llmAnalysis && !loading && (
                <div className="p-6 space-y-4">
                  {/* Analysis Type Selection */}
                  <div className="text-center space-y-4">
                    <p className="text-gray-300 mb-4">
                      Get personalized AI coaching to improve your poker skills
                    </p>

                    {/* Quick Analysis Button */}
                    <button
                      onClick={() => handleAnalyze()}
                      className="w-full bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white py-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all"
                    >
                      🎓 Analyze This Hand
                    </button>

                    <p className="text-sm text-gray-400 mt-4">
                      AI-powered analysis with round-by-round breakdown, tips for improvement, and concepts to study
                    </p>
                  </div>

                  {/* Rule-based fallback */}
                  {ruleBasedAnalysis && (
                    <div className="mt-8 pt-6 border-t border-gray-700">
                      <h3 className="text-lg font-semibold mb-3 text-gray-400">
                        Or view rule-based analysis:
                      </h3>
                      <RuleBasedAnalysisSection analysis={ruleBasedAnalysis} />
                    </div>
                  )}
                </div>
              )}

              {loading && (
                <div className="p-12 text-center">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-500 mx-auto mb-4"></div>
                  <p className="text-lg">
                    🎓 Analyzing your hand with AI...
                  </p>
                  <p className="text-sm text-gray-400 mt-2">
                    This typically takes 20-30 seconds
                  </p>
                </div>
              )}

              {error && (
                <div className="p-6">
                  <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-200">
                    <p className="font-semibold">❌ Analysis Failed</p>
                    <p className="text-sm mt-1">{error}</p>
                    {modelUsed === 'rule-based-fallback' && ruleBasedAnalysis && (
                      <div className="mt-4">
                        <p className="text-sm text-gray-300">Showing rule-based analysis instead:</p>
                        <RuleBasedAnalysisSection analysis={ruleBasedAnalysis} />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {llmAnalysis && !loading && (
                <div className="p-6 space-y-6">
                  <LLMAnalysisContent analysis={llmAnalysis} />
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-800 p-4 flex justify-between items-center">
              {llmAnalysis && (
                <button
                  onClick={() => {
                    setLlmAnalysis(null);
                    setError('');
                  }}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  ← Back to analysis options
                </button>
              )}
              <button
                onClick={onClose}
                className="ml-auto bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 text-white font-bold py-2 px-6 rounded-lg transition-all"
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

// LLM Analysis Content Renderer
function LLMAnalysisContent({ analysis }: { analysis: any }) {
  return (
    <div className="space-y-6">
      {/* Summary */}
      {analysis.summary && (
        <div className="bg-gray-800/50 p-4 rounded-lg border-l-4 border-green-500">
          <p className="text-lg">{analysis.summary}</p>
        </div>
      )}

      {/* Round-by-Round */}
      {analysis.round_by_round && analysis.round_by_round.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-3 text-blue-400">📊 Round-by-Round Breakdown</h3>
          <div className="space-y-3">
            {analysis.round_by_round.map((round: any, idx: number) => (
              <div key={idx} className="bg-gray-800 p-4 rounded-lg">
                <div className="font-semibold text-green-400">{round.round.toUpperCase()}</div>
                <div className="text-sm text-gray-400 mt-1">
                  Pot: ${round.pot_at_start} → ${round.pot_at_end}
                </div>
                {round.commentary && (
                  <p className="text-sm mt-2">{round.commentary}</p>
                )}
                {round.what_to_consider && (
                  <p className="text-xs text-gray-400 mt-2 italic">{round.what_to_consider}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Player Performance */}
      {analysis.player_analysis && (
        <div>
          <h3 className="text-xl font-semibold mb-3 text-green-400">✅ Your Performance</h3>

          {analysis.player_analysis.good_decisions?.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-green-300 mb-2">Good Decisions:</h4>
              <div className="space-y-2">
                {analysis.player_analysis.good_decisions.map((decision: any, idx: number) => (
                  <div key={idx} className="bg-green-900/20 p-3 rounded-lg border border-green-800">
                    <div className="font-semibold">{decision.action}</div>
                    <div className="text-sm text-gray-300 mt-1">{decision.why_good}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.player_analysis.questionable_decisions?.length > 0 && (
            <div>
              <h4 className="font-semibold text-yellow-300 mb-2">Areas to Improve:</h4>
              <div className="space-y-2">
                {analysis.player_analysis.questionable_decisions.map((decision: any, idx: number) => (
                  <div key={idx} className="bg-yellow-900/20 p-3 rounded-lg border border-yellow-800">
                    <div className="font-semibold">{decision.action}</div>
                    <div className="text-sm text-gray-300 mt-1">{decision.what_to_consider}</div>
                    {decision.better_play && (
                      <div className="text-sm text-yellow-200 mt-1">
                        <strong>Better play:</strong> {decision.better_play}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI Opponent Insights */}
      {analysis.ai_opponent_insights && analysis.ai_opponent_insights.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-3 text-purple-400">🤖 AI Opponent Insights</h3>
          <div className="space-y-3">
            {analysis.ai_opponent_insights.map((insight: any, idx: number) => (
              <div key={idx} className="bg-gray-800 p-4 rounded-lg">
                <div className="font-semibold text-purple-300">
                  {insight.player} ({insight.personality})
                </div>
                {insight.what_they_had && (
                  <div className="text-sm mt-1">Had: {insight.what_they_had}</div>
                )}
                {insight.why_they_played_this_way && (
                  <p className="text-sm text-gray-300 mt-2">{insight.why_they_played_this_way}</p>
                )}
                {insight.how_to_exploit && (
                  <div className="text-sm text-yellow-200 mt-2">
                    <strong>How to exploit:</strong> {insight.how_to_exploit}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Concepts to Study */}
      {analysis.concepts_to_study && analysis.concepts_to_study.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-3 text-orange-400">📚 Concepts to Study</h3>
          <div className="space-y-2">
            {analysis.concepts_to_study.map((concept: any, idx: number) => (
              <div key={idx} className="bg-gray-800 p-3 rounded-lg">
                <div className="font-semibold">
                  {idx + 1}. {concept.concept}
                  {concept.priority && (
                    <span className="text-xs text-gray-400 ml-2">(Priority {concept.priority})</span>
                  )}
                </div>
                {concept.why_relevant && (
                  <p className="text-sm text-gray-300 mt-1">{concept.why_relevant}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tips for Improvement */}
      {analysis.tips_for_improvement && analysis.tips_for_improvement.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-3 text-yellow-400">💡 Tips for Improvement</h3>
          <div className="space-y-3">
            {analysis.tips_for_improvement.map((tip: any, idx: number) => (
              <div key={idx} className="bg-gray-800 p-4 rounded-lg">
                <div className="font-semibold text-yellow-300">{tip.tip}</div>
                {tip.actionable_step && (
                  <div className="text-sm text-gray-300 mt-2 bg-gray-900/50 p-2 rounded">
                    <strong>Action step:</strong> {tip.actionable_step}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Discussion Questions */}
      {analysis.discussion_questions && analysis.discussion_questions.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-3 text-cyan-400">🤔 Think About This</h3>
          <div className="space-y-2">
            {analysis.discussion_questions.map((question: string, idx: number) => (
              <div key={idx} className="bg-cyan-900/20 p-3 rounded-lg border-l-2 border-cyan-500 text-sm">
                {question}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Overall Assessment */}
      {analysis.overall_assessment && (
        <div className="bg-gray-800/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-400 mb-2">Overall Assessment:</h4>
          <p>{analysis.overall_assessment}</p>
        </div>
      )}

      {/* Encouragement */}
      {analysis.encouragement && (
        <div className="bg-gradient-to-r from-green-900/30 to-blue-900/30 p-4 rounded-lg border border-green-700 text-center">
          <p className="text-lg text-green-300">✨ {analysis.encouragement}</p>
        </div>
      )}
    </div>
  );
}

// Rule-based Analysis Fallback
function RuleBasedAnalysisSection({ analysis }: { analysis: any }) {
  return (
    <div className="space-y-4 text-sm">
      {analysis.insights && analysis.insights.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-300 mb-2">Insights:</h4>
          <div className="space-y-1">
            {analysis.insights.map((insight: string, i: number) => (
              <div key={i} className="bg-gray-800 p-2 rounded text-gray-300">
                {insight}
              </div>
            ))}
          </div>
        </div>
      )}

      {analysis.tips && analysis.tips.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-300 mb-2">Tips:</h4>
          <div className="space-y-1">
            {analysis.tips.map((tip: string, i: number) => (
              <div key={i} className="bg-gray-800 p-2 rounded text-gray-300">
                {tip}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
