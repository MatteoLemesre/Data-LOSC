import streamlit as st
import pandas as pd
import os

# --- Functions ---
def add_average(df):
    avg = round(df["Rating"].mean(), 2)
    df_result = df[["Player", "Rating"]].copy()
    df_result = df_result.set_index("Player")
    df_result.loc["Average"] = avg
    return df_result

def get_season_code(selected_season):
    if selected_season == "2024 2025":
        return "24_25"
    elif selected_season == "2025 2026":
        return "25_26"
    return None

def load_league_file(path, league):
    file_path = os.path.join(path, f"{league}_games.csv")
    if not os.path.exists(file_path):
        st.error(f"File not found for {league}")
        st.stop()
    return pd.read_csv(file_path)

def get_match_info(df, home, away):
    return df[
        (df["Home Team"] == home) & 
        (df["Away Team"] == away)
    ].iloc[0]

# --- Page config ---
st.set_page_config(page_title="Player ratings per match")
st.sidebar.title("Select Parameters")

selected_season = st.sidebar.selectbox("Season", ["2024 2025", "2025 2026"], index=0)
season_code = get_season_code(selected_season)

path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))

ratings_players_path = os.path.join(path_folder, "ratings", "data_players.csv")
ratings_goalkeepers_path = os.path.join(path_folder, "ratings", "data_goals.csv")
leagues_path = os.path.join(path_folder, "leagues_games")

df_players = pd.read_csv(ratings_players_path)
leagues = df_players["League"].dropna().unique().tolist()

selected_league = st.sidebar.selectbox("League", leagues)
df_games = load_league_file(leagues_path, selected_league)

game_weeks = df_games["Game Week"].dropna().unique()
game_weeks_sorted = sorted(game_weeks, key=lambda x: int(str(x).strip("J").strip()))
selected_week = st.sidebar.selectbox("Game Week", game_weeks_sorted)

df_selected_week = df_games[df_games["Game Week"] == selected_week]
matches = df_selected_week.apply(lambda row: f"{row['Home Team']} vs {row['Away Team']}", axis=1).tolist()
selected_match = st.sidebar.selectbox("Match", matches)

home_team, away_team = selected_match.split(" vs ")
match_info = get_match_info(df_selected_week, home_team, away_team)

score = match_info.get("Score", "Score not available")
referee = match_info.get("Referee", "Referee not available")
attendance = match_info.get("Attendance", "Attendance not available")
venue = match_info.get("Venue", "Venue not available")

df_gk = pd.read_csv(ratings_goalkeepers_path)
df_all = pd.concat([df_players, df_gk], ignore_index=True)

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

for df in [df_home, df_away]:
    if "ID" in df.columns:
        df.drop(columns=["ID"], inplace=True)

df_home_sorted = df_home.sort_values(by="Rating", ascending=False)
df_away_sorted = df_away.sort_values(by="Rating", ascending=False)

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