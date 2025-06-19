import streamlit as st
import pandas as pd
import os
import re

# --- Define file paths ---
path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", "csv24_25"))
ratings_players_path = os.path.join(path_folder, "ratings", "data_players.csv")
ratings_goalkeepers_path = os.path.join(path_folder, "ratings", "data_goals.csv")
agg_players_path = os.path.join(path_folder, "centiles", "data_players_aggregated.csv")
agg_goalkeepers_path = os.path.join(path_folder, "centiles", "data_goals_aggregated.csv")

# --- Load ratings ---
df_players = pd.read_csv(ratings_players_path)
df_goalkeepers = pd.read_csv(ratings_goalkeepers_path)
df_all = pd.concat([df_players, df_goalkeepers], ignore_index=True)
df_all.dropna(subset=["Rating"], inplace=True)

# --- Matchday sorting helper ---
def extract_matchday_num(j):
    match = re.match(r"J(\d+)", str(j))
    return int(match.group(1)) if match else -1

matchdays = sorted(df_all["Game Week"].dropna().unique(), key=extract_matchday_num)

# --- Streamlit config ---
st.set_page_config(page_title="Team of the Season")
st.sidebar.title("Select Parameters")

# --- Sidebar filters ---
leagues = sorted(df_all["League"].unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = leagues if all_leagues else [st.sidebar.selectbox("Choose a league", leagues)]

all_matchdays = st.sidebar.checkbox("All matchdays", value=True)
selected_matchdays = matchdays if all_matchdays else [st.sidebar.selectbox("Choose a matchday", matchdays)]

top_n = st.sidebar.slider("Number of players to display", 5, 100, 40)
min_matches = st.sidebar.slider("Minimum matches played", 1, 50, 25)
min_minutes_pct = st.sidebar.slider("Minimum percentage of minutes played", 0, 100, 70)

# --- Filter rating data by league and matchday ---
df_filtered = df_all[
    (df_all["League"].isin(selected_leagues)) &
    (df_all["Game Week"].isin(selected_matchdays))
]

# --- Compute average ratings ---
df_avg = df_filtered.groupby("Player", as_index=False)["Rating"].mean().rename(columns={"Rating": "Average Rating"})

# --- Add club and league info ---
if all_leagues or len(selected_leagues) > 1:
    clubs = df_all.groupby("Player")["Team"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
    leagues_info = df_all.groupby("Player")["League"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
else:
    filtered_df = df_all[df_all["League"] == selected_leagues[0]]
    clubs = filtered_df.groupby("Player")["Team"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
    leagues_info = filtered_df.groupby("Player")["League"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()

df_avg = df_avg.merge(clubs, on="Player", how="left").merge(leagues_info, on="Player", how="left")

# --- Load aggregated minutes/matches data ---
df_minutes = pd.read_csv(agg_players_path)
df_minutes_gk = pd.read_csv(agg_goalkeepers_path)
df_minutes_total = pd.concat([df_minutes, df_minutes_gk], ignore_index=True)

# --- Filter minutes/matches by league if needed ---
if not all_leagues:
    df_minutes_total = df_minutes_total[df_minutes_total["League"].isin(selected_leagues)]

# --- Aggregate total minutes and matches per player ---
df_minutes_total = df_minutes_total.groupby("Player", as_index=False)[["Minutes", "Matches"]].sum()

# --- Merge with average ratings ---
df_avg = df_avg.merge(df_minutes_total, on="Player", how="left")

# --- Compute % of minutes played ---
df_avg["% Minutes Played"] = 100 * df_avg["Minutes"] / (df_avg["Matches"] * 90)
df_avg["% Minutes Played"] = df_avg["% Minutes Played"].round(1)

# --- Apply filters: participation thresholds ---
df_avg = df_avg[
    (df_avg["Matches"] >= min_matches) &
    (df_avg["% Minutes Played"] >= min_minutes_pct)
]

# --- Sort, round, select top N ---
df_avg["Average Rating"] = df_avg["Average Rating"].round(2)
df_top = df_avg.sort_values(by="Average Rating", ascending=False).head(top_n)

# --- Display table ---
st.title("📊 Top Players")
df_top.set_index("Player", inplace=True)

if all_leagues or len(selected_leagues) > 1:
    cols_to_display = ["Average Rating", "Matches", "Minutes", "% Minutes Played", "Team", "League"]
    rename_cols = {"Team": "Club(s)", "League": "League(s)"}
else:
    cols_to_display = ["Average Rating", "Matches", "Minutes", "% Minutes Played", "Team"]
    rename_cols = {"Team": "Club(s)"}

st.dataframe(
    df_top[cols_to_display].rename(columns=rename_cols),
    use_container_width=True
)


