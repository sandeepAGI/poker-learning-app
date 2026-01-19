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
  describe('with 3 opponents (4-player table)', () => {
    it('should return exactly 3 positions', () => {
      const positions = calculateOpponentPositions(3);
      expect(positions).toHaveLength(3);
    });

    it('should position first opponent on left side (~180°)', () => {
      const positions = calculateOpponentPositions(3);
      const leftPosition = positions[0];

      // At 180°, cos(180°) = -1, so x = 50 + 42*(-1) = 8
      expect(parseFloat(leftPosition.left)).toBeLessThan(20);
      expect(parseFloat(leftPosition.left)).toBeGreaterThan(0);

      // At 180°, sin(180°) = 0, so y = 40 - 28*(0) = 40
      expect(parseFloat(leftPosition.top)).toBeCloseTo(40, 1);
    });

    it('should position second opponent at top center (~90°)', () => {
      const positions = calculateOpponentPositions(3);
      const topPosition = positions[1];

      // At 90°, cos(90°) = 0, so x = 50 + 42*(0) = 50
      expect(parseFloat(topPosition.left)).toBeCloseTo(50, 1);

      // At 90°, sin(90°) = 1, so y = 40 - 28*(1) = 12
      expect(parseFloat(topPosition.top)).toBeLessThan(20);
      expect(parseFloat(topPosition.top)).toBeGreaterThan(0);
    });

    it('should position third opponent on right side (~0°)', () => {
      const positions = calculateOpponentPositions(3);
      const rightPosition = positions[2];

      // At 0°, cos(0°) = 1, so x = 50 + 42*(1) = 92
      expect(parseFloat(rightPosition.left)).toBeGreaterThan(80);
      expect(parseFloat(rightPosition.left)).toBeLessThanOrEqual(100);

      // At 0°, sin(0°) = 0, so y = 40 - 28*(0) = 40
      expect(parseFloat(rightPosition.top)).toBeCloseTo(40, 1);
    });

    it('should use translate(-50%, -50%) for all positions', () => {
      const positions = calculateOpponentPositions(3);

      positions.forEach(position => {
        expect(position.transform).toBe('translate(-50%, -50%)');
      });
    });
  });

  describe('with 5 opponents (6-player table)', () => {
    it('should return exactly 5 positions', () => {
      const positions = calculateOpponentPositions(5);
      expect(positions).toHaveLength(5);
    });

    it('should distribute opponents evenly across 180° arc', () => {
      const positions = calculateOpponentPositions(5);

      // Position 0: Far left (~180°)
      expect(parseFloat(positions[0].left)).toBeLessThan(20);

      // Position 1: Top-left (~135°)
      expect(parseFloat(positions[1].left)).toBeGreaterThan(20);
      expect(parseFloat(positions[1].left)).toBeLessThan(50);

      // Position 2: Top center (~90°)
      expect(parseFloat(positions[2].left)).toBeCloseTo(50, 1);
      expect(parseFloat(positions[2].top)).toBeLessThan(20);

      // Position 3: Top-right (~45°)
      expect(parseFloat(positions[3].left)).toBeGreaterThan(50);
      expect(parseFloat(positions[3].left)).toBeLessThan(80);

      // Position 4: Far right (~0°)
      expect(parseFloat(positions[4].left)).toBeGreaterThan(80);
    });

    it('should have symmetric left and right positions', () => {
      const positions = calculateOpponentPositions(5);

      // Far left and far right should be symmetric around 50%
      const leftX = parseFloat(positions[0].left);
      const rightX = parseFloat(positions[4].left);
      expect(leftX + rightX).toBeCloseTo(100, 1);

      // Top-left and top-right should be symmetric
      const topLeftX = parseFloat(positions[1].left);
      const topRightX = parseFloat(positions[3].left);
      expect(topLeftX + topRightX).toBeCloseTo(100, 1);
    });
  });

  describe('with 1 opponent (heads-up)', () => {
    it('should return single position at top center', () => {
      const positions = calculateOpponentPositions(1);

      expect(positions).toHaveLength(1);
      expect(positions[0].left).toBe('50%');
      expect(positions[0].top).toBe('8%');
      expect(positions[0].transform).toBe('translate(-50%, -50%)');
    });
  });

  describe('with custom ellipse config', () => {
    it('should use custom centerX', () => {
      const customConfig: EllipseConfig = {
        centerX: 60, // Shifted right
        centerY: 40,
        radiusX: 42,
        radiusY: 28
      };

      const positions = calculateOpponentPositions(3, customConfig);
      const topPosition = positions[1];

      // At 90°, cos(90°) = 0, so x = 60 + 42*(0) = 60
      expect(parseFloat(topPosition.left)).toBeCloseTo(60, 1);
    });

    it('should use custom centerY', () => {
      const customConfig: EllipseConfig = {
        centerX: 50,
        centerY: 35, // Higher (smaller Y)
        radiusX: 42,
        radiusY: 28
      };

      const positions = calculateOpponentPositions(3, customConfig);
      const topPosition = positions[1];

      // At 90°, y = 35 - 28*(1) = 7
      expect(parseFloat(topPosition.top)).toBeLessThan(10);
    });

    it('should use custom radiusX', () => {
      const customConfig: EllipseConfig = {
        centerX: 50,
        centerY: 40,
        radiusX: 35, // Narrower
        radiusY: 28
      };

      const positions = calculateOpponentPositions(3, customConfig);
      const leftPosition = positions[0];

      // At 180°, x = 50 + 35*(-1) = 15
      expect(parseFloat(leftPosition.left)).toBeCloseTo(15, 1);
    });

    it('should use custom radiusY', () => {
      const customConfig: EllipseConfig = {
        centerX: 50,
        centerY: 40,
        radiusX: 42,
        radiusY: 20 // Flatter
      };

      const positions = calculateOpponentPositions(3, customConfig);
      const topPosition = positions[1];

      // At 90°, y = 40 - 20*(1) = 20
      expect(parseFloat(topPosition.top)).toBeCloseTo(20, 1);
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

    expect(position.left).toBe('50%');
    expect(position.top).toBe('92%');
    expect(position.transform).toBe('translate(-50%, -50%)');
  });

  it('should be consistent across multiple calls', () => {
    const position1 = getHumanPlayerPosition();
    const position2 = getHumanPlayerPosition();

    expect(position1).toEqual(position2);
  });
});

