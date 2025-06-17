import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Top Matchs stats")

path_folder = ""

match_path_template = os.path.join(path_folder, "leagues_games", "{}_games.csv")
data_clean_players_path = os.path.join(path_folder, "clean", "data_players.csv")
data_clean_goals_path = os.path.join(path_folder, "clean", "data_goals.csv")
data_notes_players_path = os.path.join(path_folder, "notes", "data_players.csv")
data_notes_goals_path = os.path.join(path_folder, "notes", "data_goals.csv")

df_players = pd.read_csv(data_clean_players_path)
df_goals = pd.read_csv(data_clean_goals_path)
df_notes_players = pd.read_csv(data_notes_players_path)
df_notes_goals = pd.read_csv(data_notes_goals_path)

STATS_PLAYERS = [
    col for col in df_players.columns if col not in [
        "Player", "Game Week", "Team", "League", "Minutes", "Age", "Position", "Nationality"
    ]
]

STATS_GOALS = [
    col for col in df_goals.columns if col not in [
        "Player", "Game Week", "Team", "League", "Minutes", "Age", "Nationality", "Position"
    ]
]

df_goals["Position"] = "GK"
df_combined = pd.concat([df_players, df_goals], ignore_index=True)

df_notes_combined = pd.concat([df_notes_players, df_notes_goals], ignore_index=True)

df = df_combined.merge(
    df_notes_combined,
    on=["Player", "Game Week", "Team", "League", "Minutes", "Position"],
    how="left"
)

st.sidebar.title("Select Parameters")

selected_positions = st.sidebar.multiselect("Position", df_combined["Position"].unique())

if set(selected_positions) == {"GK"}:
    stats_available = STATS_GOALS
    df = df[df["Position"] == "GK"]
else:
    stats_available = STATS_PLAYERS
    df = df[df["Position"].isin(selected_positions)]

selected_stat = st.sidebar.selectbox("Statistic to display", sorted(stats_available))

num_players = st.sidebar.slider("Number of top performances to display", min_value=5, max_value=100, value=20)

available_leagues = sorted(df["League"].dropna().unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = available_leagues if all_leagues else [st.sidebar.selectbox("Choose a league", available_leagues)]

df = df[df["League"].isin(selected_leagues)]
df = df[df[selected_stat].notna()]

games_dfs = {}
for league in df["League"].unique():
    try:
        games_dfs[league] = pd.read_csv(match_path_template.format(league))
    except FileNotFoundError:
        continue

def get_opponent_and_score(row):
    league = row["League"]
    game_week = row["Game Week"]
    team = row["Team"]

    df_games = games_dfs.get(league)
    if df_games is None:
        return pd.Series(["Unknown", "N/A"])

    match = df_games[df_games["Game Week"] == game_week]
    for _, m in match.iterrows():
        if m["Home Team"] == team:
            return pd.Series([m["Away Team"], m["Score"]])
        elif m["Away Team"] == team:
            return pd.Series([m["Home Team"], m["Score"]])
    return pd.Series(["Unknown", "N/A"])

st.title("📈 Top Individual Performances")

if selected_positions and selected_stat and selected_leagues:
    df[["Opponent", "Score"]] = df.apply(get_opponent_and_score, axis=1)

    df = df[df[selected_stat].notna() & df["Score"].notna()]

    df_sorted = df.sort_values(by=selected_stat, ascending=False).head(num_players)

    df_display = df_sorted[
        [
            "Player",
            selected_stat,
            "Rate",        
            "Score",
            "Team",
            "Opponent",
            "League",
            "Game Week",
            "Minutes"
        ]
    ].rename(columns={
        selected_stat: "Value",
        "Team": "Club",
        "Opponent": "Opponent",
        "Score": "Score",
        "League": "League",
        "Game Week": "Game Week",
        "Minutes": "Minutes Played"
    })

    df_display = df_display.set_index("Player")
    st.dataframe(df_display, use_container_width=True)
