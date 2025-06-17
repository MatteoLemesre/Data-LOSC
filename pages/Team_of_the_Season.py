import streamlit as st
import pandas as pd
import os
import re

DATA_PATH = "csv"
NOTES_PLAYERS_PATH = os.path.join(DATA_PATH, "notes", "data_players.csv")
NOTES_GOALS_PATH = os.path.join(DATA_PATH, "notes", "data_goals.csv")
AGG_PLAYERS_PATH = os.path.join(DATA_PATH, "centiles", "data_players_aggregated.csv")
AGG_GOALS_PATH = os.path.join(DATA_PATH, "centiles", "data_goals_aggregated.csv")

df_players = pd.read_csv(NOTES_PLAYERS_PATH)
df_goalkeepers = pd.read_csv(NOTES_GOALS_PATH)
df_total = pd.concat([df_players, df_goalkeepers], ignore_index=True)
df_total.dropna(subset=["Rate"], inplace=True)

def extract_matchday_num(j):
    match = re.match(r"J(\d+)", str(j))
    return int(match.group(1)) if match else -1

available_matchdays = sorted(
    df_total["Game Week"].dropna().unique(),
    key=lambda x: extract_matchday_num(x)
)
st.set_page_config(page_title="Team of the Season")
st.sidebar.title("Select Parameters")

available_leagues = sorted(df_total["League"].unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = available_leagues if all_leagues else [st.sidebar.selectbox("Choose a league", available_leagues)]

all_matchdays = st.sidebar.checkbox("All matchdays", value=True)
selected_matchdays = available_matchdays if all_matchdays else [st.sidebar.selectbox("Choose a matchday", available_matchdays)]

num_players = st.sidebar.slider("Number of players to display", min_value=5, max_value=100, value=40)
min_matches = st.sidebar.slider("Minimum matches played", min_value=1, max_value=50, value=25)
min_minutes_percentage = st.sidebar.slider("Minimum percentage of minutes played", min_value=0, max_value=100, value=70)

df_filtered = df_total[
    (df_total["League"].isin(selected_leagues)) &
    (df_total["Game Week"].isin(selected_matchdays))
]

df_grouped = df_filtered.groupby("Player", as_index=False).agg({
    "Rate": "mean"
}).rename(columns={"Rate": "Average Rating"})

clubs_per_player = df_total.groupby("Player")["Team"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
leagues_per_player = df_total.groupby("Player")["League"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()

df_grouped = df_grouped.merge(clubs_per_player, on="Player", how="left")
df_grouped = df_grouped.merge(leagues_per_player, on="Player", how="left")

df_agg_players = pd.read_csv(AGG_PLAYERS_PATH)[["Player", "Minutes", "Matches"]]
df_agg_goalkeepers = pd.read_csv(AGG_GOALS_PATH)[["Player", "Minutes", "Matches"]]
df_agg_total = pd.concat([df_agg_players, df_agg_goalkeepers], ignore_index=True)

df_agg_total = df_agg_total.groupby("Player", as_index=False).agg({
    "Minutes": "sum",
    "Matches": "sum"
})

df_grouped = df_grouped.merge(df_agg_total, on="Player", how="left")

df_grouped["% Minutes Played"] = 100 * df_grouped["Minutes"] / (df_grouped["Matches"] * 90)
df_grouped["% Minutes Played"] = df_grouped["% Minutes Played"].round(1)

df_grouped = df_grouped[
    (df_grouped["Matches"] >= min_matches) &
    (df_grouped["% Minutes Played"] >= min_minutes_percentage)
]

df_grouped["Average Rating"] = df_grouped["Average Rating"].round(2)

df_result = df_grouped.sort_values(by="Average Rating", ascending=False).head(num_players)

st.title("📊 Top Players")

df_result.set_index("Player", inplace=True)

st.dataframe(
    df_result[[
        "Average Rating", "Matches", "Minutes", "% Minutes Played", "Team", "League"
    ]].rename(columns={
        "Team": "Club(s)",
        "League": "League(s)"
    }),
    use_container_width=True
)
