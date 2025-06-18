import streamlit as st
import pandas as pd
import os

# --- File paths ---
path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", "csv24_25"))
leagues_path = os.path.join(path_folder, "leagues_games")
ratings_players_path = os.path.join(path_folder, "ratings", "data_players.csv")
ratings_goalkeepers_path = os.path.join(path_folder, "ratings", "data_goals.csv")

# --- Load data ---
df_players = pd.read_csv(ratings_players_path)
leagues = df_players["League"].dropna().unique().tolist()

# --- Streamlit setup ---
st.set_page_config(page_title="Player ratings per match")
st.sidebar.title("Select Parameters")

# --- League selection ---
selected_league = st.sidebar.selectbox("League", leagues)
league_file = os.path.join(leagues_path, f"{selected_league}_games.csv")

if not os.path.exists(league_file):
    st.error(f"File not found for {selected_league}")
    st.stop()

df_games = pd.read_csv(league_file)

# --- Game week selection ---
game_weeks = df_games["Game Week"].dropna().unique()
game_weeks_sorted = sorted(game_weeks, key=lambda x: int(str(x).strip("J").strip()))
selected_week = st.sidebar.selectbox("Game Week", game_weeks_sorted)

df_selected_week = df_games[df_games["Game Week"] == selected_week]
matches = df_selected_week.apply(lambda row: f"{row['Home Team']} vs {row['Away Team']}", axis=1).tolist()
selected_match = st.sidebar.selectbox("Match", matches)

# --- Match metadata ---
home_team, away_team = selected_match.split(" vs ")
match_info = df_selected_week[
    (df_selected_week["Home Team"] == home_team) & 
    (df_selected_week["Away Team"] == away_team)
].iloc[0]

score = match_info.get("Score", "Score not available")
referee = match_info.get("Referee", "Referee not available")
attendance = match_info.get("Attendance", "Attendance not available")
venue = match_info.get("Venue", "Venue not available")

# --- Load ratings ---
df_gk = pd.read_csv(ratings_goalkeepers_path)
df_all = pd.concat([df_players, df_gk], ignore_index=True)

# --- Filter by team & match ---
df_home = df_all[
    (df_all["Team"] == home_team) &
    (df_all["Game Week"] == selected_week) &
    (df_all["League"] == selected_league)
].copy()

df_away = df_all[
    (df_all["Team"] == away_team) &
    (df_all["Game Week"] == selected_week) &
    (df_all["League"] == selected_league)
].copy()

# --- Clean ---
for df in [df_home, df_away]:
    if "ID" in df.columns:
        df.drop(columns=["ID"], inplace=True)

df_home_sorted = df_home.sort_values(by="Rating", ascending=False)
df_away_sorted = df_away.sort_values(by="Rating", ascending=False)

# --- Add team average ---
def add_average(df):
    avg = round(df["Rating"].mean(), 2)
    df_result = df[["Player", "Rating"]].copy()
    df_result = df_result.set_index("Player")
    df_result.loc["Average"] = avg
    return df_result

# --- Display ---
st.title(f"{home_team} vs {away_team}")
st.subheader(f"Score: {score}")
st.subheader(f"Referee: {referee}")
st.subheader(f"Attendance: {attendance}")
st.subheader(f"Venue: {venue}")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### {home_team}")
    st.dataframe(add_average(df_home_sorted), use_container_width=True)

with col2:
    st.markdown(f"### {away_team}")
    st.dataframe(add_average(df_away_sorted), use_container_width=True)
