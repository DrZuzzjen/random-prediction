-- BACKUP QUERIES - Run these in Supabase SQL Editor before making changes
-- Copy and save the results somewhere safe

-- 1. Backup current leaderboard data
SELECT * FROM leaderboard 
ORDER BY email, game_type, id;

-- 2. Backup current game_runs data (just email and id for reference)
SELECT id, email, user_name, created_at 
FROM game_runs 
ORDER BY email, created_at;

-- 3. Count current state
SELECT 
    'leaderboard' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT email) as unique_emails,
    COUNT(DISTINCT LOWER(email)) as unique_emails_normalized
FROM leaderboard

UNION ALL

SELECT 
    'game_runs' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT email) as unique_emails,
    COUNT(DISTINCT LOWER(email)) as unique_emails_normalized
FROM game_runs;

-- 4. Check for duplicates that will be merged
WITH duplicate_check AS (
    SELECT 
        LOWER(email) as normalized_email,
        game_type,
        COUNT(*) as duplicate_count,
        STRING_AGG(DISTINCT name, ', ') as all_names,
        MAX(best_score) as max_score,
        SUM(total_games_played) as total_games
    FROM leaderboard
    GROUP BY LOWER(email), game_type
    HAVING COUNT(*) > 1
)
SELECT * FROM duplicate_check
ORDER BY duplicate_count DESC, normalized_email;