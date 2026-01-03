/**
 * Unit tests for short-stack button logic
 *
 * Issue #1: Short-Stack Call/Raise UI Blocks Valid Actions
 *
 * These tests define the CORRECT behavior:
 * - Call button should be enabled when player has ANY chips
 * - Raise button should be available when player has ANY chips (for all-in)
 * - Backend already handles this correctly, UI needs to match
 */

describe('Short-Stack Button Logic', () => {
  describe('canCall logic', () => {
    it('should allow call when stack >= callAmount (normal case)', () => {
      const stack = 100;
      const callAmount = 80;

      // Current (WRONG) logic: stack >= callAmount
      const canCall_OLD = stack >= callAmount;

      // Correct logic: can call if have any chips
      const canCall_NEW = stack > 0;

      expect(canCall_NEW).toBe(true);
      expect(canCall_OLD).toBe(true);  // Both work in normal case
    });

    it('should allow call when stack < callAmount (SHORT STACK CASE)', () => {
      const stack = 30;  // Short stack
      const callAmount = 80;  // Facing bigger bet

      // Current (WRONG) logic: stack >= callAmount
      const canCall_OLD = stack >= callAmount;

      // Correct logic: can call if have any chips (all-in)
      const canCall_NEW = stack > 0;

      expect(canCall_NEW).toBe(true);  // ✅ Should be true
      expect(canCall_OLD).toBe(false); // ❌ Currently false (BUG)
    });

    it('should NOT allow call when stack = 0 (busted)', () => {
      const stack = 0;
      const callAmount = 80;

      const canCall_NEW = stack > 0;

      expect(canCall_NEW).toBe(false);
    });
  });

  describe('canRaise logic', () => {
    it('should allow raise when stack allows normal raise', () => {
      const stack = 200;
      const currentBet = 20;
      const callAmount = 20;
      const minRaise = 40;
      const maxRaise = stack + currentBet;

      // Current logic
      const canRaise_OLD = maxRaise >= minRaise && stack > callAmount;

      // Correct logic: can raise if have any chips
      const canRaise_NEW = stack > 0;

      expect(canRaise_NEW).toBe(true);
      expect(canRaise_OLD).toBe(true);  // Both work in normal case
    });

    it('should allow raise when stack < minRaise (SHORT STACK ALL-IN)', () => {
      const stack = 50;  // Short stack
      const currentBet = 0;
      const callAmount = 20;
      const minRaise = 40;  // Min raise is 40
      const maxRaise = stack + currentBet;  // Max is only 50

      // Current (WRONG) logic
      const canRaise_OLD = maxRaise >= minRaise && stack > callAmount;

      // Correct logic: can raise if have any chips (all-in)
      const canRaise_NEW = stack > 0;

      expect(canRaise_NEW).toBe(true);  // ✅ Should be true
      expect(canRaise_OLD).toBe(true);   // Actually this passes the first condition
    });

    it('should allow raise when stack <= callAmount (VERY SHORT STACK)', () => {
      const stack = 15;  // Very short stack
      const currentBet = 0;
      const callAmount = 20;
      const minRaise = 40;
      const maxRaise = stack + currentBet;

      // Current (WRONG) logic
      const canRaise_OLD = maxRaise >= minRaise && stack > callAmount;

      // Correct logic: can raise if have any chips
      const canRaise_NEW = stack > 0;

      expect(canRaise_NEW).toBe(true);  // ✅ Should be true
      expect(canRaise_OLD).toBe(false); // ❌ Currently false (BUG)
    });

    it('should NOT allow raise when stack = 0', () => {
      const stack = 0;
      const canRaise_NEW = stack > 0;
      expect(canRaise_NEW).toBe(false);
    });
  });

  describe('Call button label', () => {
    it('should show "Call $X" when stack >= callAmount', () => {
      const stack = 100;
      const callAmount = 80;

      const label = stack >= callAmount
        ? `Call $${callAmount}`
        : `Call All-In $${stack}`;

      expect(label).toBe('Call $80');
    });

    it('should show "Call All-In $X" when stack < callAmount', () => {
      const stack = 30;
      const callAmount = 80;

      const label = stack >= callAmount
        ? `Call $${callAmount}`
        : `Call All-In $${stack}`;

      expect(label).toBe('Call All-In $30');
    });
  });
});
