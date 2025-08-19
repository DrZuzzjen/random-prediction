# 🎯 Random Prediction Game

A fun web-based prediction game built with Streamlit where players try to predict random numbers and compete on a leaderboard!

## 🎮 How to Play

1. **Predict Numbers**: Enter 10 numbers between 1-99
2. **Generate Random Numbers**: Click the button to generate 10 random numbers using Random.org API  
3. **Get Your Score**: See how many of your predictions matched the random numbers (0-10 points)
4. **Save Your Score**: Enter your name and email to save your best score to the leaderboard
5. **Compete**: View the top 10 players on the sidebar leaderboard

## 🚀 Live Demo

Visit the deployed app: [Random Prediction Game](https://random-prediction.streamlit.app) *(Replace with your actual Streamlit Cloud URL)*

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/) - Python web app framework
- **Database**: [Supabase](https://supabase.com/) - PostgreSQL database with real-time features
- **Random Numbers**: [Random.org API](https://www.random.org/clients/http/) - True random number generation
- **Deployment**: [Streamlit Cloud](https://streamlit.io/cloud) - Free hosting for Streamlit apps

## 🏗️ Local Development

### Prerequisites

- Python 3.9+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/DrZuzzjen/random-prediction.git
cd random-prediction
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Random.org API Key (get from https://api.random.org/api-keys/beta)
RANDOM_API_KEY=your_random_org_api_key
RANDOM_API_KEY_HASHED=your_hashed_api_key

# Supabase Configuration (get from your Supabase project dashboard)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SECRET_KEY=your_supabase_secret_key
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
SUPABASE_PROJECT_ID=your_project_id
```

### 5. Set Up Database

1. **Create a Supabase Account**: Go to [supabase.com](https://supabase.com) and create a new project
2. **Run Database Setup**: Copy the contents of `database_setup.sql` and execute it in your Supabase SQL Editor
3. **Test Connection**: Run the database test script:

```bash
python test_db_setup.py
```

### 6. Test Random.org API

Test your Random.org API integration:

```bash
python api_client.py
```

### 7. Run the Application

```bash
streamlit run streamlit_app.py
```

The app will be available at `http://localhost:8501`

## 🗄️ Database Schema

The app uses a single `leaderboard` table:

```sql
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
```

## 🔑 API Keys Setup

### Random.org API Key

1. Visit [Random.org API Keys](https://api.random.org/api-keys/beta)
2. Create a free account
3. Generate an API key
4. Add it to your `.env` file

### Supabase Keys

1. Create a project at [supabase.com](https://supabase.com)
2. Go to Project Settings → API
3. Copy the following:
   - Project URL → `SUPABASE_URL`
   - Project Reference ID → `SUPABASE_PROJECT_ID` 
   - `anon public` key → `SUPABASE_PUBLISHABLE_KEY`
   - `service_role secret` key → `SUPABASE_SECRET_KEY`

## 🚢 Deployment

### Streamlit Cloud Deployment

1. **Push to GitHub**: Ensure your code is pushed to a GitHub repository
2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Choose `streamlit_app.py` as the main file
3. **Add Secrets**: In your Streamlit Cloud app settings, add all the environment variables from your `.env` file

### Environment Variables for Deployment

Copy the values from `.streamlit/secrets.toml` into your deployment platform's secret management system.

## 📁 Project Structure

```
random-prediction/
├── streamlit_app.py          # Main Streamlit application
├── api_client.py             # Random.org API client
├── test_db_setup.py          # Database connection test
├── database_setup.sql        # Database schema and setup
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (local)
├── .streamlit/
│   └── secrets.toml          # Streamlit secrets template
└── README.md                 # This file
```

## 🎯 Game Features

- ✅ **True Random Numbers**: Uses Random.org API for genuine randomness
- ✅ **Persistent Leaderboard**: Scores saved to Supabase database
- ✅ **Privacy Focused**: Email addresses stored but never displayed
- ✅ **High Score Tracking**: Only best scores are shown on leaderboard
- ✅ **Responsive UI**: Clean, mobile-friendly Streamlit interface
- ✅ **Real-time Updates**: Live leaderboard updates

## 🔮 Future Enhancements

- [ ] Multiple game modes (1-10, 1-1000 ranges)
- [ ] User authentication and profiles  
- [ ] Daily/weekly leaderboards
- [ ] Game statistics and analytics
- [ ] Social sharing features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙋‍♂️ Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/DrZuzzjen/random-prediction/issues) page
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about your environment and the issue

---

**Happy Predicting! 🎯**