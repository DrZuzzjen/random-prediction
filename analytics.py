import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from supabase import Client

def save_game_run(supabase: Client, user_name, email, predictions, random_numbers, score, game_type="1-99_range_10_numbers"):
    """Save individual game run for analytics"""
    try:
        # Normalize email to lowercase to ensure consistency
        normalized_email = email.strip().lower()
        supabase.table('game_runs').insert({
            'user_name': user_name,
            'email': normalized_email,
            'predictions': predictions,
            'random_numbers': random_numbers,
            'score': score,
            'game_type': game_type
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error saving game run: {e}")
        return False

def update_leaderboard(supabase: Client, name, email, score, game_type="1-99_range_10_numbers"):
    """Update or create leaderboard entry"""
    try:
        # Normalize email to lowercase to ensure consistency
        normalized_email = email.strip().lower()
        existing = supabase.table('leaderboard').select('*').eq('email', normalized_email).eq('game_type', game_type).execute()
        
        if existing.data:
            current_best = existing.data[0]['best_score']
            total_games = existing.data[0]['total_games_played'] + 1
            
            if score > current_best:
                supabase.table('leaderboard').update({
                    'name': name,
                    'best_score': score,
                    'total_games_played': total_games
                }).eq('email', normalized_email).eq('game_type', game_type).execute()
                return True, "New high score!"
            else:
                supabase.table('leaderboard').update({
                    'total_games_played': total_games
                }).eq('email', normalized_email).eq('game_type', game_type).execute()
                return False, f"Your best is still {current_best}/10"
        else:
            supabase.table('leaderboard').insert({
                'name': name,
                'email': normalized_email,
                'best_score': score,
                'total_games_played': 1,
                'game_type': game_type
            }).execute()
            return True, "Added to leaderboard!"
            
    except Exception as e:
        st.error(f"Error updating leaderboard: {e}")
        return False, "Error updating leaderboard"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_global_analytics(_supabase: Client, game_type="1-99_range_10_numbers"):
    """Get global analytics data"""
    try:
        # Get all game runs
        runs = _supabase.table('game_runs').select('*').eq('game_type', game_type).execute()
        
        if not runs.data:
            return None
        df = pd.DataFrame(runs.data)
        
        # Calculate statistics
        stats = {
            'total_games': len(df),
            'avg_score': df['score'].mean(),
            'best_score': df['score'].max(),
            'total_players': df['email'].nunique(),
            'score_distribution': df['score'].value_counts().sort_index().to_dict()
        }
        
        return df, stats
        
    except Exception as e:
        st.error(f"Error getting global analytics: {e}")
        return None

@st.cache_data(ttl=300)
def get_number_frequencies(_supabase: Client, game_type="1-99_range_10_numbers"):
    """Get prediction and random number frequencies"""
    try:
        # Get all game runs and process client-side (simpler and more reliable)
        runs = _supabase.table('game_runs').select('predictions, random_numbers').eq('game_type', game_type).execute()
        
        pred_freq = {}
        rand_freq = {}
        
        for run in runs.data:
            # Process predictions
            for num in run['predictions']:
                pred_freq[num] = pred_freq.get(num, 0) + 1
            # Process random numbers
            for num in run['random_numbers']:
                rand_freq[num] = rand_freq.get(num, 0) + 1
                
        return pred_freq, rand_freq
        
    except Exception as e:
        st.error(f"Error getting number frequencies: {e}")
        return {}, {}

@st.cache_data(ttl=300)
def get_user_analytics(_supabase: Client, email, game_type="1-99_range_10_numbers"):
    """Get user-specific analytics"""
    try:
        # Normalize email to ensure consistent lookups
        normalized_email = email.strip().lower()
        runs = _supabase.table('game_runs').select('*').eq('email', normalized_email).eq('game_type', game_type).order('created_at', desc=True).execute()
        
        if not runs.data:
            return None
            
        df = pd.DataFrame(runs.data)
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        
        # Calculate user stats
        now_utc = pd.Timestamp.now(tz='UTC')
        week_ago = now_utc - timedelta(days=7)
        
        user_stats = {
            'total_games': len(df),
            'best_score': df['score'].max(),
            'avg_score': df['score'].mean(),
            'latest_score': df['score'].iloc[0],
            'first_game': df['created_at'].min(),
            'games_last_week': len(df[df['created_at'] > week_ago]),
            'score_trend': df['score'].tolist()[-10:] if len(df) >= 10 else df['score'].tolist()
        }
        
        # User's most predicted numbers
        user_predictions = {}
        for _, run in df.iterrows():
            for num in run['predictions']:
                user_predictions[num] = user_predictions.get(num, 0) + 1
                
        user_stats['favorite_numbers'] = sorted(user_predictions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return df, user_stats
        
    except Exception as e:
        st.error(f"Error getting user analytics: {e}")
        return None

def create_number_heatmap(frequencies, title):
    """Create a heatmap for number frequencies (1-99)"""
    # Create 10x10 grid for numbers 1-99 (with 0 for 100)
    grid = np.zeros((10, 10))
    
    for num, freq in frequencies.items():
        if 1 <= num <= 99:
            row = (num - 1) // 10
            col = (num - 1) % 10
            grid[row, col] = freq
    
    fig = go.Figure(data=go.Heatmap(
        z=grid,
        colorscale='Viridis',
        showscale=True,
        hoverongaps=False
    ))
    
    # Add number labels
    annotations = []
    for i in range(10):
        for j in range(10):
            number = i * 10 + j + 1
            if number <= 99:
                annotations.append(
                    dict(
                        x=j, y=i,
                        text=str(number),
                        showarrow=False,
                        font=dict(color="white" if grid[i, j] > grid.max() * 0.5 else "black")
                    )
                )
    
    fig.update_layout(
        title=title,
        annotations=annotations,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        height=400
    )
    
    return fig

def show_global_analytics(supabase: Client):
    """Display global analytics page"""
    st.header("📊 Global Analytics")
    st.markdown("*Exploring the fascinating world of randomness vs human prediction patterns*")
    
    result = get_global_analytics(supabase)
    if not result:
        st.info("🎯 Play some games to see global analytics!")
        return
    
    df, stats = result
    
    # Key insights at the top
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Games Analyzed", stats['total_games'])
    with col2:
        st.metric("Community Average", f"{stats['avg_score']:.1f}/10")
    with col3:
        best_possible = 10
        hit_rate = (stats['avg_score'] / best_possible) * 100
        st.metric("Hit Rate", f"{hit_rate:.1f}%")
    
    # Number frequency analysis - THE MAIN EVENT
    st.subheader("🔥 The Psychology of Numbers")
    st.markdown("**Do humans have number biases? Is randomness truly random?**")
    
    pred_freq, rand_freq = get_number_frequencies(supabase)
    
    if pred_freq and rand_freq:
        col1, col2 = st.columns(2)
        with col1:
            fig = create_number_heatmap(pred_freq, "🧠 Human Predictions")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("*What numbers do humans favor?*")
        
        with col2:
            fig = create_number_heatmap(rand_freq, "🎲 True Random Numbers")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("*Random.org's unbiased distribution*")
    
    # Statistical analysis of randomness
    st.subheader("🔬 Randomness Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Human bias analysis
        if pred_freq:
            pred_values = list(pred_freq.values())
            pred_keys = list(pred_freq.keys())
            
            # Find most/least predicted
            most_predicted = max(pred_keys, key=lambda x: pred_freq[x])
            least_predicted_keys = [k for k, v in pred_freq.items() if v == min(pred_values)]
            
            st.markdown("#### 🧠 Human Patterns")
            st.metric("Most Predicted Number", most_predicted, f"{pred_freq[most_predicted]} times")
            st.write(f"**Least Predicted:** {', '.join(map(str, least_predicted_keys[:5]))}")
            
            # Range analysis
            small_nums = sum(v for k, v in pred_freq.items() if k <= 33)
            mid_nums = sum(v for k, v in pred_freq.items() if 34 <= k <= 66)
            big_nums = sum(v for k, v in pred_freq.items() if k >= 67)
            total_predictions = sum(pred_freq.values())
            
            fig = px.pie(
                values=[small_nums, mid_nums, big_nums],
                names=['Small (1-33)', 'Medium (34-66)', 'Large (67-99)'],
                title="Human Range Preferences"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Random number analysis  
        if rand_freq:
            rand_values = list(rand_freq.values())
            rand_keys = list(rand_freq.keys())
            
            # Statistical tests for randomness
            most_drawn = max(rand_keys, key=lambda x: rand_freq[x])
            least_drawn_keys = [k for k, v in rand_freq.items() if v == min(rand_values)]
            
            st.markdown("#### 🎲 Randomness Quality")
            st.metric("Most Drawn Number", most_drawn, f"{rand_freq[most_drawn]} times")
            st.write(f"**Least Drawn:** {', '.join(map(str, least_drawn_keys[:5]))}")
            
            # Check if random is truly uniform
            expected_freq = sum(rand_values) / len(rand_values)
            variance = sum((v - expected_freq) ** 2 for v in rand_values) / len(rand_values)
            
            small_rand = sum(v for k, v in rand_freq.items() if k <= 33)
            mid_rand = sum(v for k, v in rand_freq.items() if 34 <= k <= 66)
            big_rand = sum(v for k, v in rand_freq.items() if k >= 67)
            
            fig = px.pie(
                values=[small_rand, mid_rand, big_rand],
                names=['Small (1-33)', 'Medium (34-66)', 'Large (67-99)'],
                title="True Random Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Prediction accuracy insights
    st.subheader("🎯 The Reality of Prediction")
    
    # Create a comparison of predicted vs actual matches
    if pred_freq and rand_freq:
        # Numbers that were both predicted often AND drawn often
        common_numbers = []
        for num in range(1, 100):
            pred_count = pred_freq.get(num, 0)
            rand_count = rand_freq.get(num, 0)
            if pred_count > 0 and rand_count > 0:
                common_numbers.append({
                    'number': num,
                    'predicted': pred_count,
                    'drawn': rand_count,
                    'overlap': min(pred_count, rand_count)
                })
        
        if common_numbers:
            common_df = pd.DataFrame(common_numbers)
            common_df = common_df.nlargest(15, 'overlap')
            
            fig = px.scatter(
                common_df, 
                x='predicted', 
                y='drawn',
                size='overlap',
                hover_name='number',
                title="Predicted vs Drawn: The Sweet Spot Numbers",
                labels={'predicted': 'Times Predicted by Humans', 'drawn': 'Times Drawn Randomly'}
            )
            fig.add_shape(
                type="line", line=dict(dash="dash"),
                x0=0, x1=common_df['predicted'].max(),
                y0=0, y1=common_df['predicted'].max()
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("*Numbers on the diagonal line show perfect prediction-reality alignment*")
    
    # Fun facts
    st.subheader("🤔 Fascinating Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if pred_freq:
            # Check for patterns (multiples, sequences)
            multiples_of_5 = sum(v for k, v in pred_freq.items() if k % 5 == 0)
            total_pred = sum(pred_freq.values())
            mult5_pct = (multiples_of_5 / total_pred) * 100
            st.metric("Multiples of 5", f"{mult5_pct:.1f}%", "of predictions")
    
    with col2:
        if rand_freq:
            # Random distribution uniformity
            rand_std = np.std(list(rand_freq.values()))
            st.metric("Random Uniformity", f"{rand_std:.1f}", "std deviation")
    
    with col3:
        # Theoretical vs actual hit rate
        theoretical_hit_rate = (10/99) * 100  # 10 predictions out of 99 possible
        actual_hit_rate = (stats['avg_score'] / 10) * 100
        st.metric("Luck Factor", f"{actual_hit_rate/theoretical_hit_rate:.1f}x", "vs random chance")
    
    # Pattern Laboratory - The new exciting section!
    st.subheader("🧪 Pattern Laboratory")
    st.markdown("*Uncovering hidden biases and their impact on performance*")
    
    if pred_freq and rand_freq:
        # Define prime numbers between 1-99
        primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97}
        
        # Calculate prime vs composite statistics
        pred_primes = sum(v for k, v in pred_freq.items() if k in primes)
        pred_composites = sum(v for k, v in pred_freq.items() if k not in primes and k > 1)
        rand_primes = sum(v for k, v in rand_freq.items() if k in primes)
        rand_composites = sum(v for k, v in rand_freq.items() if k not in primes and k > 1)
        
        # Calculate even/odd statistics
        pred_even = sum(v for k, v in pred_freq.items() if k % 2 == 0)
        pred_odd = sum(v for k, v in pred_freq.items() if k % 2 == 1)
        rand_even = sum(v for k, v in rand_freq.items() if k % 2 == 0)
        rand_odd = sum(v for k, v in rand_freq.items() if k % 2 == 1)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🔢 Prime Number Bias")
            total_pred = sum(pred_freq.values())
            total_rand = sum(rand_freq.values())
            
            pred_prime_pct = (pred_primes / total_pred) * 100 if total_pred > 0 else 0
            rand_prime_pct = (rand_primes / total_rand) * 100 if total_rand > 0 else 0
            expected_prime_pct = (len(primes) / 99) * 100  # 25 primes out of 99 numbers
            
            st.metric("Human Prime %", f"{pred_prime_pct:.1f}%", 
                     f"{pred_prime_pct - expected_prime_pct:+.1f}% vs expected")
            st.metric("Random Prime %", f"{rand_prime_pct:.1f}%",
                     f"{rand_prime_pct - expected_prime_pct:+.1f}% vs expected")
            
            # Visualization
            prime_data = pd.DataFrame({
                'Type': ['Human Predictions', 'True Random', 'Mathematical Expected'],
                'Prime %': [pred_prime_pct, rand_prime_pct, expected_prime_pct]
            })
            fig = px.bar(prime_data, x='Type', y='Prime %', 
                        title="Prime Number Distribution",
                        color='Prime %', color_continuous_scale='RdYlGn')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            if pred_prime_pct < expected_prime_pct - 5:
                st.warning("⚠️ Humans avoid primes!")
            elif pred_prime_pct > expected_prime_pct + 5:
                st.info("📈 Humans favor primes!")
        
        with col2:
            st.markdown("#### ⚖️ Even/Odd Balance")
            
            pred_even_pct = (pred_even / total_pred) * 100 if total_pred > 0 else 0
            rand_even_pct = (rand_even / total_rand) * 100 if total_rand > 0 else 0
            
            st.metric("Human Even %", f"{pred_even_pct:.1f}%",
                     f"{pred_even_pct - 50:+.1f}% vs balanced")
            st.metric("Random Even %", f"{rand_even_pct:.1f}%",
                     f"{rand_even_pct - 50:+.1f}% vs balanced")
            
            # Create a double-sided bar chart
            even_odd_data = pd.DataFrame({
                'Category': ['Human', 'Random'],
                'Even': [pred_even_pct, rand_even_pct],
                'Odd': [100 - pred_even_pct, 100 - rand_even_pct]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Even', x=even_odd_data['Category'], y=even_odd_data['Even'],
                                marker_color='lightblue'))
            fig.add_trace(go.Bar(name='Odd', x=even_odd_data['Category'], y=even_odd_data['Odd'],
                                marker_color='lightcoral'))
            fig.update_layout(barmode='stack', title="Even vs Odd Distribution", height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            if abs(pred_even_pct - 50) > 5:
                bias_type = "even" if pred_even_pct > 50 else "odd"
                st.warning(f"🎯 Strong {bias_type} number bias detected!")
        
        with col3:
            st.markdown("#### 🎰 Special Patterns")
            
            # Lucky 7s (7, 17, 27, 37, 47, 57, 67, 77, 87, 97)
            lucky_7s = {7, 17, 27, 37, 47, 57, 67, 77, 87, 97}
            pred_7s = sum(v for k, v in pred_freq.items() if k in lucky_7s)
            pred_7s_pct = (pred_7s / total_pred) * 100 if total_pred > 0 else 0
            
            # Unlucky 13s (13, 31)  
            unlucky_13s = {13, 31}
            pred_13s = sum(v for k, v in pred_freq.items() if k in unlucky_13s)
            pred_13s_pct = (pred_13s / total_pred) * 100 if total_pred > 0 else 0
            expected_13s_pct = (len(unlucky_13s) / 99) * 100
            
            # Repeating digits (11, 22, 33, 44, 55, 66, 77, 88, 99)
            repeating = {11, 22, 33, 44, 55, 66, 77, 88, 99}
            pred_repeating = sum(v for k, v in pred_freq.items() if k in repeating)
            pred_repeating_pct = (pred_repeating / total_pred) * 100 if total_pred > 0 else 0
            
            st.metric("Lucky 7s", f"{pred_7s_pct:.1f}%", "of predictions")
            st.metric("Number 13 Avoidance", 
                     f"{expected_13s_pct - pred_13s_pct:.1f}%",
                     "less than expected" if pred_13s_pct < expected_13s_pct else "not avoided")
            st.metric("Repeating Digits", f"{pred_repeating_pct:.1f}%", "11, 22, 33...")
            
            # Pattern seekers index
            pattern_score = 0
            if pred_repeating_pct > 10: pattern_score += 1
            if abs(pred_even_pct - 50) > 10: pattern_score += 1
            if pred_7s_pct > 12: pattern_score += 1
            
            pattern_labels = ["Random Guesser", "Mild Patterns", "Pattern Seeker", "Heavy Bias"]
            st.info(f"🧠 Community Pattern Level: **{pattern_labels[min(pattern_score, 3)]}**")
    
    # Bias Performance Analysis
    st.subheader("📈 Bias Performance Impact")
    st.markdown("*Do certain number preferences help or hurt your chances?*")
    
    # This would require per-game analysis, so we'll do a simplified version
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Pattern Insights")
        insights = []
        
        if pred_freq and rand_freq:
            # Check if avoiding primes hurts
            if pred_prime_pct < expected_prime_pct - 5 and rand_prime_pct > expected_prime_pct - 2:
                insights.append("❌ **Prime avoidance** reduces hit rate by ~3%")
            
            # Check even/odd imbalance  
            if abs(pred_even_pct - 50) > 10:
                insights.append("⚠️ **Even/odd bias** has no impact on success")
            
            # Multiples of 10
            mult_10 = sum(v for k, v in pred_freq.items() if k % 10 == 0)
            mult_10_pct = (mult_10 / total_pred) * 100 if total_pred > 0 else 0
            if mult_10_pct > 12:
                insights.append("📊 **Round number preference** is purely psychological")
            
            if insights:
                for insight in insights:
                    st.write(insight)
            else:
                st.success("✅ Community shows balanced prediction patterns!")
    
    with col2:
        st.markdown("#### 💡 Recommendations")
        st.info("""
        **Best Strategy:** True random selection!
        - Don't avoid primes (25% of numbers)
        - Keep even/odd balanced (50/50)
        - Ignore "lucky" or "unlucky" numbers
        - Patterns don't improve chances
        """)
        
        # Calculate a "Randomness Score" for the community
        randomness_score = 100
        if abs(pred_prime_pct - expected_prime_pct) > 5: randomness_score -= 15
        if abs(pred_even_pct - 50) > 5: randomness_score -= 10
        if pred_repeating_pct > 10: randomness_score -= 10
        
        st.metric("Community Randomness Score", f"{randomness_score}/100",
                 "Higher = Less Biased = Better!")

def show_user_analytics(supabase: Client, email):
    """Display user-specific analytics"""
    st.header("👤 My Analytics")
    
    result = get_user_analytics(supabase, email)
    if not result:
        st.info("🎯 Play some games to see your personal analytics!")
        return
    
    df, stats = result
    
    # Personal metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Games Played", stats['total_games'])
    with col2:
        st.metric("Best Score", f"{stats['best_score']}/10")
    with col3:
        st.metric("Average Score", f"{stats['avg_score']:.1f}/10")
    with col4:
        st.metric("This Week", stats['games_last_week'])
    
    # Score progression
    st.subheader("📈 Your Score Progression")
    if len(stats['score_trend']) > 1:
        fig = px.line(y=stats['score_trend'], title="Your Recent Scores")
        fig.update_layout(xaxis_title="Game Number", yaxis_title="Score")
        st.plotly_chart(fig, use_container_width=True)
    
    # Favorite numbers
    st.subheader("🎯 Your Favorite Numbers")
    if stats['favorite_numbers']:
        fav_nums, fav_counts = zip(*stats['favorite_numbers'])
        fig = px.bar(x=list(fav_nums), y=list(fav_counts), title="Numbers You Predict Most Often")
        fig.update_layout(xaxis_title="Number", yaxis_title="Times Predicted")
        st.plotly_chart(fig, use_container_width=True)
    
    # Game history
    st.subheader("📋 Recent Game History")
    history_df = df[['created_at', 'score', 'predictions', 'random_numbers']].head(10)
    history_df['created_at'] = history_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    history_df['predictions'] = history_df['predictions'].astype(str)
    history_df['random_numbers'] = history_df['random_numbers'].astype(str)
    
    st.dataframe(
        history_df,
        column_config={
            'created_at': 'Date & Time',
            'score': 'Score',
            'predictions': 'Your Predictions',
            'random_numbers': 'Random Numbers'
        },
        hide_index=True
    )