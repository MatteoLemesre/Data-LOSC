import streamlit as st
import pandas as pd
import os

# ---------------------- Utility Functions ----------------------
def get_player_stats():
    return [
        "Goals", "Assists", "Shots Total", "Shots on Target",
        "Expected Goals (xG)", "Non-Penalty Expected Goals (npxG)",
        "Shot-Creating Actions (SCA)", "Goal-Creating Actions (GCA)",
        "Key Passes", "Passes into Final Third", "Passes into Penalty Area",
        "Crosses into Penalty Area", "Crosses", "Expected Assists (xA)",
        "Expected Assisted Goals (xAG)", "Passes Completed", 
        "Progressive Passes", "Through Balls", "Switches", 
        "Passes Offside",  "Passes Completed (Short)", 
        "Passes Completed (Medium)", "Passes Completed (Long)",
        "Carries", "Progressive Carries", "Carries into Final Third",
        "Carries into Penalty Area", "Successful Take-Ons", 
        "Tackles Won", "Dribblers Tackled", "Interceptions", 
        "Clearances", "Errors Leading to Shot", 
        "Touches", "Touches in Defensive Penalty Area", "Touches in Defensive Third",
        "Touches in Middle Third", "Touches in Attacking Third",
        "Touches in Attacking Penalty Area", "Live-Ball Touches",
        "Fouls Drawn", "Offsides", "Own Goals", "Aerials Won"
    ]

def get_goalkeeper_stats():
    return [
        "Goals Against", "Saves", "Save Efficiency", "Completed Long Passes",
        "Crosses Stopped", "Defensive Actions Outside Penalty Area"
    ]

def get_opponent_score(row):
    league = row["League"]
    gameweek = row["Game Week"]
    team = row["Team"]
    match_df = games.get(league)
    
    if match_df is None:
        return pd.Series(["Unknown", "N/A"])

    match = match_df[match_df["Game Week"] == gameweek]
    for _, m in match.iterrows():
        if m["Home Team"] == team:
            return pd.Series([m["Away Team"], m["Score"]])
        elif m["Away Team"] == team:
            return pd.Series([m["Home Team"], m["Score"]])
    
    return pd.Series(["Unknown", "N/A"])

# ---------------------- Streamlit Config ----------------------
st.set_page_config(page_title="Top Match Stats")
st.title("📈 Top Individual Performances")
st.sidebar.title("Select Parameters")

# ---------------------- Season Selection ----------------------
selected_season = st.sidebar.selectbox("Season", ["2024 2025", "2025 2026"], index=0)
season_code = None
if selected_season == "2024 2025":
    season_code = "24_25"
elif selected_season == "2025 2026":
    season_code = "25_26"

path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))

# ---------------------- File Paths ----------------------
paths = {
    "games": os.path.join(path_folder, "leagues_games", "{}_games.csv"),
    "clean_players": os.path.join(path_folder, "clean", "data_players.csv"),
    "clean_goals": os.path.join(path_folder, "clean", "data_goals.csv"),
    "ratings_players": os.path.join(path_folder, "ratings", "data_players.csv"),
    "ratings_goals": os.path.join(path_folder, "ratings", "data_goals.csv"),
}

# ---------------------- Load Data ----------------------
df_players = pd.read_csv(paths["clean_players"])
df_goalkeepers = pd.read_csv(paths["clean_goals"])
df_ratings_players = pd.read_csv(paths["ratings_players"])
df_ratings_goalkeepers = pd.read_csv(paths["ratings_goals"])

df_goalkeepers["Position"] = "GK"
df_all = pd.concat([df_players, df_goalkeepers], ignore_index=True)
df_ratings = pd.concat([df_ratings_players, df_ratings_goalkeepers], ignore_index=True)

df = df_all.merge(
    df_ratings,
    on=["Player", "Game Week", "Team", "League", "Minutes", "Position"],
    how="left"
)

# ---------------------- Sidebar Filters ----------------------
positions = st.sidebar.multiselect("Position", df_all["Position"].unique())
if not positions:
    st.stop()

if set(positions) == {"GK"}:
    stats_list = get_goalkeeper_stats()
    df = df[df["Position"] == "GK"]
else:
    stats_list = get_player_stats()
    df = df[df["Position"].isin(positions)]

stat = st.sidebar.selectbox("Statistic to display", sorted(stats_list))
top_n = st.sidebar.slider("Number of top performances to display", 5, 100, 20)

leagues = sorted(df["League"].dropna().unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = leagues if all_leagues else [st.sidebar.selectbox("Choose a league", leagues)]

df = df[df["League"].isin(selected_leagues)]
if stat and stat in df.columns:
    df = df[df[stat].notna()]

# ---------------------- Load Game Data (per league) ----------------------
games = {}
for lg in df["League"].unique():
    try:
        games[lg] = pd.read_csv(paths["games"].format(lg))
    except FileNotFoundError:
        continue

# ---------------------- Data Processing ----------------------
if positions and stat and selected_leagues:
    df[["Opponent", "Score"]] = df.apply(get_opponent_score, axis=1)

    df = df[df[stat].notna() & df["Score"].notna()]

    df_top = df.sort_values(by=stat, ascending=False).head(top_n)

    df_display = df_top[[
        "Player", stat, "Rating", "Minutes", "Score", "Team", "Opponent",
        "League", "Game Week"
    ]].rename(columns={
        stat: stat,
        "Team": "Club",
        "Game Week": "Game Week",
        "Minutes": "Minutes Played"
    })

    # ---------------------- Display ----------------------
    st.dataframe(df_display.set_index("Player"), use_container_width=True)