import streamlit as st
import pandas as pd
import os

# --- Stat definitions based on player type ---
def get_player_stats():
    return ["Goals", "Assists", "Shots Total", "Shots on Target",
            "Expected Goals (xG)", "Non-Penalty Expected Goals (npxG)",
            "Shot-Creating Actions (SCA)", "Goal-Creating Actions (GCA)",
            "Key Passes", "Passes into Final Third", "Passes into Penalty Area",
            "Crosses into Penalty Area", "Crosses", "Expected Assists (xA)",
            "Expected Assisted Goals (xAG)", "Passes Completed",
            "Progressive Passes", "Through Balls", "Switches",
            "Passes Offside",  "Passes Completed (Short)",
            "Passes Completed (Medium)", "Passes Completed (Long)", "Carries", "Progressive Carries",
            "Carries into Final Third", "Carries into Penalty Area", "Successful Take-Ons",
            "Tackles Won", "Dribblers Tackled", "Interceptions",
            "Clearances", "Errors Leading to Shot",
            "Touches", "Touches in Defensive Penalty Area", "Touches in Defensive Third",
            "Touches in Middle Third", "Touches in Attacking Third",
            "Touches in Attacking Penalty Area", "Live-Ball Touches", "Fouls Drawn", "Offsides", "Own Goals",
            "Aerials Won"]

def get_goalkeeper_stats():
    return [
        'Goals Against', 'Saves', 'Save Efficiency', 'Completed Long Passes',
        'Crosses Stopped', 'Defensive Actions Outside Penalty Area'
    ]

# --- Config ---
st.set_page_config(page_title="Top Match Stats")
st.title("📈 Top Individual Performances")

# --- Paths ---
path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", "csv24_25"))
paths = {
    "centiles_players": os.path.join(path_folder, "centiles", "data_players_adjusted.csv"),
    "centiles_goals": os.path.join(path_folder, "centiles", "data_goals_adjusted.csv"),
    "centiles_players_2": os.path.join(path_folder, "centiles", "data_players_aggregated.csv"),
    "centiles_goals_2": os.path.join(path_folder, "centiles", "data_goals_aggregated.csv"),
    "ratings_players": os.path.join(path_folder, "ratings", "data_players.csv"),
    "ratings_goals": os.path.join(path_folder, "ratings", "data_goals.csv"),
}

# --- Sidebar selections ---
st.sidebar.title("Select Parameters")
per_90 = st.sidebar.checkbox("Per 90 min?", value=True)

# Load datasets depending on per_90 mode
if per_90:
    df_players = pd.read_csv(paths["centiles_players"])
    df_goals = pd.read_csv(paths["centiles_goals"])
else:
    df_players = pd.read_csv(paths["centiles_players_2"])
    df_goals = pd.read_csv(paths["centiles_goals_2"])

df_goals["Position"] = "GK"
df_all = pd.concat([df_players, df_goals], ignore_index=True)

df_notes_players = pd.read_csv(paths["ratings_players"])
df_notes_goals = pd.read_csv(paths["ratings_goals"])
df_notes = pd.concat([df_notes_players, df_notes_goals], ignore_index=True)

# --- League selection ---
leagues = sorted(df_all["League"].dropna().unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = leagues if all_leagues else [st.sidebar.selectbox("Choose a league", leagues)]

# --- Position selection ---
positions = st.sidebar.multiselect("Position", df_all["Position"].unique())
if not positions:
    st.stop()

# --- Stat selection ---
stats_list = get_goalkeeper_stats() if set(positions) == {"GK"} else get_player_stats()
stat = st.sidebar.selectbox("Statistic to display", sorted(stats_list))
n = st.sidebar.slider("Number of top players to display", 5, 100, 20)
min_minutes = st.sidebar.slider("Minimum minutes played", 0, 3000, 1500)

# --- Filter by position + selected leagues ---
df_filtered = df_all[
    (df_all["Position"].isin(positions)) &
    (df_all["League"].isin(selected_leagues)) &
    (df_all[stat].notna())
].copy()

# --- Per-90 handling (convert to raw values before aggregation) ---
if per_90:
    df_filtered["RawStat"] = df_filtered[stat] * df_filtered["Minutes"] / 90
    df_grouped = df_filtered.groupby("Player", as_index=False).agg({
        "RawStat": "sum",
        "Minutes": "sum"
    })
    df_grouped[stat] = round((df_grouped["RawStat"] / df_grouped["Minutes"]) * 90, 2)
    df_grouped.drop(columns=["RawStat"], inplace=True)
else:
    df_grouped = df_filtered.groupby("Player", as_index=False).agg({
        stat: "sum",
        "Minutes": "sum"
    })

# --- Apply minimum minutes filter AFTER aggregation ---
df_grouped = df_grouped[df_grouped["Minutes"] >= min_minutes]

# --- Ratings / Clubs / Leagues ---
df_notes_filtered = df_notes[df_notes["League"].isin(selected_leagues)]

df_avg_rating = df_notes_filtered.groupby("Player", as_index=False)["Rating"].mean().rename(columns={"Rating": "Average Rating"})
df_avg_rating["Average Rating"] = df_avg_rating["Average Rating"].round(2)

df_club = df_notes_filtered.groupby("Player")["Team"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
df_league = df_notes_filtered.groupby("Player")["League"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()

df_final = df_grouped.merge(df_avg_rating, on="Player", how="left") \
                     .merge(df_club, on="Player", how="left") \
                     .merge(df_league, on="Player", how="left")

# --- Sort and prepare display ---
df_final = df_final.sort_values(by=stat, ascending=False).head(n)

if all_leagues or len(selected_leagues) > 1:
    df_display = df_final[["Player", stat, "Average Rating", "Minutes", "Team", "League"]].rename(columns={
        stat: stat,
        "Team": "Club(s)",
        "League": "League(s)",
        "Minutes": "Minutes Played"
    })
else:
    def get_club(row):
        clubs = row["Team"].split(", ")
        leagues_ = row["League"].split(", ")
        for c, l in zip(clubs, leagues_):
            if l == selected_leagues[0]:
                return c
        return clubs[0]

    df_final["Team"] = df_final.apply(get_club, axis=1)
    df_display = df_final[["Player", stat, "Average Rating", "Minutes", "Team"]].rename(columns={
        stat: stat,
        "Team": "Club(s)",
        "Minutes": "Minutes Played"
    })

# --- Display table ---
st.dataframe(df_display.set_index("Player"), use_container_width=True)

