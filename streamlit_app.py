import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from api_client import RandomOrgClient
from analytics import (
    save_game_run, update_leaderboard, show_global_analytics, 
    show_user_analytics
)

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
    """Calculate how many numbers match - handles duplicates correctly"""
    # Convert to sets to avoid counting duplicates multiple times
    user_set = set(user_numbers)
    random_set = set(random_numbers)
    
    # Count actual unique matches
    matches = len(user_set.intersection(random_set))
    return matches

@st.cache_data(ttl=60)
def get_leaderboard(_supabase: Client, game_type="1-99_range_10_numbers"):
    """Fetch leaderboard from database"""
    try:
        result = _supabase.table('leaderboard').select('name, best_score').eq('game_type', game_type).order('best_score', desc=True).limit(10).execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching leaderboard: {e}")
        return []

def show_game_tab(supabase: Client, random_client: RandomOrgClient):
    """Display the main game interface"""
    
    st.markdown("### 🎯 Predict 10 numbers between 1-99 and see how many match!")
    
    # Game state management
    if 'game_state' not in st.session_state:
        st.session_state.game_state = 'input'  # 'input', 'user_details', 'results'
    if 'user_numbers' not in st.session_state:
        st.session_state.user_numbers = []
    if 'random_numbers' not in st.session_state:
        st.session_state.random_numbers = []
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ""

    # Phase 1: Number input
    if st.session_state.game_state == 'input':
        st.markdown("#### Enter your 10 unique predictions (1-99):")
        st.markdown("*Choose different numbers to maximize your chances!*")
        
        # Input fields for 10 numbers in a nice grid
        cols = st.columns(5)
        user_numbers = []
        
        for i in range(10):
            col_idx = i % 5
            with cols[col_idx]:
                num = st.number_input(
                    f"#{i+1}", 
                    min_value=0, 
                    max_value=99, 
                    value=0,
                    key=f"num_{i}",
                    help="Choose a number between 1-99"
                )
                user_numbers.append(num)
        
        # Check for invalid numbers (zeros) and duplicates
        zeros_count = user_numbers.count(0)
        valid_numbers = [n for n in user_numbers if n > 0]
        unique_predictions = len(set(valid_numbers))
        
        if zeros_count > 0:
            st.error(f"❌ Please choose numbers between 1-99 (you have {zeros_count} zeros)")
        elif unique_predictions < len(valid_numbers):
            st.warning(f"⚠️ You have only {unique_predictions} unique numbers. Duplicates won't increase your chances!")
        elif len(valid_numbers) < 10:
            st.error("❌ Please enter all 10 predictions")
        
        can_play = zeros_count == 0 and len(valid_numbers) == 10
        
        if st.button("🎲 Generate Random Numbers", type="primary", use_container_width=True, disabled=not can_play):
            try:
                with st.spinner("🔮 Generating truly random numbers..."):
                    random_numbers = random_client.generate_random_numbers(10, 1, 99)
                    score = calculate_score(user_numbers, random_numbers)
                    
                    # Store data in session state
                    st.session_state.user_numbers = user_numbers
                    st.session_state.random_numbers = random_numbers
                    st.session_state.score = score
                    st.session_state.game_state = 'user_details'
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error generating random numbers: {e}")
                st.info("💡 Please check your internet connection and Random.org API key.")

    # Phase 2: Collect user details BEFORE showing results
    elif st.session_state.game_state == 'user_details':
        st.markdown("#### 📝 Almost there! Tell us who you are:")
        st.markdown("*We need your details to save your score and show personalized analytics.*")
        
        with st.form("user_details_form", clear_on_submit=False):
            name = st.text_input("Your Name:", max_chars=50, placeholder="Enter your name")
            email = st.text_input("Your Email:", max_chars=100, placeholder="your@email.com")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("🎯 Show My Results!", type="primary", use_container_width=True):
                    if name.strip() and email.strip():
                        st.session_state.user_name = name.strip()
                        # Normalize email to lowercase to prevent duplicates
                        st.session_state.user_email = email.strip().lower()
                        st.session_state.game_state = 'results'
                        
                        # Save game run for analytics
                        save_game_run(
                            supabase, 
                            st.session_state.user_name,
                            st.session_state.user_email,
                            st.session_state.user_numbers,
                            st.session_state.random_numbers,
                            st.session_state.score
                        )
                        
                        # Update leaderboard
                        update_leaderboard(
                            supabase,
                            st.session_state.user_name,
                            st.session_state.user_email,
                            st.session_state.score
                        )
                        
                        st.rerun()
                    else:
                        st.error("❌ Please enter both your name and email.")
            
            with col2:
                if st.form_submit_button("🔄 Start Over", use_container_width=True):
                    # Reset game state
                    for key in ['game_state', 'user_numbers', 'random_numbers', 'score', 'user_name', 'user_email']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

    # Phase 3: Show results
    elif st.session_state.game_state == 'results':
        # Show score with celebration
        if st.session_state.score >= 8:
            st.balloons()
            st.success(f"🎉 AMAZING! Your Score: **{st.session_state.score}/10**")
        elif st.session_state.score >= 5:
            st.success(f"🎯 Great job! Your Score: **{st.session_state.score}/10**")
        elif st.session_state.score >= 2:
            st.info(f"🎲 Nice try! Your Score: **{st.session_state.score}/10**")
        else:
            st.warning(f"🍀 Better luck next time! Your Score: **{st.session_state.score}/10**")
        
        # Show comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🧠 Your Predictions:")
            pred_display = ", ".join(map(str, st.session_state.user_numbers))
            st.code(pred_display, language=None)
            
        with col2:
            st.markdown("#### 🎲 Random Numbers:")
            rand_display = ", ".join(map(str, st.session_state.random_numbers))
            st.code(rand_display, language=None)
        
        # Show matches
        matches = [num for num in st.session_state.user_numbers if num in st.session_state.random_numbers]
        if matches:
            st.success(f"✅ **Matching numbers:** {', '.join(map(str, matches))}")
        else:
            st.info("❌ No matches this time - the odds were 1 in 75 million!")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎮 Play Again", type="primary", use_container_width=True):
                # Reset game state
                for key in ['game_state', 'user_numbers', 'random_numbers', 'score']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("📊 View My Stats", use_container_width=True):
                # Switch to user analytics tab
                st.session_state.active_tab = "👤 My Analytics"
                st.rerun()
        
        with col3:
            if st.button("🌍 Global Stats", use_container_width=True):
                # Switch to global analytics tab
                st.session_state.active_tab = "📊 Global Analytics"
                st.rerun()

