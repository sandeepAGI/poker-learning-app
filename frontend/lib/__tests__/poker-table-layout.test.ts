/**
 * Unit tests for poker table elliptical layout utilities
 */

import {
  calculateOpponentPositions,
  getHumanPlayerPosition,
  getCenterAreaPosition,
  calculateContainerSize,
  DEFAULT_ELLIPSE_CONFIG,
  type EllipseConfig
} from '../poker-table-layout';

describe('calculateOpponentPositions', () => {
  describe('with 3 opponents (4-player table) — 240° arc', () => {
    it('should return exactly 3 positions', () => {
      const positions = calculateOpponentPositions(3);
      expect(positions).toHaveLength(3);
    });

    it('should position first opponent in lower-left quadrant (~210°)', () => {
      const positions = calculateOpponentPositions(3);
      const pos = positions[0];
      // 210°: cos(210°) ≈ -0.866, sin(210°) = -0.5
      // x = 50 + 40*(-0.866) ≈ 15.4, y = 42 - 32*(-0.5) = 58
      expect(parseFloat(pos.left)).toBeGreaterThan(12);
      expect(parseFloat(pos.left)).toBeLessThan(22);
      expect(parseFloat(pos.top)).toBeGreaterThan(50);
      expect(parseFloat(pos.top)).toBeLessThan(65);
    });

    it('should position second opponent at top center (~90°)', () => {
      const positions = calculateOpponentPositions(3);
      const pos = positions[1];
      // 90°: cos(90°) ≈ 0, sin(90°) = 1
      // x ≈ 50, y = 42 - 32 = 10
      expect(parseFloat(pos.left)).toBeCloseTo(50, 0);
      expect(parseFloat(pos.top)).toBeLessThan(15);
    });

    it('should position third opponent in lower-right quadrant (~-30°)', () => {
      const positions = calculateOpponentPositions(3);
      const pos = positions[2];
      // -30°: cos(-30°) ≈ 0.866, sin(-30°) = -0.5
      // x = 50 + 40*(0.866) ≈ 84.6, y = 42 - 32*(-0.5) = 58
      expect(parseFloat(pos.left)).toBeGreaterThan(78);
      expect(parseFloat(pos.left)).toBeLessThan(90);
      expect(parseFloat(pos.top)).toBeGreaterThan(50);
      expect(parseFloat(pos.top)).toBeLessThan(65);
    });

    it('should have symmetric left and right positions', () => {
      const positions = calculateOpponentPositions(3);
      const leftX = parseFloat(positions[0].left);
      const rightX = parseFloat(positions[2].left);
      // Symmetric around 50%
      expect(leftX + rightX).toBeCloseTo(100, 0);

      // Symmetric Y values
      const leftY = parseFloat(positions[0].top);
      const rightY = parseFloat(positions[2].top);
      expect(leftY).toBeCloseTo(rightY, 0);
    });

    it('should place opponents in multiple quadrants (not just top arc)', () => {
      const positions = calculateOpponentPositions(3);
      // At least one opponent should be in lower half (top > 42% center)
      const hasLowerQuadrant = positions.some(p => parseFloat(p.top) > 42);
      expect(hasLowerQuadrant).toBe(true);
    });

    it('should use translate(-50%, -50%) for all positions', () => {
      const positions = calculateOpponentPositions(3);
      positions.forEach(position => {
        expect(position.transform).toBe('translate(-50%, -50%)');
      });
    });
  });

  describe('with 5 opponents (6-player table) — 280° arc', () => {
    it('should return exactly 5 positions', () => {
      const positions = calculateOpponentPositions(5);
      expect(positions).toHaveLength(5);
    });

    it('should distribute across wider 280° arc', () => {
      const positions = calculateOpponentPositions(5);

      // Position 0: ~230° (lower-left)
      expect(parseFloat(positions[0].left)).toBeLessThan(30);
      expect(parseFloat(positions[0].top)).toBeGreaterThan(42);

      // Position 2: ~90° (top center)
      expect(parseFloat(positions[2].left)).toBeCloseTo(50, 0);
      expect(parseFloat(positions[2].top)).toBeLessThan(15);

      // Position 4: ~-50° (lower-right)
      expect(parseFloat(positions[4].left)).toBeGreaterThan(70);
      expect(parseFloat(positions[4].top)).toBeGreaterThan(42);
    });

    it('should have symmetric left and right positions', () => {
      const positions = calculateOpponentPositions(5);

      // First and last should be symmetric
      const leftX = parseFloat(positions[0].left);
      const rightX = parseFloat(positions[4].left);
      expect(leftX + rightX).toBeCloseTo(100, 0);

      // Second and fourth should be symmetric
      const topLeftX = parseFloat(positions[1].left);
      const topRightX = parseFloat(positions[3].left);
      expect(topLeftX + topRightX).toBeCloseTo(100, 0);
    });

    it('should place opponents in all four quadrants', () => {
      const positions = calculateOpponentPositions(5);
      // Upper-left: left < 50, top < 42
      const hasUpperLeft = positions.some(p => parseFloat(p.left) < 50 && parseFloat(p.top) < 42);
      // Upper-right: left > 50, top < 42
      const hasUpperRight = positions.some(p => parseFloat(p.left) > 50 && parseFloat(p.top) < 42);
      // Lower-left: left < 50, top > 42
      const hasLowerLeft = positions.some(p => parseFloat(p.left) < 50 && parseFloat(p.top) > 42);
      // Lower-right: left > 50, top > 42
      const hasLowerRight = positions.some(p => parseFloat(p.left) > 50 && parseFloat(p.top) > 42);

      expect(hasUpperLeft).toBe(true);
      expect(hasUpperRight).toBe(true);
      expect(hasLowerLeft).toBe(true);
      expect(hasLowerRight).toBe(true);
    });

    it('should keep safety margin from control panel (x < 95%)', () => {
      const positions = calculateOpponentPositions(5);
      positions.forEach(pos => {
        expect(parseFloat(pos.left)).toBeLessThan(95);
        expect(parseFloat(pos.left)).toBeGreaterThan(5);
      });
    });
  });

  describe('with 1 opponent (heads-up)', () => {
    it('should return single position at top center', () => {
      const positions = calculateOpponentPositions(1);
      expect(positions).toHaveLength(1);
      // x = centerX = 50, y = centerY - radiusY = 42 - 32 = 10
      expect(parseFloat(positions[0].left)).toBeCloseTo(50, 0);
      expect(parseFloat(positions[0].top)).toBeCloseTo(10, 0);
      expect(positions[0].transform).toBe('translate(-50%, -50%)');
    });
  });

  describe('with custom ellipse config', () => {
    it('should use custom centerX', () => {
      const customConfig: EllipseConfig = {
        centerX: 60,
        centerY: 42,
        radiusX: 40,
        radiusY: 32
      };

      const positions = calculateOpponentPositions(3, customConfig);
      // At 90° (middle opponent): x = 60 + 42*cos(90°) ≈ 60
      expect(parseFloat(positions[1].left)).toBeCloseTo(60, 0);
    });

    it('should use custom radiusY', () => {
      const customConfig: EllipseConfig = {
        centerX: 50,
        centerY: 42,
        radiusX: 40,
        radiusY: 20 // Flatter
      };

      const positions = calculateOpponentPositions(3, customConfig);
      // At 90°: y = 42 - 20*1 = 22
      expect(parseFloat(positions[1].top)).toBeCloseTo(22, 0);
    });
  });

  describe('with default config', () => {
    it('should use DEFAULT_ELLIPSE_CONFIG when not provided', () => {
      const positions = calculateOpponentPositions(3);
      const positionsWithDefault = calculateOpponentPositions(3, DEFAULT_ELLIPSE_CONFIG);
      expect(positions).toEqual(positionsWithDefault);
    });
  });
});

