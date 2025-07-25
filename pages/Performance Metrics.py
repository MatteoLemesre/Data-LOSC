import streamlit as st
import pandas as pd
import os

# ---------------- Stats ----------------
def get_player_stats():
    return ["Offensive Index", "Passing Index", "Possession Index", "Defensive Index"]

def get_goalkeeper_stats():
    return ["Line Index", "Passes Index"]

st.set_page_config(page_title="Performance Metrics")
st.title("Performance Metrics")
st.markdown("""This page lets you explore **performance indices** across various leagues, positions, and metrics.

- You can filter by **league category**, **player position**, **age**, and **performance metric** to highlight the profiles you’re interested in.
- The index values are shown on a **percentile scale** to allow fair comparisons across players.
- The **indices are computed using a custom algorithm** that is regularly improved and updated based on new data.
- These metrics aim to offer a consistent view of player performance, tailored to their role and playing time.
""")



# ---------------- Sidebar progressive filters ----------------
st.sidebar.title("Select Parameters")

selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=1)

season = None
if selected_season == "2023-2024":
    season_code = "23_24"
elif selected_season == "2024-2025":
    season_code = "24_25"
elif selected_season == "2025-2026":
    season_code = "25_26"

league_group = st.sidebar.multiselect("League Group", ["Big 5 + UCL + UEL + UECL", "Others Leagues"])
if not league_group:
    st.stop()
else:
    if "Big 5 + UCL + UEL + UECL" in league_group:
        leagues_name = "TopLeagues"
    elif "Others Leagues" in league_group:
        leagues_name = "OthersLeagues"
    else:
        st.stop()

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))
paths = {
    "metrics_players": os.path.join(base_path, "metrics", f"{leagues_name}_metrics.csv"),
    "metrics_gk": os.path.join(base_path, "metrics", f"{leagues_name}_metrics_gk.csv"),
    "aggregated_players": os.path.join(base_path, "centiles", f"{leagues_name}_aggregated.csv"),
    "aggregated_gk": os.path.join(base_path, "centiles", f"{leagues_name}_aggregated_gk.csv"),
    "ratings_players": os.path.join(base_path, "ratings", "data_players.csv"),
    "ratings_gk": os.path.join(base_path, "ratings", "data_goals.csv")
}

df_players = pd.read_csv(paths["metrics_players"])
df_gk = pd.read_csv(paths["metrics_gk"])
df_gk["Position"] = "GK"
df_all = pd.concat([df_players, df_gk], ignore_index=True)

if leagues_name == "TopLeagues":
    df_notes = pd.concat([
        pd.read_csv(paths["ratings_players"]),
        pd.read_csv(paths["ratings_gk"])
    ], ignore_index=True)
else:
    df_notes = pd.DataFrame(columns=["Player", "Rating", "Team", "League"])

positions = st.sidebar.multiselect("Position", sorted(df_all["Position"].unique()))
if not positions:
    st.stop()

is_only_gk = set(positions) == {"GK"}
stats_list = get_goalkeeper_stats() if is_only_gk else get_player_stats()
stat = st.sidebar.selectbox("Statistic to display", sorted(stats_list))
if not stat:
    st.stop()

n = st.sidebar.slider("Number of top players to display", 5, 100, 30)
min_minutes = st.sidebar.slider("Minimum minutes played", 0, 4000, 2000)
age_max = st.sidebar.slider("Maximum age", 15, 50, 50)

df_filtered = df_all[(df_all["Position"].isin(positions)) & (df_all[stat].notna())].copy()
df_filtered = df_filtered[df_filtered["Minutes Played"] >= min_minutes]
df_filtered["Age"] = df_filtered["Age"].astype(str).str.split("-").str[0].astype(int)
df_filtered = df_filtered[df_filtered["Age"] <= age_max]

df_grouped = df_filtered[["Player", stat, "Minutes Played", "Age", "Nation"]].copy()

if not df_notes.empty:
    df_rating = df_notes.groupby("Player", as_index=False)["Rating"].mean().rename(columns={"Rating": "Average Rating"})
    df_rating["Average Rating"] = df_rating["Average Rating"].round(2)

    df_club = df_notes.groupby("Player")["Team"].agg(lambda x: ", ".join(sorted(set(x)))).reset_index()
    df_league = df_notes.groupby("Player")["League"].agg(lambda x: ", ".join(sorted(set(x)))).reset_index()

    df_final = df_grouped.merge(df_rating, on="Player", how="left") \
                         .merge(df_club, on="Player", how="left") \
                         .merge(df_league, on="Player", how="left")
else:
    df_rating = pd.DataFrame(columns=["Player"])
    df_aggregated_players = pd.read_csv(paths["aggregated_players"])
    df_aggregated_gk = pd.read_csv(paths["aggregated_gk"])
    df_aggregated_gk["Position"] = "GK"
    df_aggregated_all = pd.concat([df_aggregated_players, df_aggregated_gk], ignore_index=True)
    df_club = df_aggregated_all[["Player", "Team"]].drop_duplicates()

    df_final = df_grouped.merge(df_rating, on="Player", how="left") \
                         .merge(df_club, on="Player", how="left")

df_final = df_final.sort_values(by=stat, ascending=False).head(n)

columns_to_display = ["Player", stat, "Age", "Nation", "Minutes Played"]
if "Average Rating" in df_final.columns:
    columns_to_display = ["Player", stat, "Average Rating", "Age", "Nation", "Minutes Played"]
if "Team" in df_final.columns:
    df_final.rename(columns={"Team": "Team(s)"}, inplace=True)
    columns_to_display.append("Team(s)")
if "League" in df_final.columns:
    df_final.rename(columns={"League": "League(s)"}, inplace=True)
    columns_to_display.append("League(s)")

df_display = df_final[columns_to_display]
df_display["Nation"] = df_display["Nation"].astype(str).str.split(" ").str[1]
st.dataframe(df_display.set_index("Player"), use_container_width=True)

