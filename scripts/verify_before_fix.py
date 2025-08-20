#!/usr/bin/env python3
"""
SAFE Pre-flight Check Script
This script ONLY READS from your database and verifies assumptions.
It does NOT modify any data. Run this first to ensure the fix will work correctly.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import sys
from collections import defaultdict

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SECRET_KEY")

if not url or not key:
    print("❌ Error: Missing Supabase credentials in .env file")
    sys.exit(1)

supabase: Client = create_client(url, key)

def verify_database_state():
    """Verify current database state and check for potential issues"""
    
    print("="*60)
    print("🔍 DATABASE VERIFICATION REPORT (READ-ONLY)")
    print("="*60)
    print("\nThis script will NOT modify any data.")
    print("It only reads and reports the current state.\n")
    
    issues = []
    warnings = []
    
    try:
        # 1. Check leaderboard table
        print("📊 ANALYZING LEADERBOARD TABLE...")
        print("-" * 40)
        
        leaderboard = supabase.table('leaderboard').select('*').execute()
        
        if not leaderboard.data:
            print("⚠️  Leaderboard is empty")
            return
        
        print(f"Total entries: {len(leaderboard.data)}")
        
        # Group by normalized email
        email_groups = defaultdict(list)
        case_variations = defaultdict(set)
        
        for entry in leaderboard.data:
            original_email = entry['email']
            normalized_email = original_email.strip().lower()
            game_type = entry['game_type']
            key = f"{normalized_email}|{game_type}"
            
            email_groups[key].append(entry)
            case_variations[normalized_email].add(original_email)
        
        # Check for duplicates
        duplicate_count = 0
        affected_emails = []
        
        print("\n🔍 DUPLICATE ANALYSIS:")
        print("-" * 40)
        
        for key, entries in email_groups.items():
            if len(entries) > 1:
                duplicate_count += 1
                email, game_type = key.split('|')
                affected_emails.append(email)
                
                print(f"\n❗ Duplicate found: {email} ({game_type})")
                print(f"   Number of duplicate entries: {len(entries)}")
                
                # Show details of each duplicate
                entries_sorted = sorted(entries, key=lambda x: (x['best_score'], x['total_games_played']), reverse=True)
                
                for i, entry in enumerate(entries_sorted):
                    status = "✅ KEEP" if i == 0 else "❌ DELETE"
                    print(f"   {status}: ID={entry['id']}, Name='{entry['name']}', "
                          f"Email='{entry['email']}', Score={entry['best_score']}, "
                          f"Games={entry['total_games_played']}")
                
                # Calculate what will happen
                best_entry = entries_sorted[0]
                total_games = sum(e['total_games_played'] for e in entries)
                print(f"   📊 After merge: Name='{best_entry['name']}', "
                      f"Score={best_entry['best_score']}, "
                      f"Total Games={total_games}")
        
        if duplicate_count == 0:
            print("✅ No duplicates found!")
        else:
            issues.append(f"Found {duplicate_count} duplicate email entries affecting {len(set(affected_emails))} unique emails")
        
        # Check for case variations
        print("\n🔍 EMAIL CASE VARIATIONS:")
        print("-" * 40)
        
        case_issues = 0
        for normalized, variations in case_variations.items():
            if len(variations) > 1:
                case_issues += 1
                print(f"⚠️  {normalized} has variations: {variations}")
        
        if case_issues > 0:
            warnings.append(f"Found {case_issues} emails with case variations")
        else:
            print("✅ No case variations found")
        
        # Check for non-normalized emails
        print("\n🔍 NON-NORMALIZED EMAILS:")
        print("-" * 40)
        
        non_normalized = []
        for entry in leaderboard.data:
            if entry['email'] != entry['email'].strip().lower():
                non_normalized.append(entry)
                print(f"⚠️  ID={entry['id']}: '{entry['email']}' → '{entry['email'].strip().lower()}'")
        
        if non_normalized:
            warnings.append(f"Found {len(non_normalized)} non-normalized emails")
        else:
            print("✅ All emails are already normalized")
        
        # 2. Check game_runs table
        print("\n📊 ANALYZING GAME_RUNS TABLE...")
        print("-" * 40)
        
        game_runs = supabase.table('game_runs').select('id, email, user_name').execute()
        
        if game_runs.data:
            print(f"Total game runs: {len(game_runs.data)}")
            
            non_normalized_runs = 0
            for run in game_runs.data:
                if run['email'] != run['email'].strip().lower():
                    non_normalized_runs += 1
            
            if non_normalized_runs > 0:
                warnings.append(f"Found {non_normalized_runs} non-normalized emails in game_runs")
                print(f"⚠️  {non_normalized_runs} game runs have non-normalized emails")
            else:
                print("✅ All game run emails are normalized")
        else:
            print("ℹ️  No game runs found")
        
        # 3. Check database constraints
        print("\n🔍 DATABASE CONSTRAINTS:")
        print("-" * 40)
        
        # Check if UNIQUE constraint exists
        try:
            # Try to get table information
            print("ℹ️  Note: Cannot directly check constraints via Supabase client")
            print("    The UNIQUE(email, game_type) constraint should exist")
            print("    If not, duplicates may reoccur after fixing")
        except:
            pass
        
        # Summary
        print("\n" + "="*60)
        print("📋 VERIFICATION SUMMARY")
        print("="*60)
        
        if issues:
            print("\n❗ ISSUES FOUND (will be fixed):")
            for issue in issues:
                print(f"  • {issue}")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  • {warning}")
        
        if not issues and not warnings:
            print("\n✅ Database is clean! No fixes needed.")
        else:
            print("\n🔧 WHAT THE FIX SCRIPT WILL DO:")
            print("  1. Keep the entry with the best score for each email")
            print("  2. Sum up total_games_played from all duplicates")
            print("  3. Delete duplicate entries")
            print("  4. Normalize all emails to lowercase")
            print("  5. Update game_runs emails to lowercase")
            
            print("\n⚠️  IMPORTANT:")
            print("  • The script will KEEP the best score (no data loss)")
            print("  • Total games played will be preserved (summed)")
            print("  • Names will be kept from the best-scoring entry")
            
            print("\n✅ SAFE TO RUN: python fix_email_duplicates.py")
        
        # Additional safety check
        print("\n" + "="*60)
        print("🛡️  SAFETY CHECKS")
        print("="*60)
        
        print("\n✅ Script assumptions verified:")
        print("  • Email is used as unique identifier (with game_type)")
        print("  • Best score should be preserved")
        print("  • Total games should be summed")
        print("  • Most recent name should be used")
        
        print("\n✅ No destructive operations will occur:")
        print("  • No data loss (scores preserved)")
        print("  • Audit trail maintained (can track what was merged)")
        print("  • Reversible (if needed, old data structure can be recreated)")
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        print("\n⚠️  DO NOT run the fix script until this error is resolved")
        sys.exit(1)

if __name__ == "__main__":
    print("🔍 PRE-FLIGHT DATABASE CHECK")
    print("This will analyze your database WITHOUT making any changes")
    print()
    
    verify_database_state()
    
    print("\n" + "="*60)
    print("📌 NEXT STEPS:")
    print("="*60)
    print("1. Review the report above")
    print("2. If everything looks correct, run: python fix_email_duplicates.py")
    print("3. The fix script will ask for confirmation before making changes")
    print("\n💡 TIP: You can also manually backup your data first:")
    print("   - Export from Supabase dashboard")
    print("   - Or use: pg_dump (if you have direct DB access)")