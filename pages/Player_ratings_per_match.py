import streamlit as st
import pandas as pd
import os

DATA_PATH = "csv/csv24_25"
LEAGUES_PATH = os.path.join(DATA_PATH, "leagues_games")
NOTES_PLAYERS_PATH = os.path.join(DATA_PATH, "ratings", "data_players.csv")
NOTES_GOALS_PATH = os.path.join(DATA_PATH, "ratings", "data_goals.csv")

df_players = pd.read_csv(NOTES_PLAYERS_PATH)
leagues = df_players["League"].dropna().unique().tolist()

st.set_page_config(page_title="Player ratings per match")
st.sidebar.title("Select Parameters")

league = st.sidebar.selectbox("League", leagues)

league_file = os.path.join(LEAGUES_PATH, f"{league}_games.csv")
if not os.path.exists(league_file):
    st.error(f"File not found for {league}")
    st.stop()

df_games = pd.read_csv(league_file)

game_weeks = df_games["Game Week"].dropna().unique()
game_weeks_sorted = sorted(game_weeks, key=lambda x: int(str(x).strip("J").strip()))
game_week = st.sidebar.selectbox("Game Week", game_weeks_sorted)

df_game_week = df_games[df_games["Game Week"] == game_week]
matches = df_game_week.apply(lambda row: f"{row['Home Team']} vs {row['Away Team']}", axis=1).tolist()
selected_match = st.sidebar.selectbox("Match", matches)

home_team, away_team = selected_match.split(" vs ")

match_info = df_game_week[(df_game_week["Home Team"] == home_team) & (df_game_week["Away Team"] == away_team)].iloc[0]
score = match_info["Score"] if "Score" in match_info else "Score not available"
referee = match_info["Referee"] if "Referee" in match_info else "Referee not available"
attendance = match_info["Attendance"] if "Attendance" in match_info else "Attendance not available"
venue = match_info["Venue"] if "Venue" in match_info else "Venue not available"

df_players = pd.read_csv(NOTES_PLAYERS_PATH)
df_goalkeepers = pd.read_csv(NOTES_GOALS_PATH)

df_all_players = pd.concat([df_players, df_goalkeepers], ignore_index=True)

df_home = df_all_players[
    (df_all_players["Team"] == home_team) &
    (df_all_players["Game Week"] == game_week) &
    (df_all_players["League"] == league)
].copy()

df_away = df_all_players[
    (df_all_players["Team"] == away_team) &
    (df_all_players["Game Week"] == game_week) &
    (df_all_players["League"] == league)
].copy()

for df in [df_home, df_away]:
    if "ID" in df.columns:
        df.drop(columns=["ID"], inplace=True)

df_home_sorted = df_home.sort_values(by="Rate", ascending=False)
df_away_sorted = df_away.sort_values(by="Rate", ascending=False)

def add_average(df):
    avg = round(df["Rate"].mean(), 2)
    df_result = df[["Player", "Rate"]].copy()
    df_result = df_result.set_index("Player")
    df_result.loc["Average"] = avg
    return df_result

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
