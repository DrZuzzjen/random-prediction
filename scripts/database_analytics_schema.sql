-- Enhanced Database Schema for Analytics Feature
-- Run this AFTER the existing database_setup.sql

-- Table to store individual game runs for detailed analytics
CREATE TABLE game_runs (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    predictions JSONB NOT NULL,        -- Array of 10 predicted numbers [1,2,3,...]
    random_numbers JSONB NOT NULL,     -- Array of 10 random numbers [15,25,35,...]
    score INTEGER NOT NULL,            -- Number of matches (0-10)
    game_type VARCHAR(50) NOT NULL DEFAULT '1-99_range_10_numbers',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_game_runs_email_type ON game_runs(email, game_type);
CREATE INDEX idx_game_runs_type_created ON game_runs(game_type, created_at);
CREATE INDEX idx_game_runs_score ON game_runs(game_type, score);

-- Useful views for analytics

-- View: Flattened predictions for frequency analysis
CREATE VIEW prediction_frequency AS
SELECT 
    game_type,
    jsonb_array_elements_text(predictions)::integer as predicted_number,
    created_at
FROM game_runs;

-- View: Flattened random numbers for frequency analysis  
CREATE VIEW random_frequency AS
SELECT 
    game_type,
    jsonb_array_elements_text(random_numbers)::integer as random_number,
    created_at
FROM game_runs;

-- View: User performance summary
CREATE VIEW user_performance AS
SELECT 
    email,
    user_name,
    game_type,
    COUNT(*) as total_games,
    MAX(score) as best_score,
    AVG(score) as avg_score,
    MIN(created_at) as first_game,
    MAX(created_at) as last_game
FROM game_runs 
GROUP BY email, user_name, game_type;

-- Function: Calculate matches for a game run
CREATE OR REPLACE FUNCTION calculate_matches(pred JSONB, rand JSONB)
RETURNS INTEGER AS $$
BEGIN
    -- Count intersection of two JSONB arrays
    RETURN (
        SELECT COUNT(*)
        FROM jsonb_array_elements(pred) p
        WHERE p IN (SELECT jsonb_array_elements(rand))
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- RLS policies for game_runs
ALTER TABLE game_runs ENABLE ROW LEVEL SECURITY;

-- Allow all users to read all game runs (for global analytics)
CREATE POLICY "Allow read access to game_runs" ON game_runs
    FOR SELECT USING (true);

-- Allow insert for all users (when playing games)
CREATE POLICY "Allow insert for all users" ON game_runs
    FOR INSERT WITH CHECK (true);

-- Allow users to update only their own runs (if needed)
CREATE POLICY "Allow update own runs" ON game_runs
    FOR UPDATE USING (email = current_setting('app.user_email', true));

COMMENT ON TABLE game_runs IS 'Stores individual game runs for detailed analytics';
COMMENT ON COLUMN game_runs.predictions IS 'JSONB array of 10 predicted numbers';
COMMENT ON COLUMN game_runs.random_numbers IS 'JSONB array of 10 random numbers'; 
COMMENT ON COLUMN game_runs.score IS 'Number of matches between predictions and random numbers';