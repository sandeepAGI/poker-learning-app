"""Test both hand analysis and session analysis features"""
import pytest
from playwright.sync_api import Page, expect
import time


def test_both_analysis_features(page: Page):
    """Test that both features work correctly"""
    
    print("\n=== CREATE GAME ===")
    page.goto("http://localhost:3000")
    page.fill('input[placeholder="Enter your name"]', 'TestPlayer')
    page.click('button:has-text("Start Game")')
    time.sleep(2)
    
    print("\n=== PLAY 3 HANDS ===")
    for i in range(3):
        time.sleep(1)
        fold_btn = page.locator('button:has-text("Fold")').first
        if fold_btn.is_visible(timeout=3000):
            fold_btn.click()
            time.sleep(0.5)
        
        next_btn = page.locator('button:has-text("Next Hand")').first
        if next_btn.is_visible(timeout=5000):
            next_btn.click()
            time.sleep(0.5)
    
    print("\n=== TEST 1: HAND ANALYSIS (No Deep Dive) ===")
    page.click('button:has-text("Settings")')
    time.sleep(0.5)
    page.click('button:has-text("Analyze Hand")')
    time.sleep(2)
    
    # Check for modal
    expect(page.locator('text=Hand Analysis')).to_be_visible(timeout=5000)
    print("✅ Hand Analysis modal opened")
    
    # Check there's NO "Deep Dive" text anywhere
    deep_dive_count = page.locator('text=Deep Dive').count()
    print(f"'Deep Dive' text found: {deep_dive_count} times")
    assert deep_dive_count == 0, "Deep Dive option should not exist!"
    print("✅ No 'Deep Dive' option found (correct!)")
    
    # Check for single "Analyze This Hand" button
    analyze_btn = page.locator('button:has-text("Analyze This Hand")')
    assert analyze_btn.count() >= 1, "Should have 'Analyze This Hand' button"
    print("✅ 'Analyze This Hand' button found")
    
    # Close modal
    page.locator('button:has-text("Close")').first.click()
    time.sleep(0.5)
    
    print("\n=== TEST 2: SESSION ANALYSIS ===")
    page.click('button:has-text("Settings")')
    time.sleep(0.5)
    page.click('button:has-text("Session Analysis")')
    time.sleep(10)  # Wait for LLM analysis
    
    # Check modal opened with title
    modal_visible = page.locator('text=Session Analysis').first.is_visible()
    print(f"Session Analysis modal visible: {modal_visible}")
    assert modal_visible, "Session Analysis modal should be visible"
    print("✅ Session Analysis modal opened")
    
    # Check for Quick/Deep toggle buttons
    quick_btn = page.locator('button:has-text("Quick")')
    deep_btn_count = page.locator('button:has-text("Deep")').count()
    print(f"Quick button count: {quick_btn.count()}")
    print(f"Deep button count: {deep_btn_count}")
    assert quick_btn.count() > 0, "Should have Quick button"
    assert deep_btn_count > 0, "Should have Deep Dive button for session analysis"
    print("✅ Quick/Deep toggle buttons found")
    
    # Take screenshot
    page.screenshot(path="/tmp/final_verification.png")
    
    print("\n✅ ALL TESTS PASSED!")
    print("- Hand Analysis: Single button, no Deep Dive ✓")
    print("- Session Analysis: Modal opens with Quick/Deep toggle ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
