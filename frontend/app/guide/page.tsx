'use client';

import Link from 'next/link';

export default function GuidePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-700 to-blue-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-2xl p-6 mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-800">How to Use This App</h1>
            <Link
              href="/"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              ← Back to Home
            </Link>
          </div>
          <p className="text-gray-600 mt-2">
            A complete guide to playing poker and learning from AI opponents.
          </p>
        </div>

        {/* Content */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 space-y-8">
          {/* Getting Started */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Getting Started</h2>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">1. Create a New Game</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li>Enter your name on the welcome screen</li>
                  <li>Choose table size: 4 players (beginner-friendly) or 6 players (full table)</li>
                  <li>Click "Start Game" to begin</li>
                </ul>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">2. Table Size Options</h3>
                <div className="text-sm text-gray-700 space-y-2">
                  <p><strong>🎯 4 Players (Recommended for beginners):</strong> Faster hands, easier to learn, less complex decision-making</p>
                  <p><strong>🔥 6 Players (Full table):</strong> More realistic poker experience, more challenging, varied strategies</p>
                </div>
              </div>
            </div>
          </section>

          {/* Understanding the Interface */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Understanding the Interface</h2>

            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Your Seat (Bottom Center)</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li><strong>Hole Cards:</strong> Your two private cards</li>
                  <li><strong>Stack:</strong> Your total chips</li>
                  <li><strong>Current Bet:</strong> How much you've bet this round (green text)</li>
                  <li><strong>Yellow Border:</strong> Indicates it's your turn to act</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Opponent Seats</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li>Cards are hidden until showdown</li>
                  <li>Watch for betting patterns and stack sizes</li>
                  <li>Yellow border shows whose turn it is</li>
                  <li>AI personality revealed at showdown</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Table Center</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li><strong>Community Cards:</strong> 5 shared cards (flop, turn, river)</li>
                  <li><strong>Pot:</strong> Total chips in play (amber badge)</li>
                  <li><strong>Blinds:</strong> Small blind (SB) and big blind (BB) indicators</li>
                  <li><strong>Dealer Button (D):</strong> Shows who has the button position</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Position Indicators</h3>
                <div className="flex gap-4 mt-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-white rounded-full border-4 border-amber-500 flex items-center justify-center text-xs font-bold">D</div>
                    <span className="text-sm text-gray-700">Dealer Button</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">SB</div>
                    <span className="text-sm text-gray-700">Small Blind</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold">BB</div>
                    <span className="text-sm text-gray-700">Big Blind</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Action Controls */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Action Controls</h2>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Available Actions</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-semibold text-red-700">Fold</p>
                    <p className="text-sm text-gray-700">Give up your hand and forfeit the pot. Use when your hand is weak.</p>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-blue-700">Call</p>
                    <p className="text-sm text-gray-700">Match the current bet to stay in the hand. Amount shown on button.</p>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-green-700">Raise</p>
                    <p className="text-sm text-gray-700">Increase the bet. Use slider or input to set amount, then click "Raise".</p>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <p className="text-sm text-blue-900">
                  <strong>Tip:</strong> The Call button shows "Check" when there's no bet to call. Checking
                  means you stay in the hand without betting.
                </p>
              </div>
            </div>
          </section>

          {/* AI Thinking Sidebar */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">AI Thinking Sidebar</h2>

            <div className="space-y-4">
              <p className="text-gray-700">
                The AI thinking sidebar (right side) shows real-time AI decision-making. This is the
                best feature for learning poker strategy.
              </p>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">What You'll See</h3>
                <ul className="text-sm text-gray-700 space-y-2 ml-4 list-disc">
                  <li><strong>AI Name:</strong> Which opponent made the decision</li>
                  <li><strong>Action:</strong> Fold, Call, or Raise with amount</li>
                  <li><strong>SPR:</strong> Stack-to-Pot Ratio calculation</li>
                  <li><strong>Hand Strength:</strong> AI's estimated strength (0.0 to 1.0)</li>
                  <li><strong>Pot Odds:</strong> Mathematical AI shows pot odds calculation</li>
                  <li><strong>Reasoning:</strong> Why the AI made this decision</li>
                </ul>
              </div>

              <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
                <p className="text-sm text-green-900">
                  <strong>Learning Tip:</strong> Toggle the sidebar on/off with the button at the top. Watch
                  how different AI personalities react to the same situations - this is how you learn strategy!
                </p>
              </div>
            </div>
          </section>

          {/* Features */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Features</h2>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Hand History & Analysis</h3>
                <p className="text-sm text-gray-700">
                  After each hand completes, view detailed analysis showing pot size, winner, and
                  all player decisions throughout the hand.
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Next Hand</h3>
                <p className="text-sm text-gray-700">
                  Click "Next Hand" button to start a new hand. Dealer button rotates, new cards
                  are dealt, blinds are posted automatically.
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Beginner Mode</h3>
                <p className="text-sm text-gray-700 mb-2">
                  Toggle in the sidebar to switch between beginner-friendly explanations and
                  advanced poker terminology.
                </p>
                <ul className="text-xs text-gray-600 ml-4 list-disc space-y-1">
                  <li><strong>Beginner:</strong> "I have a pretty good hand" (simple language)</li>
                  <li><strong>Expert:</strong> "Top pair with weak kicker, SPR 4.2" (technical terms)</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Tips & Tricks */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Tips & Tricks</h2>

            <div className="space-y-3">
              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">💡</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Watch AI Reasoning</p>
                  <p className="text-sm text-gray-700">Keep the AI thinking sidebar open to learn why they fold, call, or raise</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">💡</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Start with 4 Players</p>
                  <p className="text-sm text-gray-700">Beginners should start with 4-player tables - hands are faster and decisions are simpler</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">💡</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Compare AI Personalities</p>
                  <p className="text-sm text-gray-700">Watch how Conservative, Aggressive, and Mathematical AIs handle the same cards differently</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">💡</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Learn SPR Concept</p>
                  <p className="text-sm text-gray-700">Understanding Stack-to-Pot Ratio is the key to better decision-making - see tutorial for details</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">💡</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Take Your Time</p>
                  <p className="text-sm text-gray-700">There's no timer - think through each decision and learn at your own pace</p>
                </div>
              </div>
            </div>
          </section>

          {/* Troubleshooting */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Common Questions</h2>

            <div className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-gray-800">Why can't I raise more than my stack?</p>
                <p className="text-sm text-gray-700">You can only bet chips you have. If you want to bet more, you'll go "all-in" with your remaining chips.</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-800">What does "ALL-IN" mean?</p>
                <p className="text-sm text-gray-700">A player has bet all their remaining chips. They can't be forced out but also can't win more than what they've contributed to the pot.</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-800">Why did the AI fold with good cards?</p>
                <p className="text-sm text-gray-700">Conservative AI folds frequently. Aggressive AI might have made a big raise. Check the AI thinking sidebar to see their reasoning.</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-800">How do I see the tutorial again?</p>
                <p className="text-sm text-gray-700">Click "Back to Home" and then click "Learn Texas Hold'em" to review hand rankings and strategy.</p>
              </div>
            </div>
          </section>

          {/* Back to Game */}
          <div className="flex justify-center pt-4">
            <Link
              href="/"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors text-center"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
