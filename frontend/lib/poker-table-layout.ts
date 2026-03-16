/**
 * Poker Table Seat Layout Utilities
 *
 * Defines fixed seat positions for each player count.
 * Positions are percentages of the table container, which maintains
 * a fixed aspect ratio (16:10 desktop, 4:5 mobile) via calculateContainerSize().
 * Percentage-based positions therefore scale automatically on window resize.
 *
 * Seat order: opponents are assigned seats in array order (index 0 = first opponent).
 * The human player always sits at bottom-center.
 */

export interface PlayerPosition {
  left: string;       // CSS left value as percentage (e.g., "50%")
  top: string;        // CSS top value as percentage (e.g., "15%")
  transform: string;  // CSS transform for centering (always "translate(-50%, -50%)")
}

// ---------------------------------------------------------------------------
// Seat maps: [left%, top%] per seat, indexed by opponent seat number.
// Desktop (16:10 aspect ratio container)
// ---------------------------------------------------------------------------

// Ellipse geometry: center=(50,50), a=38 (horizontal), b=35 (vertical)
// Seat at angle θ: left = 50 + 38·cos(θ), top = 50 − 35·sin(θ)
// Hero at 6 o'clock (270°), opponents distributed evenly over remaining positions.
const DESKTOP_SEATS: Record<number, Array<[number, number]>> = {
  1: [
    [50, 15],   // 12 o'clock (90°)
  ],
  3: [
    [12, 50],   //  9 o'clock (180°)
    [50, 15],   // 12 o'clock (90°)
    [88, 50],   //  3 o'clock (0°)
  ],
  5: [
    [17, 33],   // 10 o'clock (150°)
    [50, 15],   // 12 o'clock (90°)
    [83, 33],   //  2 o'clock (30°)
    [17, 67],   //  8 o'clock (210°)
    [83, 67],   //  4 o'clock (330°)
  ],
};

// Mobile (4:5 aspect ratio container) — tighter semi-axes: a=36, b=33
const MOBILE_SEATS: Record<number, Array<[number, number]>> = {
  1: [
    [50, 17],   // 12 o'clock
  ],
  3: [
    [14, 50],   //  9 o'clock
    [50, 17],   // 12 o'clock
    [86, 50],   //  3 o'clock
  ],
  5: [
    [19, 34],   // 10 o'clock
    [50, 17],   // 12 o'clock
    [81, 34],   //  2 o'clock
    [19, 66],   //  8 o'clock
    [81, 66],   //  4 o'clock
  ],
};

// Human player seat: always 6 o'clock (270°) → top = 50 + 35 = 85, clamped to 82%
const HUMAN_DESKTOP: [number, number] = [50, 82];
const HUMAN_MOBILE:  [number, number] = [50, 80];

function toPosition([left, top]: [number, number]): PlayerPosition {
  return {
    left: `${left}%`,
    top: `${top}%`,
    transform: 'translate(-50%, -50%)',
  };
}

/**
 * Returns seat positions for AI opponents.
 *
 * @param numOpponents - Number of AI opponents (1, 3, or 5)
 * @param isMobile - Use tighter mobile layout (default: false)
 */
export function calculateOpponentPositions(
  numOpponents: number,
  isMobile: boolean = false
): PlayerPosition[] {
  const map = isMobile ? MOBILE_SEATS : DESKTOP_SEATS;
  const seats = map[numOpponents];

  if (!seats) {
    // Fallback: evenly distribute along top arc for unsupported counts
    console.warn(`No seat map for ${numOpponents} opponents, falling back`);
    return Array.from({ length: numOpponents }, (_, i) => ({
      left: `${10 + (i * 80) / Math.max(numOpponents - 1, 1)}%`,
      top: '15%',
      transform: 'translate(-50%, -50%)',
    }));
  }

  return seats.map(toPosition);
}

/**
 * Returns the human player's seat position (always bottom center).
 *
 * @param isMobile - Use mobile layout (default: false)
 */
export function getHumanPlayerPosition(isMobile: boolean = false): PlayerPosition {
  return toPosition(isMobile ? HUMAN_MOBILE : HUMAN_DESKTOP);
}

/**
 * Get center area position (community cards).
 * Positioned at 50% horizontal, 45% vertical — center of the table.
 */
export function getCenterAreaPosition(): PlayerPosition {
  return {
    left: '50%',
    top: '45%',
    transform: 'translate(-50%, -50%)',
  };
}

/**
 * Calculate container size to fit viewport while maintaining aspect ratio.
 * 16:10 on desktop, 4:5 on mobile.
 */
export function calculateContainerSize(
  viewportWidth: number,
  viewportHeight: number,
  headerHeight: number = 0,
  isMobile: boolean = false
): { width: string; height: string } {
  const aspectRatio = isMobile ? 4 / 5 : 16 / 10;
  const padding = isMobile ? 16 : 32;
  const bottomBarHeight = isMobile ? 140 : 0;

  const availableWidth = Math.min(viewportWidth - padding, 1400);
  const availableHeight = viewportHeight - headerHeight - padding - bottomBarHeight;

  const wWidth = availableWidth;
  const wHeight = wWidth / aspectRatio;

  const hHeight = availableHeight;
  const hWidth = hHeight * aspectRatio;

  let finalWidth: number;
  let finalHeight: number;

  if (wHeight <= availableHeight) {
    finalWidth = wWidth;
    finalHeight = wHeight;
  } else {
    finalWidth = Math.min(hWidth, availableWidth);
    finalHeight = finalWidth / aspectRatio;
  }

  return {
    width: `${finalWidth}px`,
    height: `${finalHeight}px`,
  };
}
