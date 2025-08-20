-- Random Prediction Game Database Schema
-- Run this in your Supabase SQL Editor

CREATE TABLE leaderboard (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    best_score INTEGER NOT NULL DEFAULT 0,
    total_games_played INTEGER NOT NULL DEFAULT 0,
    game_type VARCHAR(50) NOT NULL DEFAULT '1-99_range_10_numbers',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(email, game_type)
);

-- Index for faster leaderboard queries
CREATE INDEX idx_leaderboard_score_game_type ON leaderboard(game_type, best_score DESC);

-- RLS (Row Level Security) policies
ALTER TABLE leaderboard ENABLE ROW LEVEL SECURITY;

-- Allow all users to read leaderboard
CREATE POLICY "Allow read access to leaderboard" ON leaderboard
    FOR SELECT USING (true);

-- Allow insert/update for authenticated users
CREATE POLICY "Allow insert/update for all users" ON leaderboard
    FOR ALL USING (true);