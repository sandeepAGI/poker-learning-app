'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { getUsername, isAuthenticated, deleteAccount } from '@/lib/auth';
import Link from 'next/link';

export default function SettingsPage() {
  const router = useRouter();
  const username = getUsername();
  const authenticated = isAuthenticated();
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');

  if (!authenticated) {
    router.push('/login');
    return null;
  }

  const handleDeleteAccount = async () => {
    const confirmed = window.confirm(
      'Are you sure? This will permanently delete your account and all game history. This cannot be undone.'
    );
    if (!confirmed) return;

    setDeleting(true);
    setError('');
    try {
      await deleteAccount();
      router.push('/login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete account');
      setDeleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center px-4">
      <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">Account Settings</h1>
          <Link
            href="/"
            className="text-gray-400 hover:text-white text-sm transition"
          >
            Back to Lobby
          </Link>
        </div>

        {/* Account Info */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-300 mb-3">Account</h2>
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="text-sm text-gray-400">Username</div>
            <div className="text-white font-medium">{username}</div>
          </div>
        </div>

        {/* Danger Zone */}
        <div>
          <h2 className="text-lg font-semibold text-red-400 mb-3">Danger Zone</h2>
          <div className="border border-red-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-4">
              Permanently delete your account and all game history. This action cannot be undone.
            </p>

            {error && (
              <div className="bg-red-900 border border-red-500 text-red-200 px-4 py-2 rounded text-sm mb-4">
                {error}
              </div>
            )}

            <button
              onClick={handleDeleteAccount}
              disabled={deleting}
              data-testid="delete-account-button"
              className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded transition"
            >
              {deleting ? 'Deleting...' : 'Delete Account'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