describe('getHumanPlayerPosition', () => {
  it('should return bottom-center position', () => {
    const position = getHumanPlayerPosition();
    // 270°: cos(270°) = 0 → x = 50, sin(270°) = -1 → y = 42 + 32 = 74
    expect(parseFloat(position.left)).toBeCloseTo(50, 0);
    expect(parseFloat(position.top)).toBeCloseTo(74, 0);
    expect(position.transform).toBe('translate(-50%, -50%)');
  });

  it('should be consistent across multiple calls', () => {
    const position1 = getHumanPlayerPosition();
    const position2 = getHumanPlayerPosition();
    expect(position1).toEqual(position2);
  });
});

describe('getCenterAreaPosition', () => {
  it('should return center position matching ellipse config', () => {
    const position = getCenterAreaPosition();
    expect(position.left).toBe(`${DEFAULT_ELLIPSE_CONFIG.centerX}%`);
    expect(position.top).toBe(`${DEFAULT_ELLIPSE_CONFIG.centerY}%`);
    expect(position.transform).toBe('translate(-50%, -50%)');
  });

  it('should be consistent across multiple calls', () => {
    const position1 = getCenterAreaPosition();
    const position2 = getCenterAreaPosition();
    expect(position1).toEqual(position2);
  });
});

describe('calculateContainerSize', () => {
  const aspectRatio = 16 / 10;

  describe('when width-constrained', () => {
    it('should fit within viewport width', () => {
      const result = calculateContainerSize(1000, 1000);
      const width = parseFloat(result.width);
      const height = parseFloat(result.height);
      expect(width).toBe(968);
      expect(width / height).toBeCloseTo(aspectRatio, 2);
    });

    it('should respect max width of 1400px', () => {
      const result = calculateContainerSize(2000, 2000);
      expect(parseFloat(result.width)).toBe(1400);
    });
  });

  describe('when height-constrained', () => {
    it('should fit within viewport height', () => {
      const result = calculateContainerSize(2000, 600);
      const width = parseFloat(result.width);
      const height = parseFloat(result.height);
      expect(height).toBe(510);
      expect(width / height).toBeCloseTo(aspectRatio, 2);
    });
  });

  describe('edge cases', () => {
    it('should handle very small viewports', () => {
      const result = calculateContainerSize(400, 600);
      const width = parseFloat(result.width);
      const height = parseFloat(result.height);
      expect(width).toBeGreaterThan(0);
      expect(height).toBeGreaterThan(0);
      expect(width / height).toBeCloseTo(aspectRatio, 2);
    });

    it('should handle very large viewports', () => {
      const result = calculateContainerSize(3000, 2000);
      expect(parseFloat(result.width)).toBe(1400);
    });
  });
});
