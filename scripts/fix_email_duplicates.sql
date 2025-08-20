-- Fix Email Duplicates and Case Sensitivity
-- Run this in your Supabase SQL Editor to fix the duplicate email issue

-- Step 1: Normalize all existing emails to lowercase
UPDATE leaderboard 
SET email = LOWER(TRIM(email));

UPDATE game_runs 
SET email = LOWER(TRIM(email));

-- Step 2: Merge duplicate entries in leaderboard
-- For each duplicate email, keep the entry with the best score
WITH duplicate_emails AS (
    SELECT 
        email,
        game_type,
        COUNT(*) as count
    FROM leaderboard
    GROUP BY email, game_type
    HAVING COUNT(*) > 1
),
best_scores AS (
    SELECT 
        l.id,
        l.email,
        l.game_type,
        l.name,
        l.best_score,
        l.total_games_played,
        ROW_NUMBER() OVER (
            PARTITION BY l.email, l.game_type 
            ORDER BY l.best_score DESC, l.total_games_played DESC, l.id ASC
        ) as rn
    FROM leaderboard l
    INNER JOIN duplicate_emails d 
        ON l.email = d.email 
        AND l.game_type = d.game_type
)
-- Delete all but the best entry for each duplicate
DELETE FROM leaderboard 
WHERE id IN (
    SELECT id 
    FROM best_scores 
    WHERE rn > 1
);

-- Step 3: Drop the existing unique constraint
ALTER TABLE leaderboard 
DROP CONSTRAINT IF EXISTS leaderboard_email_game_type_key;

-- Step 4: Create a case-insensitive unique constraint
-- PostgreSQL doesn't have case-insensitive constraints directly,
-- so we create a unique index on lowercased email
CREATE UNIQUE INDEX idx_leaderboard_email_game_type_unique 
ON leaderboard (LOWER(email), game_type);

-- Step 5: Add a check constraint to ensure emails are always lowercase
ALTER TABLE leaderboard 
ADD CONSTRAINT email_must_be_lowercase 
CHECK (email = LOWER(email));

ALTER TABLE game_runs 
ADD CONSTRAINT email_must_be_lowercase 
CHECK (email = LOWER(email));

-- Step 6: Update the name for remaining entries to use the most recent name
WITH latest_names AS (
    SELECT DISTINCT ON (email) 
        email,
        user_name
    FROM game_runs
    ORDER BY email, created_at DESC
)
UPDATE leaderboard l
SET name = ln.user_name
FROM latest_names ln
WHERE l.email = ln.email;

-- Verify the fix
SELECT 
    email, 
    COUNT(*) as entries,
    STRING_AGG(name, ', ') as names,
    STRING_AGG(best_score::text, ', ') as scores
FROM leaderboard
GROUP BY email, game_type
HAVING COUNT(*) > 1;