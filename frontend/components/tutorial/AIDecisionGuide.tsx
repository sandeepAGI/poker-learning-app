'use client';

export function AIDecisionGuide() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">How AI Opponents Think</h2>
        <p className="text-gray-600">
          Learn how AI opponents make decisions and use advanced concepts like SPR.
        </p>
      </div>

      {/* SPR Explanation */}
      <section className="bg-white border-2 border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-3">Stack-to-Pot Ratio (SPR)</h3>
        <p className="text-gray-700 mb-4">
          SPR is one of the most important concepts in poker. It's the ratio of your stack
          size to the current pot size.
        </p>

        <div className="bg-gray-50 rounded p-4 mb-4">
          <p className="font-mono text-sm mb-2">
            SPR = Your Stack ÷ Pot Size
          </p>
          <p className="text-sm text-gray-700 italic">
            Example: You have $800, pot is $100. SPR = 800 ÷ 100 = 8
          </p>
        </div>

        <div className="space-y-4">
          <div className="border-l-4 border-red-500 bg-red-50 p-3 rounded">
            <h4 className="font-semibold text-red-800 mb-1">Low SPR (0-3)</h4>
            <p className="text-sm text-gray-700">
              Small stack relative to pot. You're pot-committed - even weak hands should
              go all-in. No room for complicated play.
            </p>
          </div>

          <div className="border-l-4 border-yellow-500 bg-yellow-50 p-3 rounded">
            <h4 className="font-semibold text-yellow-800 mb-1">Medium SPR (4-8)</h4>
            <p className="text-sm text-gray-700">
              Balanced stack. Good for playing strong hands aggressively. Top pair and
              better hands are usually worth committing to.
            </p>
          </div>

          <div className="border-l-4 border-green-500 bg-green-50 p-3 rounded">
            <h4 className="font-semibold text-green-800 mb-1">High SPR (9+)</h4>
            <p className="text-sm text-gray-700">
              Deep stack relative to pot. Only commit with very strong hands. More room
              for post-flop play and bluffing.
            </p>
          </div>
        </div>
      </section>

      {/* AI Personalities */}
      <section className="bg-white border-2 border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-3">AI Personalities</h3>
        <p className="text-gray-700 mb-4">
          Each AI opponent has a distinct playing style. Understanding them helps you predict
          their moves.
        </p>

        <div className="space-y-4">
          {/* Conservative */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🛡️</span>
              <h4 className="text-lg font-bold text-blue-800">Conservative AI</h4>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              Plays tight and cautious. Only bets with strong hands.
            </p>
            <div className="text-xs space-y-1">
              <p><strong>Low SPR:</strong> Only goes all-in with premium hands (AA, KK, QQ)</p>
              <p><strong>Medium SPR:</strong> Plays top pair carefully, folds to heavy pressure</p>
              <p><strong>High SPR:</strong> Only commits with very strong hands, folds frequently</p>
            </div>
            <div className="mt-2 text-xs bg-white rounded p-2">
              <strong>Tell:</strong> If Conservative AI raises, they have a real hand. Respect their bets.
            </div>
          </div>

          {/* Aggressive */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">⚔️</span>
              <h4 className="text-lg font-bold text-red-800">Aggressive AI</h4>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              Plays loose and aggressive. Bets, raises, and bluffs frequently.
            </p>
            <div className="text-xs space-y-1">
              <p><strong>Low SPR:</strong> Goes all-in with any pair or decent draw</p>
              <p><strong>Medium SPR:</strong> Continuation bets frequently, raises on draws</p>
              <p><strong>High SPR:</strong> Makes big bluffs, applies maximum pressure</p>
            </div>
            <div className="mt-2 text-xs bg-white rounded p-2">
              <strong>Tell:</strong> Don't believe every bet - Aggressive AI bluffs often. Call them down with decent hands.
            </div>
          </div>

          {/* Mathematical */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">📊</span>
              <h4 className="text-lg font-bold text-purple-800">Mathematical AI</h4>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              Makes decisions based on math: pot odds, expected value, hand equity.
            </p>
            <div className="text-xs space-y-1">
              <p><strong>Pot Odds:</strong> Calls draws only when odds justify it</p>
              <p><strong>EV Calculation:</strong> Folds if expected value is negative</p>
              <p><strong>Hand Strength:</strong> Adjusts bet sizing based on estimated equity</p>
            </div>
            <div className="mt-2 text-xs bg-white rounded p-2">
              <strong>Tell:</strong> Mathematical AI is balanced and unpredictable. Their bets are always sized for value.
            </div>
          </div>

          {/* Loose-Passive */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🐟</span>
              <h4 className="text-lg font-bold text-yellow-800">Loose-Passive AI (Calling Station)</h4>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              Calls too often, rarely raises. Shows what NOT to do - a common beginner mistake.
            </p>
            <div className="text-xs space-y-1">
              <p><strong>Low SPR:</strong> Calls to see showdown, even with marginal hands</p>
              <p><strong>Medium/High SPR:</strong> Calls almost any bet if it's small enough</p>
              <p><strong>Strategy:</strong> Rarely folds, rarely raises - just calls and calls</p>
            </div>
            <div className="mt-2 text-xs bg-white rounded p-2">
              <strong>Tell:</strong> Easy to beat! Value bet your strong hands - they'll call. Don't bluff - they never fold.
            </div>
          </div>

          {/* Tight-Aggressive */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🎯</span>
              <h4 className="text-lg font-bold text-green-800">Tight-Aggressive AI (TAG)</h4>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              Premium hands only, but aggressive when playing. The most profitable poker style.
            </p>
            <div className="text-xs space-y-1">
              <p><strong>Hand Selection:</strong> Folds marginal hands, only plays top 20%</p>
              <p><strong>Low SPR:</strong> Goes all-in with strong hands (trips or better)</p>
              <p><strong>High SPR:</strong> Raises for value, folds to heavy resistance</p>
            </div>
            <div className="mt-2 text-xs bg-white rounded p-2">
              <strong>Tell:</strong> Disciplined and profitable. If TAG is in the hand, respect their strength.
            </div>
          </div>

          {/* Maniac */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🔥</span>
              <h4 className="text-lg font-bold text-orange-800">Maniac AI</h4>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              Hyper-aggressive chaos. Raises and bluffs 70%+ of the time - high variance!
            </p>
            <div className="text-xs space-y-1">
              <p><strong>Any SPR:</strong> Raises constantly, applies maximum pressure</p>
              <p><strong>Bluff Rate:</strong> 70% of hands are pure bluffs</p>
              <p><strong>Strategy:</strong> Keeps opponents guessing, creates big pots</p>
            </div>
            <div className="mt-2 text-xs bg-white rounded p-2">
              <strong>Tell:</strong> Don't fold to every raise! Maniac bluffs constantly - call them down with any decent hand.
            </div>
          </div>
        </div>

        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>💡 Note:</strong> Each game randomly assigns different AI personalities, so you'll face
            a variety of playing styles. Learn to adapt to each opponent!
          </p>
        </div>
      </section>

      {/* Example Scenarios */}
      <section className="bg-white border-2 border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-3">Example AI Decisions</h3>
        <p className="text-gray-700 mb-4">
          See how different AI personalities react to the same situation.
        </p>

        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <p className="text-sm font-semibold text-gray-800 mb-2">Scenario:</p>
          <p className="text-sm text-gray-700">
            SPR = 5, You have Q♠ J♠, Flop comes K♠ 10♠ 3♣ (flush draw + straight draw).
            Pot is $100, opponent bets $60.
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-32 text-sm font-semibold text-blue-700">Conservative:</span>
            <span className="text-sm text-gray-700">
              FOLD - "No made hand, too risky even with draws. Not worth the money."
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-32 text-sm font-semibold text-red-700">Aggressive:</span>
            <span className="text-sm text-gray-700">
              RAISE to $180 - "Great bluffing opportunity with equity backup. Push them out!"
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-32 text-sm font-semibold text-purple-700">Mathematical:</span>
            <span className="text-sm text-gray-700">
              CALL - "15 outs (45% to hit), pot odds 37%. +EV call, let's see the turn."
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-32 text-sm font-semibold text-yellow-700">Loose-Passive:</span>
            <span className="text-sm text-gray-700">
              CALL - "Lots of outs, let's see what happens. Calling is safe."
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-32 text-sm font-semibold text-green-700">Tight-Aggressive:</span>
            <span className="text-sm text-gray-700">
              FOLD - "No made hand, below TAG threshold. Disciplined fold."
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-32 text-sm font-semibold text-orange-700">Maniac:</span>
            <span className="text-sm text-gray-700">
              RAISE to $240 - "Bluffing with equity backup! Maximum pressure, baby!"
            </span>
          </div>
        </div>
      </section>

      {/* Learning Tips */}
      <section className="bg-green-50 border-2 border-green-300 rounded-lg p-6">
        <h3 className="text-xl font-bold text-green-800 mb-3">Learning from AI</h3>
        <ul className="space-y-2">
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">📖</span>
            <span className="text-gray-700">
              <strong>Toggle AI Thinking:</strong> Click the sidebar icon to see AI reasoning in real-time
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">📖</span>
            <span className="text-gray-700">
              <strong>SPR Display:</strong> AI shows their SPR calculation before each decision
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">📖</span>
            <span className="text-gray-700">
              <strong>Hand Strength:</strong> See how AI estimates the strength of their hand (0.0 to 1.0)
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">📖</span>
            <span className="text-gray-700">
              <strong>Decision Logic:</strong> Each AI explains why they chose fold, call, or raise
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">📖</span>
            <span className="text-gray-700">
              <strong>Compare Styles:</strong> Watch how different personalities react to identical situations
            </span>
          </li>
        </ul>
      </section>
    </div>
  );
}
