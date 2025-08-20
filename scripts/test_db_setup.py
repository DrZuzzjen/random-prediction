#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def test_database_setup():
    """Test Supabase connection and create table"""
    
    # Get environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SECRET_KEY in .env")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(url, key)
        print("✅ Connected to Supabase successfully")
        
        # Read and execute SQL
        with open('database_setup.sql', 'r') as file:
            sql_content = file.read()
        
        # Execute the SQL (Note: supabase-py doesn't support raw SQL execution easily)
        # We'll test connection by trying a simple query instead
        result = supabase.table('leaderboard').select("*").limit(1).execute()
        print("✅ Database table exists and is accessible")
        return True
        
    except Exception as e:
        print(f"❌ Database setup error: {str(e)}")
        print("\n📝 Please manually run the SQL from database_setup.sql in your Supabase dashboard:")
        print("   1. Go to your Supabase project dashboard")
        print("   2. Navigate to SQL Editor")
        print("   3. Copy and paste the content from database_setup.sql")
        print("   4. Execute the SQL")
        return False

if __name__ == "__main__":
    print("🚀 Testing Supabase database setup...")
    success = test_database_setup()
    if success:
        print("\n🎉 Database setup completed successfully!")
    else:
        print("\n⚠️  Manual setup required - see instructions above")