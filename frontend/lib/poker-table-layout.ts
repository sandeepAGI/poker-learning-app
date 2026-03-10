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
 * Centered above middle (centerY: 38%) to prevent community card / hero overlap
 * radiusX: 40% (leaves safety margin near control panel)
 * radiusY: 30% (prevents hero from clipping below viewport)
 */
export const DEFAULT_ELLIPSE_CONFIG: EllipseConfig = {
  centerX: 50,
  centerY: 38,
  radiusX: 40,
  radiusY: 30
};

/**
 * Calculate elliptical positions for opponents
 * Distributes players across a wide arc that uses lower quadrants too.
 * 4-player (3 opponents): ~240° arc (from 210° to -30°)
 * 6-player (5 opponents): ~280° arc (from 220° to -60°)
 * A gap is left at the bottom (270°) where the human hero sits.
 *
 * Formula: (x, y) = (cx + rx*cos(θ), cy - ry*sin(θ))
 * Note: Y is subtracted because CSS Y-axis is inverted (0 at top)
 *
 * @param numOpponents - Number of AI opponents (typically 1, 3, or 5)
 * @param config - Ellipse configuration (optional, uses defaults if not provided)
 * @returns Array of position objects for each opponent
 */
export function calculateOpponentPositions(
  numOpponents: number,
  config: EllipseConfig = DEFAULT_ELLIPSE_CONFIG
): PlayerPosition[] {
  // Edge case: single opponent (heads-up poker)
  if (numOpponents === 1) {
    return [{
      left: `${config.centerX.toFixed(2)}%`,
      top: `${(config.centerY - config.radiusY).toFixed(2)}%`,
      transform: 'translate(-50%, -50%)'
    }];
  }

  // Full-ellipse placement: wider arcs that use lower quadrants
  // 4-player (3 opponents): 240° arc (210° to -30°) — uses lower-left and lower-right
  // 6-player (5 opponents): 280° arc (230° to -50°) — even wider spread
  // Safety: reserve gap around 270° (bottom) where the hero sits
  const arcSize = numOpponents <= 3 ? 240 : 280;
  const startAngle = numOpponents <= 3 ? 210 : 230;  // Left-lower quadrant
  const endAngle = startAngle - arcSize;               // Right-lower quadrant
  const angleStep = arcSize / (numOpponents - 1);

  return Array.from({ length: numOpponents }, (_, i) => {
    const angleDeg = startAngle - i * angleStep;
    const angleRad = (angleDeg * Math.PI) / 180;

    const x = config.centerX + config.radiusX * Math.cos(angleRad);
    const y = config.centerY - config.radiusY * Math.sin(angleRad);

    return {
      left: `${x.toFixed(2)}%`,
      top: `${y.toFixed(2)}%`,
      transform: 'translate(-50%, -50%)'
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
 * Positioned at ellipse center
 *
 * @returns Position object for center area
 */
export function getCenterAreaPosition(config: EllipseConfig = DEFAULT_ELLIPSE_CONFIG): PlayerPosition {
  return {
    left: `${config.centerX}%`,
    top: `${config.centerY}%`,
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
  viewportHeight: number,
  headerHeight: number = 0
): { width: string; height: string } {
  const aspectRatio = 16 / 10;
  const padding = 32; // 2rem total padding

  const availableWidth = Math.min(viewportWidth - padding, 1400);
  const availableHeight = viewportHeight - headerHeight - padding;

  // Width-driven dimensions
  const wWidth = availableWidth;
  const wHeight = wWidth / aspectRatio;

  // Height-driven dimensions
  const hHeight = availableHeight;
  const hWidth = hHeight * aspectRatio;

  // Pick the one that fits in both dimensions
  let finalWidth: number;
  let finalHeight: number;

  if (wHeight <= availableHeight) {
    // Width-driven fits vertically — use it (maximizes table size)
    finalWidth = wWidth;
    finalHeight = wHeight;
  } else {
    // Height-constrained — derive width from height
    finalWidth = Math.min(hWidth, availableWidth);
    finalHeight = finalWidth / aspectRatio;
  }

  return {
    width: `${finalWidth}px`,
    height: `${finalHeight}px`
  };
}
