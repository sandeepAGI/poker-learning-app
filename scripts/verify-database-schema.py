#!/usr/bin/env python3
"""Verify Azure PostgreSQL database schema"""
import os
from sqlalchemy import create_engine, text, inspect

# Get DATABASE_URL from environment
database_url = os.environ.get('DATABASE_URL_PRODUCTION')
if not database_url:
    print("❌ FAIL: DATABASE_URL_PRODUCTION not set")
    exit(1)

print("🔍 Verifying database schema...")
print()

try:
    # Connect to database
    engine = create_engine(database_url)
    inspector = inspect(engine)

    # Expected tables
    expected_tables = ['users', 'games', 'hands', 'analysis_cache']

    # Get actual tables
    actual_tables = inspector.get_table_names()

    print(f"Expected tables: {expected_tables}")
    print(f"Found tables: {actual_tables}")
    print()

    # Check each table exists
    all_tables_exist = True
    for table in expected_tables:
        if table in actual_tables:
            columns = inspector.get_columns(table)
            print(f"✅ Table '{table}' exists ({len(columns)} columns)")
        else:
            print(f"❌ Table '{table}' NOT FOUND")
            all_tables_exist = False

    if not all_tables_exist:
        exit(1)

    print()

    # Test connection with a simple query
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"✅ Users table query successful: {user_count} users")

        result = conn.execute(text("SELECT COUNT(*) FROM games"))
        game_count = result.scalar()
        print(f"✅ Games table query successful: {game_count} games")

        result = conn.execute(text("SELECT COUNT(*) FROM hands"))
        hand_count = result.scalar()
        print(f"✅ Hands table query successful: {hand_count} hands")

        result = conn.execute(text("SELECT COUNT(*) FROM analysis_cache"))
        cache_count = result.scalar()
        print(f"✅ Analysis cache query successful: {cache_count} entries")

    print()
    print("🎉 All database schema tests passed!")
    print(f"Database: {database_url.split('@')[1].split('/')[0]}")

except Exception as e:
    print(f"❌ FAIL: {e}")
    exit(1)
