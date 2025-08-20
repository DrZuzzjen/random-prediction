#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def cleanup_test_data():
    """Remove all test data"""
    print("🧹 Cleaning up test data...")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") 
    supabase: Client = create_client(url, key)
    
    test_emails = [
        "alice@demo.com", "bob@demo.com", "charlie@demo.com", 
        "diana@demo.com", "eve@demo.com"
    ]
    
    try:
        # Count existing test data
        total_runs = 0
        total_leaderboard = 0
        
        for email in test_emails:
            runs = supabase.table('game_runs').select('id').eq('email', email).execute()
            total_runs += len(runs.data)
            
            leaderboard = supabase.table('leaderboard').select('id').eq('email', email).execute()
            total_leaderboard += len(leaderboard.data)
        
        print(f"Found {total_runs} test game runs and {total_leaderboard} leaderboard entries")
        
        if total_runs == 0 and total_leaderboard == 0:
            print("✅ No test data found - already clean!")
            return
        
        # Confirm deletion
        confirm = input(f"Delete {total_runs} game runs and {total_leaderboard} leaderboard entries? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("❌ Cleanup cancelled")
            return
        
        # Remove from game_runs
        for email in test_emails:
            result = supabase.table('game_runs').delete().eq('email', email).execute()
            if result.data:
                print(f"  • Removed {len(result.data)} game runs for {email}")
        
        # Remove from leaderboard
        for email in test_emails:
            result = supabase.table('leaderboard').delete().eq('email', email).execute()
            if result.data:
                print(f"  • Removed leaderboard entry for {email}")
        
        print("✅ Test data cleaned up successfully!")
        print("🎯 Analytics will now show only real user data")
        
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")

if __name__ == "__main__":
    cleanup_test_data()