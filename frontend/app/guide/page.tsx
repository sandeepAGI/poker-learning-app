'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function getBackNav(from: string | null) {
  switch (from) {
    case 'game':
      return { href: '/', label: 'Close Tab to Return to Game', isGameTab: true };
    case 'setup':
      return { href: '/game/new', label: 'Back to Game Setup', isGameTab: false };
    default:
      return { href: '/', label: 'Back to Home', isGameTab: false };
  }
}

function GuideContent() {
  const searchParams = useSearchParams();
  const from = searchParams.get('from');
  const nav = getBackNav(from);

  const backLink = nav.isGameTab ? (
    <button
      onClick={() => window.close()}
      className="text-sm text-blue-600 hover:text-blue-700 font-medium cursor-pointer"
    >
      &larr; {nav.label}
    </button>
  ) : (
    <Link href={nav.href} className="text-sm text-blue-600 hover:text-blue-700 font-medium">
      &larr; {nav.label}
    </Link>
  );

  const backButton = nav.isGameTab ? (
    <button
      onClick={() => window.close()}
      className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors text-center cursor-pointer"
    >
      Close &amp; Return to Game
    </button>
  ) : (
    <Link
      href={nav.href}
      className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors text-center"
    >
      {nav.label}
    </Link>
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-2xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-800">How to Use This App</h1>
          {backLink}
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
                <h3 className="font-semibold text-gray-800 mb-2">1. Create an Account</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li>Register with a username and password on the login screen</li>
                  <li>Your game history and progress are saved to your account</li>
                </ul>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">2. Create a New Game</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li>Enter your player name on the game setup screen</li>
                  <li>Choose table size: 4 players (beginner-friendly) or 6 players (full table)</li>
                  <li>Click &ldquo;Start Game&rdquo; to begin</li>
                </ul>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">3. Table Size Options</h3>
                <div className="text-sm text-gray-700 space-y-2">
                  <p><strong>4 Players (Recommended for beginners):</strong> Faster hands, easier to learn, less complex decision-making</p>
                  <p><strong>6 Players (Full table):</strong> More realistic poker experience, more challenging, varied strategies</p>
                </div>
              </div>
            </div>
          </section>

          {/* Understanding the Interface */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Understanding the Interface</h2>

            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Game Header</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li><strong>Hand Counter:</strong> Shows which hand you&apos;re on (e.g., &ldquo;Hand #5&rdquo;)</li>
                  <li><strong>Blind Levels:</strong> Current blind amounts (e.g., &ldquo;$5/$10&rdquo;) &mdash; blinds increase as you play</li>
                  <li><strong>Connection Status:</strong> Green dot shows you&apos;re connected to the server</li>
                  <li><strong>Settings (gear icon):</strong> Access hand analysis, session analysis, and step mode</li>
                  <li><strong>Help (?):</strong> Opens this guide in a new tab</li>
                  <li><strong>Quit (X):</strong> Leave the current game with option to analyze first</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Your Seat (Bottom Center)</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li><strong>Hole Cards:</strong> Your two private cards, face up</li>
                  <li><strong>Stack:</strong> Your total chips</li>
                  <li><strong>Current Bet:</strong> How much you&apos;ve bet this round</li>
                  <li><strong>Yellow Border:</strong> Indicates it&apos;s your turn to act</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Opponent Seats</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li>Cards are hidden (face down) until showdown</li>
                  <li>Watch for betting patterns and stack sizes</li>
                  <li>Yellow border shows whose turn it is</li>
                  <li>Each AI has a unique personality that affects their strategy</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Table Center</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li><strong>Community Cards:</strong> Up to 5 shared cards dealt in stages (Flop, Turn, River)</li>
                  <li><strong>Pot:</strong> Total chips in play</li>
                  <li><strong>Stage Label:</strong> Shows current stage (FLOP, TURN, RIVER) above the cards</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Position Indicators</h3>
                <div className="flex gap-4 mt-2 flex-wrap">
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
                    <p className="text-sm font-semibold text-blue-700">Call / Check</p>
                    <p className="text-sm text-gray-700">Match the current bet to stay in the hand. Shows &ldquo;Check&rdquo; when there&apos;s no bet to match (free to stay in).</p>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-green-700">Raise</p>
                    <p className="text-sm text-gray-700">Increase the bet. Use the raise panel to pick your amount, then click &ldquo;Confirm Raise&rdquo;.</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Raise Presets</h3>
                <p className="text-sm text-gray-700 mb-2">Quick-select buttons for common raise sizes:</p>
                <div className="flex flex-wrap gap-2">
                  <span className="bg-gray-200 text-gray-700 px-3 py-1 rounded text-xs font-medium">Min</span>
                  <span className="bg-gray-200 text-gray-700 px-3 py-1 rounded text-xs font-medium">1/2 Pot</span>
                  <span className="bg-gray-200 text-gray-700 px-3 py-1 rounded text-xs font-medium">Pot</span>
                  <span className="bg-gray-200 text-gray-700 px-3 py-1 rounded text-xs font-medium">2x Pot</span>
                  <span className="bg-gray-200 text-gray-700 px-3 py-1 rounded text-xs font-medium">All-In</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">You can also use the slider to set a custom raise amount.</p>
              </div>

              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <p className="text-sm text-blue-900">
                  <strong>Tip:</strong> Going &ldquo;All-In&rdquo; bets all your remaining chips. You can&apos;t be forced out of the hand, but you can only win up to what you&apos;ve contributed to the pot.
                </p>
              </div>
            </div>
          </section>

          {/* Winner Modal & Showdown */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Hand Results &amp; Showdown</h2>

            <div className="space-y-4">
              <p className="text-gray-700">
                When a hand ends, a results modal shows who won and how.
              </p>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">What You&apos;ll See</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li><strong>Winner &amp; Amount:</strong> Who won and how much they collected</li>
                  <li><strong>Board:</strong> The community cards for that hand</li>
                  <li><strong>Showdown Results:</strong> All remaining players&apos; hands ranked best to worst, with their hole cards revealed</li>
                  <li><strong>Folded Players:</strong> Who folded during the hand (no cards shown)</li>
                  <li><strong>Split Pot:</strong> When two or more players tie, the pot is split evenly</li>
                </ul>
              </div>

              <p className="text-sm text-gray-700">
                Click <strong>&ldquo;Next Hand&rdquo;</strong> to deal a new hand. The dealer button rotates, new cards are dealt, and blinds are posted automatically.
              </p>
            </div>
          </section>

          {/* AI Reasoning */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">AI Reasoning Panel</h2>

            <div className="space-y-4">
              <p className="text-gray-700">
                Click <strong>&ldquo;Show AI Reasoning&rdquo;</strong> below the action controls to see real-time AI decision-making. This is the best feature for learning poker strategy.
              </p>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">What You&apos;ll See</h3>
                <ul className="text-sm text-gray-700 space-y-2 ml-4 list-disc">
                  <li><strong>AI Name:</strong> Which opponent made the decision</li>
                  <li><strong>Action:</strong> Fold, Call, or Raise with the amount</li>
                  <li><strong>SPR:</strong> Stack-to-Pot Ratio &mdash; a key metric for decision-making</li>
                  <li><strong>Hand Strength:</strong> AI&apos;s estimated hand strength (percentage)</li>
                  <li><strong>Pot Odds:</strong> The mathematical odds the pot is offering</li>
                  <li><strong>Reasoning:</strong> A text explanation of why the AI made this decision</li>
                </ul>
              </div>

              <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
                <p className="text-sm text-green-900">
                  <strong>Learning Tip:</strong> Watch how different AI personalities react to the same situations. Some fold often, others bluff aggressively &mdash; learning to read these patterns is how you improve!
                </p>
              </div>
            </div>
          </section>

          {/* AI Coaching & Analysis */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">AI Coaching &amp; Analysis</h2>

            <div className="space-y-4">
              <p className="text-gray-700">
                Get AI-powered feedback on your play. Access these from the <strong>Settings (gear)</strong> menu during a game, or from the Game History page after a game ends.
              </p>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Hand Analysis</h3>
                <p className="text-sm text-gray-700 mb-2">
                  Select <strong>&ldquo;Analyze Last Hand&rdquo;</strong> from the settings menu to get a detailed AI review of the most recent hand. Includes:
                </p>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li>Round-by-round breakdown with commentary</li>
                  <li>Your good decisions highlighted in green</li>
                  <li>Areas to improve highlighted in yellow</li>
                  <li>Opponent insights and exploitation tips</li>
                  <li>Concepts to study, ranked by priority</li>
                </ul>
                <p className="text-xs text-gray-500 mt-2">Analysis takes 20&ndash;30 seconds. Requires an active internet connection.</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Session Analysis</h3>
                <p className="text-sm text-gray-700 mb-2">
                  Select <strong>&ldquo;Session Analysis&rdquo;</strong> from the settings menu to review your entire session. Available in two modes:
                </p>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li><strong>Quick:</strong> Fast overview with key stats and patterns (20&ndash;30 seconds)</li>
                  <li><strong>Deep:</strong> Thorough analysis with detailed recommendations (30&ndash;40 seconds)</li>
                </ul>
                <p className="text-sm text-gray-700 mt-2">Shows your Win Rate, VPIP, PFR, top strengths, biggest leaks, and a coach&apos;s overall assessment.</p>
              </div>

              <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded">
                <p className="text-sm text-purple-900">
                  <strong>Pro Tip:</strong> You can also run session analysis on completed games from the <strong>Game History</strong> page &mdash; great for reviewing older sessions.
                </p>
              </div>
            </div>
          </section>

          {/* Game History */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Game History</h2>

            <div className="space-y-4">
              <p className="text-gray-700">
                Access <strong>&ldquo;View Game History&rdquo;</strong> from the home screen to see all your past games.
              </p>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">What&apos;s Tracked</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li>Date and time of each game</li>
                  <li>Number of AI opponents</li>
                  <li>Total hands played</li>
                  <li>Starting and ending stack</li>
                  <li>Net profit or loss (color-coded green/red)</li>
                </ul>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Actions</h3>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
                  <li><strong>Review:</strong> Step through each hand with details and AI analysis</li>
                  <li><strong>Analyze:</strong> Run a session analysis on the completed game</li>
                  <li><strong>Clear All:</strong> Delete all game history (with confirmation)</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Quitting & Settings */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Quitting &amp; Account</h2>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Quitting a Game</h3>
                <p className="text-sm text-gray-700">
                  Click the <strong>Quit (X)</strong> button in the game header. You&apos;ll see three options:
                </p>
                <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc mt-2">
                  <li><strong>Analyze Session First:</strong> Get an AI review before leaving</li>
                  <li><strong>Just Quit:</strong> Save your game and return to the lobby</li>
                  <li><strong>Cancel:</strong> Go back to the game</li>
                </ul>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Settings Page</h3>
                <p className="text-sm text-gray-700">
                  Access from the home screen. View your account info and manage your account, including the option to permanently delete your account and all game history.
                </p>
              </div>
            </div>
          </section>

          {/* AI Personalities */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">AI Opponents</h2>

            <div className="space-y-4">
              <p className="text-gray-700">
                Each AI opponent has a distinct personality and strategy. Learning to identify and exploit their tendencies is key to improving your game.
              </p>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Personalities You&apos;ll Face</h3>
                <div className="text-sm text-gray-700 space-y-2">
                  <p><strong>Stone Face (Tight-Passive):</strong> Plays few hands, rarely bluffs. When they bet big, they usually have a strong hand.</p>
                  <p><strong>Bluff Master (Loose-Aggressive):</strong> Plays many hands aggressively. Hard to read because they bet with both strong and weak hands.</p>
                  <p><strong>Call Carl (Loose-Passive):</strong> Calls a lot but rarely raises. Easy to exploit by value betting.</p>
                  <p><strong>Raise Rachel (Tight-Aggressive):</strong> Selective but aggressive when she plays. A solid, dangerous opponent.</p>
                  <p><strong>Deep Blue (Mathematical):</strong> Makes decisions based on pot odds, hand strength, and SPR. The most technically sound opponent.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Tips & Tricks */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Tips for Learning</h2>

            <div className="space-y-3">
              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">1.</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Watch AI Reasoning</p>
                  <p className="text-sm text-gray-700">Open the AI reasoning panel to understand why opponents fold, call, or raise</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">2.</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Start with 4 Players</p>
                  <p className="text-sm text-gray-700">Fewer players means faster hands and simpler decisions while you learn</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">3.</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Use Hand Analysis After Key Hands</p>
                  <p className="text-sm text-gray-700">After a big win or tough loss, open the settings menu and run &ldquo;Analyze Last Hand&rdquo; for coaching</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">4.</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Review Sessions After Playing</p>
                  <p className="text-sm text-gray-700">Run session analysis at the end of a game or from history to spot patterns in your play</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">5.</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Learn SPR (Stack-to-Pot Ratio)</p>
                  <p className="text-sm text-gray-700">Understanding SPR helps you decide how committed to be in a hand &mdash; see the tutorial for details</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-1">6.</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Take Your Time</p>
                  <p className="text-sm text-gray-700">There&apos;s no timer &mdash; think through each decision and learn at your own pace</p>
                </div>
              </div>
            </div>
          </section>

          {/* Common Questions */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Common Questions</h2>

            <div className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-gray-800">Why can&apos;t I raise more than my stack?</p>
                <p className="text-sm text-gray-700">You can only bet chips you have. Use the &ldquo;All-In&rdquo; button to bet everything.</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-800">Why did the blinds increase?</p>
                <p className="text-sm text-gray-700">Blinds escalate as you play more hands (e.g., $5/$10 to $10/$20). This keeps the game moving and prevents overly passive play.</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-800">Why did the AI fold with seemingly good cards?</p>
                <p className="text-sm text-gray-700">Each AI has a different strategy. Open the AI reasoning panel to see exactly why they made that decision.</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-800">What happens when I run out of chips?</p>
                <p className="text-sm text-gray-700">When your stack reaches zero, you&apos;re eliminated and the game ends. You&apos;ll see your final results and can analyze your session.</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-800">How do I access the tutorial?</p>
                <p className="text-sm text-gray-700">From the home screen, click &ldquo;Tutorial&rdquo; to learn hand rankings, basic strategy, and the SPR concept.</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-800">Can I review past games?</p>
                <p className="text-sm text-gray-700">Yes! Go to &ldquo;View Game History&rdquo; from the home screen. You can review individual hands and run AI analysis on any completed game.</p>
              </div>
            </div>
          </section>

          {/* Bottom navigation */}
          <div className="flex justify-center pt-4">
            {backButton}
          </div>
        </div>
      </div>
  );
}

export default function GuidePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-700 to-blue-900">
      <Suspense fallback={
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-white rounded-2xl shadow-2xl p-6">
            <h1 className="text-3xl font-bold text-gray-800">How to Use This App</h1>
            <p className="text-gray-600 mt-2">Loading...</p>
          </div>
        </div>
      }>
        <GuideContent />
      </Suspense>
    </div>
  );
}
