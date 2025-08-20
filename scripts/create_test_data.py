#!/usr/bin/env python3

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def create_test_data():
    """Create dummy test data for analytics demonstration"""
    
    print("🎯 Creating test data for analytics demonstration...")
    
    # Initialize Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    supabase: Client = create_client(url, key)
    
    # Test users - all emails normalized to lowercase
    test_users = [
        {"name": "Alice Demo", "email": "alice@demo.com".lower()},
        {"name": "Bob Test", "email": "bob@demo.com".lower()},
        {"name": "Charlie Sample", "email": "charlie@demo.com".lower()},
        {"name": "Diana Example", "email": "diana@demo.com".lower()},
        {"name": "Eve Analytics", "email": "eve@demo.com".lower()}
    ]
    
    # Generate game runs for each test user
    all_runs = []
    
    for user in test_users:
        print(f"Creating games for {user['name']}...")
        
        # Create 15-25 games per user over the last 30 days
        num_games = random.randint(15, 25)
        
        for i in range(num_games):
            # Generate random timestamp within last 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            game_time = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            # Generate predictions - simulate human behavior
            predictions = []
            
            # Some users prefer certain ranges
            if user["email"] == "alice@demo.com":
                # Alice likes small numbers
                predictions = [random.randint(1, 30) for _ in range(10)]
            elif user["email"] == "bob@demo.com":
                # Bob likes big numbers
                predictions = [random.randint(50, 99) for _ in range(10)]
            elif user["email"] == "charlie@demo.com":
                # Charlie likes multiples of 5
                predictions = [random.choice([5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]) for _ in range(10)]
            else:
                # Random selections for others
                predictions = random.sample(range(1, 100), 10)
            
            # Generate truly random numbers (what the API would return)
            random_numbers = random.sample(range(1, 100), 10)
            
            # Calculate score (matches)
            score = len(set(predictions) & set(random_numbers))
            
            # Create game run record
            game_run = {
                'user_name': user['name'],
                'email': user['email'],
                'predictions': predictions,
                'random_numbers': random_numbers,
                'score': score,
                'game_type': '1-99_range_10_numbers',
                'created_at': game_time.isoformat()
            }
            
            all_runs.append(game_run)
    
    # Insert all game runs
    try:
        print(f"Inserting {len(all_runs)} game runs...")
        result = supabase.table('game_runs').insert(all_runs).execute()
        print(f"✅ Successfully inserted {len(result.data)} game runs")
        
        # Update leaderboard for each user
        print("Updating leaderboard...")
        for user in test_users:
            user_runs = [run for run in all_runs if run['email'] == user['email']]
            best_score = max(run['score'] for run in user_runs)
            total_games = len(user_runs)
            
            # Check if user exists in leaderboard
            existing = supabase.table('leaderboard').select('*').eq('email', user['email']).execute()
            
            if existing.data:
                # Update existing
                supabase.table('leaderboard').update({
                    'name': user['name'],
                    'best_score': best_score,
                    'total_games_played': total_games
                }).eq('email', user['email']).execute()
            else:
                # Insert new
                supabase.table('leaderboard').insert({
                    'name': user['name'],
                    'email': user['email'],
                    'best_score': best_score,
                    'total_games_played': total_games,
                    'game_type': '1-99_range_10_numbers'
                }).execute()
        
        print("✅ Leaderboard updated successfully")
        
        # Print summary statistics
        print("\n📊 Test Data Summary:")
        print(f"• Total games created: {len(all_runs)}")
        print(f"• Test users: {len(test_users)}")
        print(f"• Date range: Last 30 days")
        
        scores = [run['score'] for run in all_runs]
        print(f"• Average score: {sum(scores)/len(scores):.1f}/10")
        print(f"• Best score: {max(scores)}/10")
        print(f"• Score distribution: {dict(sorted([(i, scores.count(i)) for i in range(11)]))}")
        
        print("\n🎮 Test users created:")
        for user in test_users:
            user_games = len([r for r in all_runs if r['email'] == user['email']])
            user_best = max([r['score'] for r in all_runs if r['email'] == user['email']])
            print(f"  • {user['name']} ({user['email']}): {user_games} games, best: {user_best}/10")
        
        print("\n✨ You can now test the analytics with rich data!")
        print("📝 To clean up later, run: python cleanup_test_data.py")
        
    except Exception as e:
        print(f"❌ Error inserting test data: {e}")
        return False
    
    return True

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
        # Remove from game_runs
        for email in test_emails:
            supabase.table('game_runs').delete().eq('email', email).execute()
        
        # Remove from leaderboard
        for email in test_emails:
            supabase.table('leaderboard').delete().eq('email', email).execute()
        
        print("✅ Test data cleaned up successfully")
        
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_data()
    else:
        create_test_data()