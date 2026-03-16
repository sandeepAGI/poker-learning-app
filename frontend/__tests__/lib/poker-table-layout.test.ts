import {
  calculateOpponentPositions,
  getHumanPlayerPosition,
} from '../../lib/poker-table-layout';

describe('calculateOpponentPositions', () => {
  describe('2-player (heads-up)', () => {
    it('returns 1 position', () => {
      expect(calculateOpponentPositions(1)).toHaveLength(1);
    });

    it('places single opponent at top center', () => {
      const [pos] = calculateOpponentPositions(1);
      const left = parseFloat(pos.left);
      const top = parseFloat(pos.top);
      expect(left).toBeCloseTo(50, 0);
      expect(top).toBeLessThan(25);
    });
  });

  describe('4-player (3 opponents)', () => {
    it('returns 3 positions', () => {
      expect(calculateOpponentPositions(3)).toHaveLength(3);
    });

    it('has one seat at the top (top < 25%)', () => {
      const positions = calculateOpponentPositions(3);
      const tops = positions.map(p => parseFloat(p.top));
      expect(tops.some(t => t < 25)).toBe(true);
    });

    it('has one seat on the left (left < 25%)', () => {
      const positions = calculateOpponentPositions(3);
      const lefts = positions.map(p => parseFloat(p.left));
      expect(lefts.some(l => l < 25)).toBe(true);
    });

    it('has one seat on the right (left > 60%)', () => {
      const positions = calculateOpponentPositions(3);
      const lefts = positions.map(p => parseFloat(p.left));
      expect(lefts.some(l => l > 60)).toBe(true);
    });

    it('left and right seats are at similar vertical height (within 10%)', () => {
      const positions = calculateOpponentPositions(3);
      const sorted = [...positions].sort((a, b) => parseFloat(a.left) - parseFloat(b.left));
      const leftTop = parseFloat(sorted[0].top);
      const rightTop = parseFloat(sorted[sorted.length - 1].top);
      expect(Math.abs(leftTop - rightTop)).toBeLessThan(10);
    });

    it('all seats are within table bounds (8%–90% horizontal, 5%–82% vertical)', () => {
      const positions = calculateOpponentPositions(3);
      positions.forEach(pos => {
        const left = parseFloat(pos.left);
        const top = parseFloat(pos.top);
        expect(left).toBeGreaterThanOrEqual(8);
        expect(left).toBeLessThanOrEqual(90);
        expect(top).toBeGreaterThanOrEqual(5);
        expect(top).toBeLessThanOrEqual(82);
      });
    });

    it('all positions have centering transform', () => {
      calculateOpponentPositions(3).forEach(pos => {
        expect(pos.transform).toBe('translate(-50%, -50%)');
      });
    });

    it('has seats at the equator (left and right near 50% vertical)', () => {
      const positions = calculateOpponentPositions(3);
      const midSeats = positions.filter(p => {
        const top = parseFloat(p.top);
        return top > 40 && top < 60;
      });
      expect(midSeats.length).toBe(2); // 9 o'clock and 3 o'clock
    });
  });

  describe('6-player (5 opponents)', () => {
    it('returns 5 positions', () => {
      expect(calculateOpponentPositions(5)).toHaveLength(5);
    });

    it('has seats on left, right, and top', () => {
      const positions = calculateOpponentPositions(5);
      const lefts = positions.map(p => parseFloat(p.left));
      const tops = positions.map(p => parseFloat(p.top));
      expect(lefts.some(l => l < 20)).toBe(true);   // left side
      expect(lefts.some(l => l > 70)).toBe(true);   // right side
      expect(tops.some(t => t < 20)).toBe(true);    // top area
    });

    it('all seats are within table bounds', () => {
      const positions = calculateOpponentPositions(5);
      positions.forEach(pos => {
        const left = parseFloat(pos.left);
        const top = parseFloat(pos.top);
        expect(left).toBeGreaterThanOrEqual(5);
        expect(left).toBeLessThanOrEqual(85);
        expect(top).toBeGreaterThanOrEqual(5);
        expect(top).toBeLessThanOrEqual(82);
      });
    });

    it('has seats in the lower half (below 50%)', () => {
      const positions = calculateOpponentPositions(5);
      const tops = positions.map(p => parseFloat(p.top));
      const belowCenter = tops.filter(t => t > 50);
      expect(belowCenter.length).toBe(2); // 7 o'clock and 5 o'clock
    });

    it('opponents are left-right symmetric', () => {
      const positions = calculateOpponentPositions(5);
      const sorted = [...positions].sort((a, b) => parseFloat(a.top) - parseFloat(b.top));
      // Top center is alone at ~15%
      const topCenter = sorted[0];
      expect(parseFloat(topCenter.left)).toBeCloseTo(50, 0);
      // Upper pair
      const upperLeft = parseFloat(sorted[1].left);
      const upperRight = parseFloat(sorted[2].left);
      expect(upperLeft + upperRight).toBeCloseTo(100, 5);
      // Lower pair
      const lowerLeft = parseFloat(sorted[3].left);
      const lowerRight = parseFloat(sorted[4].left);
      expect(lowerLeft + lowerRight).toBeCloseTo(100, 5);
    });
  });

  describe('mobile variant', () => {
    it('4-player right seat is within mobile bounds (left < 88%)', () => {
      const positions = calculateOpponentPositions(3, true);
      const lefts = positions.map(p => parseFloat(p.left));
      expect(lefts.every(l => l <= 88)).toBe(true);
    });
  });
});

describe('getHumanPlayerPosition', () => {
  it('places human at bottom center', () => {
    const pos = getHumanPlayerPosition();
    expect(parseFloat(pos.left)).toBeCloseTo(50, 0);
    expect(parseFloat(pos.top)).toBeGreaterThan(70);
  });

  it('has centering transform', () => {
    expect(getHumanPlayerPosition().transform).toBe('translate(-50%, -50%)');
  });
});
