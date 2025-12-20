#!/usr/bin/env python3
"""
Quick test to verify ANTHROPIC_API_KEY is loaded correctly.
Run from backend/ directory: python test_api_key.py
"""

from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Check API key
api_key = os.getenv("ANTHROPIC_API_KEY")

print("="*60)
print("🔑 API Key Configuration Test")
print("="*60)

if api_key:
    print(f"✅ ANTHROPIC_API_KEY found!")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Prefix: {api_key[:15]}...")
    print(f"   Suffix: ...{api_key[-10:]}")

    # Test that it's a valid format
    if api_key.startswith("sk-ant-api03-"):
        print(f"✅ Key format looks correct (starts with sk-ant-api03-)")
    else:
        print(f"⚠️  Key format unexpected (doesn't start with sk-ant-api03-)")

    # Try to import and initialize LLM analyzer
    try:
        from llm_analyzer import LLMHandAnalyzer
        analyzer = LLMHandAnalyzer()
        print(f"✅ LLMHandAnalyzer initialized successfully!")
        print(f"   Haiku model: {analyzer.haiku_model}")
        print(f"   Sonnet model: {analyzer.sonnet_model}")
    except Exception as e:
        print(f"❌ Failed to initialize LLMHandAnalyzer: {e}")
else:
    print("❌ ANTHROPIC_API_KEY not found!")
    print("   Make sure backend/.env exists with:")
    print("   ANTHROPIC_API_KEY=sk-ant-api03-...")

print("="*60)
