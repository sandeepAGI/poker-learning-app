'use client';

export function HandRankings() {
  const rankings = [
    {
      rank: 1,
      name: "Royal Flush",
      description: "A, K, Q, J, 10 all of the same suit",
      example: "A♠ K♠ Q♠ J♠ 10♠",
      strength: "Unbeatable"
    },
    {
      rank: 2,
      name: "Straight Flush",
      description: "Five cards in sequence, all same suit",
      example: "9♥ 8♥ 7♥ 6♥ 5♥",
      strength: "Extremely strong"
    },
    {
      rank: 3,
      name: "Four of a Kind",
      description: "Four cards of the same rank",
      example: "K♠ K♥ K♦ K♣ 3♠",
      strength: "Very strong"
    },
    {
      rank: 4,
      name: "Full House",
      description: "Three of a kind plus a pair",
      example: "J♠ J♥ J♦ 8♣ 8♠",
      strength: "Strong"
    },
    {
      rank: 5,
      name: "Flush",
      description: "Five cards of the same suit, not in sequence",
      example: "K♦ 10♦ 7♦ 5♦ 2♦",
      strength: "Good"
    },
    {
      rank: 6,
      name: "Straight",
      description: "Five cards in sequence, mixed suits",
      example: "10♠ 9♥ 8♦ 7♣ 6♠",
      strength: "Good"
    },
    {
      rank: 7,
      name: "Three of a Kind",
      description: "Three cards of the same rank",
      example: "9♠ 9♥ 9♦ K♣ 4♠",
      strength: "Decent"
    },
    {
      rank: 8,
      name: "Two Pair",
      description: "Two different pairs",
      example: "Q♠ Q♥ 7♦ 7♣ 3♠",
      strength: "Decent"
    },
    {
      rank: 9,
      name: "One Pair",
      description: "Two cards of the same rank",
      example: "10♠ 10♥ A♦ 8♣ 5♠",
      strength: "Weak"
    },
    {
      rank: 10,
      name: "High Card",
      description: "No matching cards, highest card plays",
      example: "A♠ K♥ 9♦ 6♣ 3♠",
      strength: "Very weak"
    }
  ];

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case "Unbeatable":
      case "Extremely strong":
        return "text-green-700 bg-green-50";
      case "Very strong":
      case "Strong":
        return "text-blue-700 bg-blue-50";
      case "Good":
      case "Decent":
        return "text-yellow-700 bg-yellow-50";
      default:
        return "text-gray-700 bg-gray-50";
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Poker Hand Rankings</h2>
        <p className="text-gray-600">
          From strongest to weakest. The player with the best hand wins the pot.
        </p>
      </div>

      <div className="space-y-3">
        {rankings.map((hand) => (
          <div
            key={hand.rank}
            className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-green-500 transition-colors"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                {hand.rank}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-lg font-bold text-gray-800">{hand.name}</h3>
                  <span className={`text-xs font-semibold px-2 py-1 rounded ${getStrengthColor(hand.strength)}`}>
                    {hand.strength}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{hand.description}</p>
                <div className="bg-gray-50 rounded px-3 py-2 font-mono text-sm">
                  Example: {hand.example}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
        <p className="text-sm text-blue-900">
          <strong>Tip:</strong> When two players have the same hand type, the one with higher-ranking
          cards wins. For example, a pair of Kings beats a pair of 7s.
        </p>
      </div>
    </div>
  );
}
