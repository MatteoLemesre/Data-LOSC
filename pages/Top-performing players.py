import streamlit as st
import pandas as pd
import os
import re

# ------------------------- Functions -------------------------
def extract_matchday_num(j):
    match = re.match(r"J(\d+)", str(j))
    return int(match.group(1)) if match else -1

def new_poste(df_all):
    main_positions = (
        df_all.groupby("Player")["Position"]
        .agg(lambda x: x.mode().iloc[0])
        .reset_index()
        .rename(columns={"Position": "Main Position"})
    )
    df_all = df_all.merge(main_positions, on="Player", how="left")
    df_all["Position"] = df_all["Main Position"]
    df_all.drop(columns=["Main Position"], inplace=True)
    return df_all

def enrich_with_team_league_age(df_ratings, df_all, df_centiles, leagues, all_leagues):
    if all_leagues or len(leagues) > 1:
        clubs = df_all.groupby("Player")["Team"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
        leagues_info = df_all.groupby("Player")["League"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
    else:
        filtered = df_all[df_all["League"] == leagues[0]]
        clubs = filtered.groupby("Player")["Team"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
        leagues_info = filtered.groupby("Player")["League"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()

    age_df = df_centiles[["Player", "Age"]].drop_duplicates()
    age_df["Age"] = age_df["Age"].astype(str).str.split("-").str[0].astype(int)

    return (
        df_ratings.merge(clubs, on="Player", how="left")
                  .merge(leagues_info, on="Player", how="left")
                  .merge(age_df, on="Player", how="left")
    )

# ------------------------- Streamlit App -------------------------
st.set_page_config(page_title="Top-Performing Players")
st.sidebar.title("Select Parameters")

selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=1)

season = None
if selected_season == "2023-2024":
    season_code = "23_24"
elif selected_season == "2024-2025":
    season_code = "24_25"
elif selected_season == "2025-2026":
    season_code = "25_26"

path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))

ratings_players_path = os.path.join(path_folder, "ratings", "data_players.csv")
ratings_goalkeepers_path = os.path.join(path_folder, "ratings", "data_goals.csv")
agg_players_path = os.path.join(path_folder, "centiles", "TopLeagues_aggregated.csv")
agg_goalkeepers_path = os.path.join(path_folder, "centiles", "TopLeagues_aggregated_gk.csv")

df_players = pd.read_csv(ratings_players_path)
df_goalkeepers = pd.read_csv(ratings_goalkeepers_path)
df_all = pd.concat([df_players, df_goalkeepers], ignore_index=True)
df_all.dropna(subset=["Rating"], inplace=True)

df_centiles_players = pd.read_csv(agg_players_path)
df_centiles_gk = pd.read_csv(agg_goalkeepers_path)
df_centiles_gk["Position"] = "GK"
df_centiles = pd.concat([df_centiles_players, df_centiles_gk], ignore_index=True)
df_centiles["Nation"] = df_centiles["Nation"].astype(str).str.split(" ").str[1]

positions = sorted(df_all["Position"].unique())
all_positions = st.sidebar.checkbox("All positions", value=True)
selected_positions = positions if all_positions else [st.sidebar.selectbox("Choose a position", positions)]

leagues = sorted(df_all["League"].unique())
all_leagues = st.sidebar.checkbox("All leagues", value=True)
selected_leagues = leagues if all_leagues else [st.sidebar.selectbox("Choose a league", leagues)]

matchdays = sorted(df_all["Game Week"].dropna().unique(), key=extract_matchday_num)
all_matchdays = st.sidebar.checkbox("All matchdays", value=True)
selected_matchdays = matchdays if all_matchdays else [st.sidebar.selectbox("Choose a matchday", matchdays)]

top_n = st.sidebar.slider("Number of players to display", 5, 100, 30)
min_matches = st.sidebar.slider("Minimum matches played", 1, 50, 25)
age_max = st.sidebar.slider("Maximum age", 15, 50, 50)

df_all = new_poste(df_all)

df_filtered = df_all[
    (df_all["League"].isin(selected_leagues)) &
    (df_all["Game Week"].isin(selected_matchdays)) &
    (df_all["Position"].isin(selected_positions))
]

df_avg = df_filtered.groupby(["Player", "Position"], as_index=False)["Rating"].mean().rename(columns={"Rating": "Average Rating"})

df_avg = enrich_with_team_league_age(df_avg, df_all, df_centiles, selected_leagues, all_leagues)

df_minutes_total = (
    df_filtered
    .groupby("Player", as_index=False)
    .agg(
        **{
            "Minutes Played": ("Minutes", "sum"),
            "Matches Played": ("Minutes", "count")
        }
    )
)
df_avg = df_avg.merge(
    df_minutes_total.drop_duplicates(subset="Player"),
    on="Player",
    how="left"
)

df_avg = df_avg.merge(
    df_centiles.drop_duplicates(subset="Player"),
    on="Player",
    how="left"
)

cols_x = [col for col in df_avg.columns if col.endswith('_x')]
rename_dict = {col: col.replace('_x', '') for col in cols_x}
df_avg = df_avg.rename(columns=rename_dict)
df_avg = df_avg.drop(columns=[col for col in df_avg.columns if '_y' in col or '_x' in col], errors='ignore')

df_avg = df_avg[(df_avg["Matches Played"] >= min_matches) & (df_avg["Age"] <= age_max)]
df_avg["Average Rating"] = df_avg["Average Rating"].round(2)

df_top = df_avg.sort_values(by="Average Rating", ascending=False).head(top_n)
df_top.set_index("Player", inplace=True)

st.title("Top-Performing Players")
st.markdown("""
This page displays the **top-performing players** based on their average match ratings.

- You can filter by **league**, **position**, **matchday**, and **age**.
- Only players with a minimum number of matches are shown.
- Ratings come from a custom algorithm and are subjective.
""")

if all_leagues or len(selected_leagues) > 1:
    cols_to_display = ["Average Rating", "Age", "Nation", "Matches Played", "Minutes Played", "Team", "League"]
    rename_cols = {"Team": "Team(s)", "League": "League(s)"}
else:
    cols_to_display = ["Average Rating", "Age", "Nation", "Matches Played", "Minutes Played", "Team"]
    rename_cols = {"Team": "Team(s)"}

st.dataframe(
    df_top[cols_to_display].rename(columns=rename_cols),
    use_container_width=True
)