describe('getCenterAreaPosition', () => {
  it('should return center position', () => {
    const position = getCenterAreaPosition();

    expect(position.left).toBe('50%');
    expect(position.top).toBe('50%');
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

      // Width should be viewport - padding (1000 - 32 = 968)
      expect(width).toBe(968);

      // Height should maintain aspect ratio
      expect(width / height).toBeCloseTo(aspectRatio, 2);
    });

    it('should respect max width of 1400px', () => {
      const result = calculateContainerSize(2000, 2000);

      const width = parseFloat(result.width);

      // Should cap at 1400px
      expect(width).toBe(1400);
    });
  });

  describe('when height-constrained', () => {
    it('should fit within viewport height', () => {
      const result = calculateContainerSize(2000, 600);

      const width = parseFloat(result.width);
      const height = parseFloat(result.height);

      // Height should be 85% of viewport (600 * 0.85 = 510)
      expect(height).toBe(510);

      // Width should maintain aspect ratio
      expect(width / height).toBeCloseTo(aspectRatio, 2);
    });

    it('should use height constraint when width-constrained would overflow', () => {
      const result = calculateContainerSize(1200, 500);

      const height = parseFloat(result.height);

      // Height should be 85% of viewport (500 * 0.85 = 425)
      expect(height).toBe(425);
    });
  });

  describe('edge cases', () => {
    it('should handle very small viewports', () => {
      const result = calculateContainerSize(400, 600);

      const width = parseFloat(result.width);
      const height = parseFloat(result.height);

      // Should fit and maintain aspect ratio
      expect(width).toBeGreaterThan(0);
      expect(height).toBeGreaterThan(0);
      expect(width / height).toBeCloseTo(aspectRatio, 2);
    });

    it('should handle very large viewports', () => {
      const result = calculateContainerSize(3000, 2000);

      const width = parseFloat(result.width);

      // Should cap at 1400px max width
      expect(width).toBe(1400);
    });
  });
});
