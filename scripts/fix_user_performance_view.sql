-- Fix the user_performance view to prevent duplicate entries per email
-- The issue: Currently groups by (email, user_name, game_type) which creates duplicates
-- The fix: Group only by (email, game_type) and use the most recent user_name

-- Drop the existing view
DROP VIEW IF EXISTS user_performance;

-- Recreate with proper grouping (by email only, not user_name)
CREATE VIEW user_performance AS
SELECT 
    email,
    -- Use the most recent user_name for this email
    (SELECT user_name 
     FROM game_runs gr2 
     WHERE gr2.email = gr.email 
     ORDER BY created_at DESC 
     LIMIT 1) as user_name,
    game_type,
    COUNT(*) as total_games,
    MAX(score) as best_score,
    AVG(score) as avg_score,
    MIN(created_at) as first_game,
    MAX(created_at) as last_game
FROM game_runs gr
GROUP BY email, game_type;

-- Verify the fix
SELECT 
    email,
    COUNT(*) as entries_count,
    STRING_AGG(user_name, ', ') as all_names
FROM user_performance
GROUP BY email
HAVING COUNT(*) > 1;