def main():
    # Set page config
    st.set_page_config(
        page_title="Random Prediction Game",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize clients
    supabase = init_supabase()
    random_client = init_random_client()
    
    # Sidebar - Leaderboard (always visible)
    with st.sidebar:
        st.markdown("# 🏆 Leaderboard")
        st.markdown("*Top 10 Best Scores*")
        
        leaderboard = get_leaderboard(supabase)
        if leaderboard:
            for i, entry in enumerate(leaderboard, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
                st.markdown(f"{medal} **{entry['name']}** - {entry['best_score']}/10")
        else:
            st.info("🎯 Be the first to play!")
        
        st.markdown("---")
        st.markdown("### 🎮 How to Play")
        st.markdown("""
        1. **Predict** 10 numbers (1-99)
        2. **Generate** random numbers
        3. **Enter** your details
        4. **See** your score!
        5. **Compete** on the leaderboard
        """)
    
    # Main content area with tabs
    st.title("🎯 Random Prediction Game")
    
    # Tab management
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "🎮 Play Game"
    
    tab1, tab2, tab3 = st.tabs(["🎮 Play Game", "📊 Global Analytics", "👤 My Analytics"])
    
    with tab1:
        if st.session_state.active_tab != "🎮 Play Game":
            st.session_state.active_tab = "🎮 Play Game"
        show_game_tab(supabase, random_client)
    
    with tab2:
        if st.session_state.active_tab != "📊 Global Analytics":
            st.session_state.active_tab = "📊 Global Analytics"
        show_global_analytics(supabase)
    
    with tab3:
        if st.session_state.active_tab != "👤 My Analytics":
            st.session_state.active_tab = "👤 My Analytics"
        
        # Check if user email is available
        if 'user_email' in st.session_state and st.session_state.user_email:
            show_user_analytics(supabase, st.session_state.user_email)
        else:
            st.info("🎯 Play a game first to see your personal analytics!")
            st.markdown("Your personal statistics will appear here after you play at least one game.")

if __name__ == "__main__":
    main()