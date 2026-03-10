'use client';

import { useState, useEffect } from 'react';

export default function MobileGate({ children }: { children: React.ReactNode }) {
  const [isMobile, setIsMobile] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check sessionStorage for previous dismissal
    const wasDismissed = sessionStorage.getItem('mobile_gate_dismissed');
    if (wasDismissed === 'true') {
      setDismissed(true);
    }

    const mql = window.matchMedia('(max-width: 767px)');
    setIsMobile(mql.matches);

    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

  if (isMobile && !dismissed) {
    return (
      <div
        data-testid="mobile-gate"
        className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-900 text-white px-8"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="w-16 h-16 mb-6 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25A2.25 2.25 0 0 1 5.25 3h13.5A2.25 2.25 0 0 1 21 5.25Z"
          />
        </svg>

        <h1 className="text-2xl font-bold mb-3 text-center">
          Optimized for Larger Screens
        </h1>

        <p className="text-gray-400 text-center mb-8 max-w-sm">
          This app works on mobile but is optimized for larger screens.
          For the best experience, visit on a desktop or laptop.
        </p>

        <button
          data-testid="mobile-gate-continue"
          onClick={() => {
            sessionStorage.setItem('mobile_gate_dismissed', 'true');
            setDismissed(true);
          }}
          className="bg-[#1F7A47] hover:bg-[#0A4D26] text-white px-6 py-3 rounded-lg font-semibold transition-colors"
        >
          Continue on Mobile
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
