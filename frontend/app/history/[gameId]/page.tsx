'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { pokerApi } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import Link from 'next/link';

interface Hand {
  hand_id: string;
  hand_number: number;
  hand_data: any;
  user_hole_cards: string;
  user_won: boolean;
  pot: number;
  created_at: string;
}

export default function HandReviewPage() {
  const router = useRouter();
  const params = useParams();
  const gameId = params.gameId as string;

  const [hands, setHands] = useState<Hand[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const fetchHands = async () => {
      try {
        const data = await pokerApi.getGameHands(gameId);
        setHands(data.hands);
      } catch (err) {
        setError('Failed to load hands');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchHands();
  }, [gameId, router]);

  const currentHand = hands[currentIndex];

  const getAnalysis = async () => {
    if (!currentHand) return;

    setLoadingAnalysis(true);
    setError('');

    try {
      const data = await pokerApi.getHandAnalysisLLM(gameId, {
        handNumber: currentHand.hand_number
      });
      setAnalysis(data);
    } catch (err: any) {
      if (err.response?.status === 429) {
        setError('Rate limited. Please wait before requesting another analysis.');
      } else {
        setError('Failed to load analysis');
      }
      console.error(err);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const goToPrevious = () => {
    setCurrentIndex(Math.max(0, currentIndex - 1));
    setAnalysis(null);
  };

  const goToNext = () => {
    setCurrentIndex(Math.min(hands.length - 1, currentIndex + 1));
    setAnalysis(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading hands...</div>
      </div>
    );
  }

  if (error && hands.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">{error}</div>
          <Link href="/history" className="text-blue-400 hover:text-blue-300">
            Back to History
          </Link>
        </div>
      </div>
    );
  }

  if (hands.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-400 text-xl mb-4">No hands found for this game</div>
          <Link href="/history" className="text-blue-400 hover:text-blue-300">
            Back to History
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <Link
            href="/history"
            className="text-blue-400 hover:text-blue-300 transition"
          >
            ← Back to History
          </Link>
          <div className="text-gray-400">
            Hand {currentIndex + 1} of {hands.length}
          </div>
        </div>

        {currentHand && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-3">
                  Hand #{currentHand.hand_number}
                </h2>
                <div className="flex flex-wrap gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Your Cards:</span>
                    <span className="text-white ml-2 font-medium">
                      {currentHand.user_hole_cards || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Pot:</span>
                    <span className="text-white ml-2">${currentHand.pot}</span>
                  </div>
                  <div>
                    <span className={currentHand.user_won ? 'text-green-400' : 'text-red-400'}>
                      {currentHand.user_won ? '✓ Won' : '✗ Lost'}
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={getAnalysis}
                disabled={loadingAnalysis}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded transition"
              >
                {loadingAnalysis ? 'Loading...' : 'Get AI Analysis'}
              </button>
            </div>

            {/* Hand Details */}
            {currentHand.hand_data && (
              <div className="bg-gray-700 rounded p-4 mb-4">
                <h3 className="text-white font-semibold mb-2">Hand Details</h3>
                <div className="text-gray-300 text-sm space-y-1">
                  {currentHand.hand_data.community_cards && (
                    <div>
                      <span className="text-gray-400">Community Cards:</span>
                      <span className="ml-2">{currentHand.hand_data.community_cards.join(', ')}</span>
                    </div>
                  )}
                  {currentHand.hand_data.rounds && (
                    <div>
                      <span className="text-gray-400">Rounds:</span>
                      <span className="ml-2">{currentHand.hand_data.rounds.length}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Analysis Display */}
            {analysis && (
              <div className="bg-gray-700 rounded p-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-white font-semibold">AI Analysis</h3>
                  <div className="text-sm text-gray-400">
                    Model: {analysis.model_used} | Cost: ${analysis.cost.toFixed(3)}
                    {analysis.cached && <span className="ml-2">(Cached)</span>}
                  </div>
                </div>
                <div className="text-gray-200 text-sm">
                  <pre className="whitespace-pre-wrap font-sans">
                    {JSON.stringify(analysis.analysis, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 rounded text-sm">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={goToPrevious}
            disabled={currentIndex === 0}
            className="bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded transition"
          >
            ← Previous
          </button>
          <button
            onClick={goToNext}
            disabled={currentIndex === hands.length - 1}
            className="bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded transition"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
