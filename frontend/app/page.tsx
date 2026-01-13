'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, getUsername, logout } from '@/lib/auth';
import Link from 'next/link';

export default function HomePage() {
  const router = useRouter();
  const username = getUsername();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
    }
  }, [router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!isAuthenticated()) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center px-4">
      <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Welcome, {username}!</h1>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white text-sm transition"
          >
            Logout
          </button>
        </div>

        <div className="space-y-4">
          <Link
            href="/game/new"
            className="block bg-blue-600 hover:bg-blue-700 text-white text-center font-bold py-3 px-4 rounded transition"
          >
            Start New Game
          </Link>

          <Link
            href="/history"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center font-bold py-3 px-4 rounded transition"
          >
            View Game History
          </Link>

          <Link
            href="/tutorial"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center py-3 px-4 rounded transition"
          >
            Tutorial
          </Link>

          <Link
            href="/guide"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center py-3 px-4 rounded transition"
          >
            Hand Rankings Guide
          </Link>
        </div>
      </div>
    </div>
  );
}
