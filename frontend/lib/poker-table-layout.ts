/**
 * Poker Table Elliptical Layout Utilities
 *
 * Calculates positions for poker table elements using elliptical mathematics.
 * Opponents are distributed evenly across a 180° arc (top-left to top-right).
 * Human player is positioned at bottom-center.
 */

export interface EllipseConfig {
  centerX: number;      // % of container width (default: 50)
  centerY: number;      // % of container height (default: 40)
  radiusX: number;      // Horizontal radius % (default: 42)
  radiusY: number;      // Vertical radius % (default: 28)
}

export interface PlayerPosition {
  left: string;         // CSS left value (e.g., "50%")
  top: string;          // CSS top value (e.g., "15%")
  transform: string;    // CSS transform (centering)
}

/**
 * Default ellipse configuration for poker table
 * Centered slightly above middle (centerY: 40%) for visual balance
 * radiusX: 40% (optimized for 75/25 split - balanced horizontal distribution)
 * radiusY: 30% (slightly increased vertical radius for better spacing)
 */
export const DEFAULT_ELLIPSE_CONFIG: EllipseConfig = {
  centerX: 50,
  centerY: 40,
  radiusX: 40,
  radiusY: 30
};

/**
 * Calculate elliptical positions for opponents
 * Distributes players evenly across 180° arc (top-left to top-right)
 *
 * Formula: (x, y) = (cx + rx*cos(θ), cy - ry*sin(θ))
 * Note: Y is subtracted because CSS Y-axis is inverted (0 at top)
 *
 * @param numOpponents - Number of AI opponents (typically 1, 3, or 5)
 * @param config - Ellipse configuration (optional, uses defaults if not provided)
 * @returns Array of position objects for each opponent
 *
 * @example
 * // 3 opponents (4-player table)
 * const positions = calculateOpponentPositions(3);
 * // Returns: [
 * //   { left: "8.00%", top: "40.00%", ... },   // Left side (180°)
 * //   { left: "50.00%", top: "12.00%", ... },  // Top center (90°)
 * //   { left: "92.00%", top: "40.00%", ... }   // Right side (0°)
 * // ]
 */
export function calculateOpponentPositions(
  numOpponents: number,
  config: EllipseConfig = DEFAULT_ELLIPSE_CONFIG
): PlayerPosition[] {
  // Edge case: single opponent (heads-up poker)
  if (numOpponents === 1) {
    return [{
      left: '50%',
      top: '8%',
      transform: 'translate(-50%, -50%)'
    }];
  }

  // Distribute opponents across arc (wider for more players)
  // 4-player (3 opponents): 180° arc works well
  // 6-player (5 opponents): 220° arc prevents overlap
  const arcSize = numOpponents <= 3 ? 180 : 220;
  const startAngle = arcSize === 180 ? 180 : 200;  // Left side
  const endAngle = arcSize === 180 ? 0 : -20;      // Right side (negative = below horizontal)
  const angleStep = (startAngle - endAngle) / (numOpponents - 1);

  return Array.from({ length: numOpponents }, (_, i) => {
    // Calculate angle for this opponent
    const angleDeg = startAngle - i * angleStep;
    const angleRad = (angleDeg * Math.PI) / 180;

    // Elliptical formula: (x, y) = (cx + rx*cos(θ), cy - ry*sin(θ))
    // Note: Subtract sin(θ) because CSS Y-axis is inverted (0 at top)
    const x = config.centerX + config.radiusX * Math.cos(angleRad);
    const y = config.centerY - config.radiusY * Math.sin(angleRad);

    return {
      left: `${x.toFixed(2)}%`,
      top: `${y.toFixed(2)}%`,
      transform: 'translate(-50%, -50%)' // Center the element on the calculated point
    };
  });
}

/**
 * Get human player position (always at bottom of ellipse)
 * Uses ellipse formula at 270° (bottom center)
 *
 * @returns Position object for human player
 */
export function getHumanPlayerPosition(config: EllipseConfig = DEFAULT_ELLIPSE_CONFIG): PlayerPosition {
  // Human player at 270° (bottom of ellipse)
  const angleRad = (270 * Math.PI) / 180;

  // Elliptical formula: (x, y) = (cx + rx*cos(θ), cy - ry*sin(θ))
  const x = config.centerX + config.radiusX * Math.cos(angleRad);
  const y = config.centerY - config.radiusY * Math.sin(angleRad);

  return {
    left: `${x.toFixed(2)}%`,
    top: `${y.toFixed(2)}%`,
    transform: 'translate(-50%, -50%)'
  };
}

/**
 * Get center area position (community cards)
 * Positioned at ellipse center (matches DEFAULT_ELLIPSE_CONFIG.centerY)
 *
 * @returns Position object for center area
 */
export function getCenterAreaPosition(): PlayerPosition {
  return {
    left: '50%',
    top: '40%', // Match ellipse centerY
    transform: 'translate(-50%, -50%)'
  };
}

/**
 * Calculate container size to fit viewport
 * Maintains 16:10 aspect ratio while fitting in available space
 *
 * @param viewportWidth - Available viewport width (px)
 * @param viewportHeight - Available viewport height (px)
 * @returns Object with width and height strings
 */
export function calculateContainerSize(
  viewportWidth: number,
  viewportHeight: number
): { width: string; height: string } {
  const aspectRatio = 16 / 10;
  const padding = 32; // 2rem total padding

  // Try fitting by width first
  const widthConstrainedWidth = Math.min(viewportWidth - padding, 1400);
  const widthConstrainedHeight = widthConstrainedWidth / aspectRatio;

  // Check if height fits
  if (widthConstrainedHeight <= viewportHeight * 0.85) {
    return {
      width: `${widthConstrainedWidth}px`,
      height: `${widthConstrainedHeight}px`
    };
  }

  // Fit by height instead
  const heightConstrainedHeight = viewportHeight * 0.85;
  const heightConstrainedWidth = heightConstrainedHeight * aspectRatio;

  return {
    width: `${heightConstrainedWidth}px`,
    height: `${heightConstrainedHeight}px`
  };
}
