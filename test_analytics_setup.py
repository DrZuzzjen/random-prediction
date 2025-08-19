#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

def test_analytics_setup():
    """Test the new analytics database setup"""
    
    print("🚀 Testing Analytics Database Setup...")
    
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
        
        # Test existing leaderboard table
        try:
            result = supabase.table('leaderboard').select("*").limit(1).execute()
            print("✅ Existing leaderboard table is accessible")
        except Exception as e:
            print(f"❌ Leaderboard table error: {e}")
            return False
        
        # Test new game_runs table
        try:
            result = supabase.table('game_runs').select("*").limit(1).execute()
            print("✅ New game_runs table exists and is accessible")
            
            # Test inserting a sample game run
            sample_run = {
                'user_name': 'Test User',
                'email': 'test@example.com',
                'predictions': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'random_numbers': [15, 25, 35, 45, 55, 65, 75, 85, 95, 5],
                'score': 1,
                'game_type': '1-99_range_10_numbers'
            }
            
            insert_result = supabase.table('game_runs').insert(sample_run).execute()
            if insert_result.data:
                print("✅ Successfully inserted test game run")
                
                # Clean up test data
                test_id = insert_result.data[0]['id']
                supabase.table('game_runs').delete().eq('id', test_id).execute()
                print("✅ Test data cleaned up")
            else:
                print("⚠️  Could not insert test data - check table permissions")
                
        except Exception as e:
            print(f"❌ game_runs table error: {e}")
            print("\n📝 You need to create the game_runs table!")
            print("   1. Go to your Supabase project dashboard")
            print("   2. Navigate to SQL Editor")
            print("   3. Copy and paste the content from database_analytics_schema.sql")
            print("   4. Execute the SQL")
            return False
        
        print("\n🎉 Analytics database setup is complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_analytics_setup()
    if not success:
        print("\n⚠️  Please fix the issues above before proceeding")
        exit(1)
    else:
        print("\n🚀 Ready to launch the enhanced application!")