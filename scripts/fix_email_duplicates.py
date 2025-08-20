#!/usr/bin/env python3
"""
Fix email duplicate entries in the leaderboard.
This script normalizes all emails to lowercase and merges duplicate entries.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import sys

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SECRET_KEY")

if not url or not key:
    print("❌ Error: Missing Supabase credentials in .env file")
    sys.exit(1)

supabase: Client = create_client(url, key)

def fix_duplicates():
    """Fix duplicate email entries in the leaderboard"""
    try:
        print("🔍 Fetching all leaderboard entries...")
        
        # Get all leaderboard entries
        all_entries = supabase.table('leaderboard').select('*').execute()
        
        if not all_entries.data:
            print("No entries found in leaderboard")
            return
        
        # Group by normalized email
        email_groups = {}
        for entry in all_entries.data:
            normalized_email = entry['email'].strip().lower()
            game_type = entry['game_type']
            key = f"{normalized_email}|{game_type}"
            
            if key not in email_groups:
                email_groups[key] = []
            email_groups[key].append(entry)
        
        # Find duplicates
        duplicates_found = False
        for key, entries in email_groups.items():
            if len(entries) > 1:
                duplicates_found = True
                email, game_type = key.split('|')
                print(f"\n⚠️  Found {len(entries)} entries for {email} ({game_type}):")
                
                # Sort by best score descending, then total games
                entries.sort(key=lambda x: (x['best_score'], x['total_games_played']), reverse=True)
                
                # Keep the best entry
                best_entry = entries[0]
                print(f"  ✅ Keeping: {best_entry['name']} - Score: {best_entry['best_score']}, Games: {best_entry['total_games_played']}")
                
                # Update the best entry with normalized email and aggregate games played
                total_games = sum(e['total_games_played'] for e in entries)
                
                # Update the best entry
                supabase.table('leaderboard').update({
                    'email': email,  # Normalized email
                    'total_games_played': total_games,
                    'name': best_entry['name']  # Keep the name from best score entry
                }).eq('id', best_entry['id']).execute()
                
                # Delete the duplicates
                for duplicate in entries[1:]:
                    print(f"  ❌ Deleting: {duplicate['name']} - Score: {duplicate['best_score']}, Games: {duplicate['total_games_played']}")
                    supabase.table('leaderboard').delete().eq('id', duplicate['id']).execute()
        
        if not duplicates_found:
            print("✅ No duplicates found!")
        else:
            print("\n✅ Duplicates have been fixed!")
        
        # Normalize all remaining emails
        print("\n🔧 Normalizing all email addresses...")
        remaining = supabase.table('leaderboard').select('*').execute()
        
        for entry in remaining.data:
            if entry['email'] != entry['email'].strip().lower():
                supabase.table('leaderboard').update({
                    'email': entry['email'].strip().lower()
                }).eq('id', entry['id']).execute()
                print(f"  Normalized: {entry['email']} → {entry['email'].strip().lower()}")
        
        print("\n✅ All emails have been normalized!")
        
        # Also normalize emails in game_runs table
        print("\n🔧 Normalizing emails in game_runs table...")
        game_runs = supabase.table('game_runs').select('id, email').execute()
        
        normalized_count = 0
        for run in game_runs.data:
            normalized = run['email'].strip().lower()
            if run['email'] != normalized:
                supabase.table('game_runs').update({
                    'email': normalized
                }).eq('id', run['id']).execute()
                normalized_count += 1
        
        if normalized_count > 0:
            print(f"  Normalized {normalized_count} game run emails")
        
        print("\n✅ Database cleanup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=== Email Duplicate Fix Script ===")
    print("This will:")
    print("1. Find duplicate email entries (case-insensitive)")
    print("2. Keep the entry with the best score")
    print("3. Aggregate total games played")
    print("4. Normalize all emails to lowercase")
    print()
    
    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        fix_duplicates()
    else:
        print("Operation cancelled.")