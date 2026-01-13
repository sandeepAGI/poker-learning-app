'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { pokerApi } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import Link from 'next/link';

interface GameSummary {
  game_id: string;
  started_at: string;
  completed_at: string;
  total_hands: number;
  starting_stack: number;
  final_stack: number;
  profit_loss: number;
  num_ai_players: number;
}

export default function HistoryPage() {
  const router = useRouter();
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const fetchHistory = async () => {
      try {
        const data = await pokerApi.getMyGames();
        setGames(data.games);
      } catch (err) {
        setError('Failed to load game history');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [router]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">{error}</div>
          <Link href="/" className="text-blue-400 hover:text-blue-300">
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">Game History</h1>
          <div className="space-x-4">
            <Link
              href="/"
              className="text-blue-400 hover:text-blue-300 transition"
            >
              Home
            </Link>
            <Link
              href="/game/new"
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition"
            >
              New Game
            </Link>
          </div>
        </div>

        {games.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <p className="text-gray-400 text-lg mb-4">No games yet</p>
            <p className="text-gray-500 mb-6">Play your first game to see it here!</p>
            <Link
              href="/game/new"
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded transition"
            >
              Start Playing
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {games.map((game) => (
              <div
                key={game.game_id}
                className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-3">
                      <span className="text-gray-400 text-sm">
                        {formatDate(game.started_at)}
                      </span>
                      <span className="text-gray-500 text-sm">
                        vs {game.num_ai_players} AI opponent{game.num_ai_players !== 1 ? 's' : ''}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-6 text-sm">
                      <div>
                        <span className="text-gray-400">Hands Played:</span>
                        <span className="text-white ml-2 font-medium">{game.total_hands}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Stack:</span>
                        <span className="text-white ml-2">
                          ${game.starting_stack} → ${game.final_stack}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Result:</span>
                        <span
                          className={`ml-2 font-bold ${
                            game.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {game.profit_loss >= 0 ? '+' : ''}{game.profit_loss}
                        </span>
                      </div>
                    </div>
                  </div>

                  <Link
                    href={`/history/${game.game_id}`}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm transition ml-4"
                  >
                    Review Hands
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
