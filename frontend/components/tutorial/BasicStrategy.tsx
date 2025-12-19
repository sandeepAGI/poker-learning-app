'use client';

export function BasicStrategy() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Basic Poker Strategy</h2>
        <p className="text-gray-600">
          Learn the fundamentals to make better decisions at the table.
        </p>
      </div>

      {/* Position */}
      <section className="bg-white border-2 border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-3">Position is Power</h3>
        <p className="text-gray-700 mb-4">
          Your position at the table determines when you act. Acting later is better because
          you have more information about what other players are doing.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-red-50 border border-red-200 rounded p-3">
            <h4 className="font-semibold text-red-800 mb-1">Early Position</h4>
            <p className="text-sm text-gray-700">Act first, least information. Play tight.</p>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
            <h4 className="font-semibold text-yellow-800 mb-1">Middle Position</h4>
            <p className="text-sm text-gray-700">Moderate information. Play moderately.</p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded p-3">
            <h4 className="font-semibold text-green-800 mb-1">Late Position (Button)</h4>
            <p className="text-sm text-gray-700">Act last, most information. Play more hands.</p>
          </div>
        </div>
      </section>

      {/* Starting Hands */}
      <section className="bg-white border-2 border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-3">Starting Hand Selection</h3>
        <p className="text-gray-700 mb-4">
          Not all starting hands are created equal. Here's a simple guide:
        </p>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-24 font-semibold text-green-700">Premium:</span>
            <span className="text-gray-700">
              AA, KK, QQ, JJ, AK suited - Raise from any position
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-24 font-semibold text-blue-700">Strong:</span>
            <span className="text-gray-700">
              TT, 99, AQ, AJ, KQ - Raise from middle/late position
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-24 font-semibold text-yellow-700">Decent:</span>
            <span className="text-gray-700">
              88, 77, AT, KJ, QJ, suited connectors - Call or raise from late position
            </span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-24 font-semibold text-red-700">Weak:</span>
            <span className="text-gray-700">
              Low pairs, weak aces (A2-A9 offsuit) - Fold from early position
            </span>
          </div>
        </div>
      </section>

      {/* Pot Odds */}
      <section className="bg-white border-2 border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-3">Pot Odds Basics</h3>
        <p className="text-gray-700 mb-4">
          Pot odds help you decide if calling a bet is profitable based on the pot size
          and the cost to call.
        </p>
        <div className="bg-gray-50 rounded p-4 mb-4">
          <p className="font-mono text-sm mb-2">
            Pot Odds = Cost to Call ÷ (Pot Size + Cost to Call)
          </p>
          <p className="text-sm text-gray-700 italic">
            Example: Pot is $100, opponent bets $20. You need to call $20 to win $120.
            <br />
            Pot odds = $20 ÷ $120 = 16.7% (you need to win more than 16.7% of the time)
          </p>
        </div>
        <p className="text-sm text-gray-600">
          If your chance of winning is better than your pot odds, calling is profitable.
          The AI uses pot odds to make mathematical decisions.
        </p>
      </section>

      {/* Expected Value */}
      <section className="bg-white border-2 border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-3">Expected Value (EV)</h3>
        <p className="text-gray-700 mb-4">
          EV tells you whether a play will make or lose money in the long run.
        </p>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">✅</span>
            <span className="text-gray-700">
              <strong>+EV (Positive):</strong> This play makes money long-term
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">❌</span>
            <span className="text-gray-700">
              <strong>-EV (Negative):</strong> This play loses money long-term
            </span>
          </div>
        </div>
        <div className="mt-4 bg-blue-50 border-l-4 border-blue-500 p-3 rounded">
          <p className="text-sm text-blue-900">
            The Mathematical AI personality focuses on making +EV plays by calculating
            pot odds and hand equity. Watch the AI thinking sidebar to see how it calculates EV.
          </p>
        </div>
      </section>

      {/* Quick Tips */}
      <section className="bg-green-50 border-2 border-green-300 rounded-lg p-6">
        <h3 className="text-xl font-bold text-green-800 mb-3">Quick Tips for Beginners</h3>
        <ul className="space-y-2">
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">💡</span>
            <span className="text-gray-700">Play fewer hands than you think - quality over quantity</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">💡</span>
            <span className="text-gray-700">Position matters more than your cards sometimes</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">💡</span>
            <span className="text-gray-700">Don't chase draws unless pot odds justify it</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">💡</span>
            <span className="text-gray-700">Watch AI reasoning to learn how they make decisions</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 mt-1">💡</span>
            <span className="text-gray-700">Fold when you're beat - saving chips is as important as winning them</span>
          </li>
        </ul>
      </section>
    </div>
  );
}
