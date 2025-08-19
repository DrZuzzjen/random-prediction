import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from api_client import RandomOrgClient

load_dotenv()

@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    return create_client(url, key)

@st.cache_resource
def init_random_client():
    """Initialize Random.org client"""
    return RandomOrgClient()

def calculate_score(user_numbers, random_numbers):
    """Calculate how many numbers match"""
    matches = sum(1 for num in user_numbers if num in random_numbers)
    return matches

def get_leaderboard(supabase: Client, game_type="1-99_range_10_numbers"):
    """Fetch leaderboard from database"""
    try:
        result = supabase.table('leaderboard').select('name, best_score').eq('game_type', game_type).order('best_score', desc=True).limit(10).execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching leaderboard: {e}")
        return []

def save_score(supabase: Client, name, email, score, game_type="1-99_range_10_numbers"):
    """Save or update user score"""
    try:
        # Try to get existing record
        existing = supabase.table('leaderboard').select('*').eq('email', email).eq('game_type', game_type).execute()
        
        if existing.data:
            # Update if new score is better
            current_best = existing.data[0]['best_score']
            total_games = existing.data[0]['total_games_played'] + 1
            
            if score > current_best:
                supabase.table('leaderboard').update({
                    'name': name,
                    'best_score': score,
                    'total_games_played': total_games
                }).eq('email', email).eq('game_type', game_type).execute()
                return True, "New high score saved!"
            else:
                supabase.table('leaderboard').update({
                    'total_games_played': total_games
                }).eq('email', email).eq('game_type', game_type).execute()
                return False, f"Score recorded. Your best is still {current_best}/10"
        else:
            # Insert new record
            supabase.table('leaderboard').insert({
                'name': name,
                'email': email,
                'best_score': score,
                'total_games_played': 1,
                'game_type': game_type
            }).execute()
            return True, "Score saved to leaderboard!"
            
    except Exception as e:
        st.error(f"Error saving score: {e}")
        return False, "Error saving score"

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="Random Prediction Game",
    page_icon="🎯",
    layout="centered"
)

st.title("🎯 Random Prediction Game")
st.markdown("### Predict 10 numbers between 1-99 and see how many match!")

# Initialize clients
supabase = init_supabase()
random_client = init_random_client()

# Game state
if 'game_played' not in st.session_state:
    st.session_state.game_played = False
if 'user_numbers' not in st.session_state:
    st.session_state.user_numbers = []
if 'random_numbers' not in st.session_state:
    st.session_state.random_numbers = []
if 'score' not in st.session_state:
    st.session_state.score = 0

# Sidebar - Leaderboard
with st.sidebar:
    st.header("🏆 Leaderboard")
    leaderboard = get_leaderboard(supabase)
    if leaderboard:
        for i, entry in enumerate(leaderboard, 1):
            st.write(f"{i}. **{entry['name']}** - {entry['best_score']}/10")
    else:
        st.write("No scores yet!")

# Main game interface
if not st.session_state.game_played:
    st.markdown("#### Enter your 10 predictions (1-99):")
    
    # Input fields for 10 numbers
    cols = st.columns(5)
    user_numbers = []
    
    for i in range(10):
        col_idx = i % 5
        with cols[col_idx]:
            num = st.number_input(
                f"#{i+1}", 
                min_value=1, 
                max_value=99, 
                value=1, 
                key=f"num_{i}"
            )
            user_numbers.append(num)
    
    if st.button("🎲 Generate Random Numbers & Calculate Score", type="primary"):
        try:
            with st.spinner("Generating random numbers..."):
                random_numbers = random_client.generate_random_numbers(10, 1, 99)
                score = calculate_score(user_numbers, random_numbers)
                
                st.session_state.user_numbers = user_numbers
                st.session_state.random_numbers = random_numbers
                st.session_state.score = score
                st.session_state.game_played = True
                st.rerun()
                
        except Exception as e:
            st.error(f"Error generating random numbers: {e}")

else:
    # Show results
    st.success(f"🎉 Your Score: **{st.session_state.score}/10**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Your Predictions:")
        st.write(st.session_state.user_numbers)
        
    with col2:
        st.subheader("Random Numbers:")
        st.write(st.session_state.random_numbers)
    
    # Show matches
    matches = [num for num in st.session_state.user_numbers if num in st.session_state.random_numbers]
    if matches:
        st.info(f"✅ Matching numbers: {matches}")
    else:
        st.info("❌ No matches this time!")
    
    # Save score form
    st.markdown("---")
    st.subheader("💾 Save Your Score")
    
    with st.form("save_score"):
        name = st.text_input("Your Name:", max_chars=50)
        email = st.text_input("Your Email (private):", max_chars=100)
        
        if st.form_submit_button("Save Score"):
            if name and email:
                is_new_best, message = save_score(supabase, name, email, st.session_state.score)
                if is_new_best:
                    st.success(message)
                else:
                    st.info(message)
            else:
                st.error("Please enter both name and email")
    
    # Play again
    if st.button("🔄 Play Again"):
        st.session_state.game_played = False
        st.session_state.user_numbers = []
        st.session_state.random_numbers = []
        st.session_state.score = 0
        st.rerun()