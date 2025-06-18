import streamlit as st
import pandas as pd
import os

# --- Define stats by player position ---
def get_player_stats(positions):
    stats = set()
    for pos in positions:
        if pos == 'FW':
            stats.update([
                'Goals', 'Assists', 'Shots on Target', 'Expected Goals (xG)',
                'Shot-Creating Actions (SCA)', 'Goal-Creating Actions (GCA)', 'Key Passes',
                'Passes into Final Third', 'Passes into Penalty Area', 'Progressive Passes',
                'Successful Take-Ons', 'Crosses', 'Expected Assists (xA)',
                'Carries into Final Third', 'Carries into Penalty Area'
            ])
        elif pos == 'MF':
            stats.update([
                'Assists', 'Key Passes',
                'Passes Completed (Short)', 'Passes Completed (Medium)', 'Passes Completed (Long)',
                'Progressive Passes', 'Through Balls', 'Switches', 'Successful Take-Ons',
                'Tackles Won', 'Interceptions', 'Blocks', 'Ball Recoveries', 'Carries', 'Progressive Carries'
            ])
        elif pos == 'DF':
            stats.update([
                'Clearances', 'Blocks', 'Interceptions', 'Tackles Won', 'Aerials Won',
                'Ball Recoveries', 'Errors Leading to Shot',
                'Passes Completed (Short)', 'Passes Completed (Medium)', 'Passes Completed (Long)',
                'Progressive Passes', 'Tackles in Defensive Third', 'Dribblers Tackled',
                'Shots Blocked', 'Passes Blocked'
            ])
    return list(stats)

def get_goalkeeper_stats():
    return [
        'Goals Against', 'Saves', 'Save Efficiency', 'Completed Long Passes',
        'Crosses Stopped', 'Defensive Actions Outside Penalty Area'
    ]

# --- Streamlit page configuration ---
st.set_page_config(page_title="Top Match Stats")

# --- Load all file paths ---
path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", "csv24_25"))
paths = {
    "games": os.path.join(path_folder, "leagues_games", "{}_games.csv"),
    "clean_players": os.path.join(path_folder, "clean", "data_players.csv"),
    "clean_goals": os.path.join(path_folder, "clean", "data_goals.csv"),
    "ratings_players": os.path.join(path_folder, "ratings", "data_players.csv"),
    "ratings_goals": os.path.join(path_folder, "ratings", "data_goals.csv"),
}

# --- Load datasets ---
df_players = pd.read_csv(paths["clean_players"])
df_goals = pd.read_csv(paths["clean_goals"])
df_notes_players = pd.read_csv(paths["ratings_players"])
df_notes_goals = pd.read_csv(paths["ratings_goals"])

# --- Combine player & goalkeeper data ---
df_goals["Position"] = "GK"
df_all = pd.concat([df_players, df_goals], ignore_index=True)
df_notes = pd.concat([df_notes_players, df_notes_goals], ignore_index=True)

# --- Merge with ratings ---
df = df_all.merge(df_notes, on=["Player", "Game Week", "Team", "League", "Minutes", "Position"], how="left")

# --- Sidebar selections ---
st.sidebar.title("Select Parameters")
positions = st.sidebar.multiselect("Position", df_all["Position"].unique())

# --- Filter stats by position ---
if set(positions) == {"GK"}:
    stats_list = get_goalkeeper_stats()
    df = df[df["Position"] == "GK"]
else:
    stats_list = get_player_stats(positions)
    df = df[df["Position"].isin(positions)]

# --- Select stat and number of top players ---
stat = st.sidebar.selectbox("Statistic to display", sorted(stats_list))
n = st.sidebar.slider("Number of top performances to display", 5, 100, 20)

# --- Filter leagues ---
leagues = sorted(df["League"].dropna().unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = leagues if all_leagues else [st.sidebar.selectbox("Choose a league", leagues)]

df = df[df["League"].isin(selected_leagues)]
if stat and stat in df.columns:
    df = df[df[stat].notna()]

# --- Load games by league ---
games = {}
for lg in df["League"].unique():
    try:
        games[lg] = pd.read_csv(paths["games"].format(lg))
    except FileNotFoundError:
        continue

# --- Get opponent and score for each match ---
def get_opponent_score(row):
    lg, gw, team = row["League"], row["Game Week"], row["Team"]
    match_df = games.get(lg)
    if match_df is None:
        return pd.Series(["Unknown", "N/A"])

    match = match_df[match_df["Game Week"] == gw]
    for _, m in match.iterrows():
        if m["Home Team"] == team:
            return pd.Series([m["Away Team"], m["Score"]])
        elif m["Away Team"] == team:
            return pd.Series([m["Home Team"], m["Score"]])
    return pd.Series(["Unknown", "N/A"])

# --- Main display ---
st.title("📈 Top Individual Performances")

if positions and stat and selected_leagues:
    df[["Opponent", "Score"]] = df.apply(get_opponent_score, axis=1)
    df = df[df[stat].notna() & df["Score"].notna()]
    df_top = df.sort_values(by=stat, ascending=False).head(n)

    df_display = df_top[[
        "Player", stat, "Rating", "Score", "Team", "Opponent",
        "League", "Game Week", "Minutes"
    ]].rename(columns={
        stat: "Value",
        "Team": "Club",
        "Game Week": "Game Week",
        "Minutes": "Minutes Played"
    })

    st.dataframe(df_display.set_index("Player"), use_container_width=True)