import streamlit as st
import pandas as pd
import os

# ----------------------- Stats ------------------------
def get_player_stats():
    return [
        "Goals", "Shots on Target", 
        "Penalties Scored",
        "Key Passes", "Actions created", "Actions in the Penalty Area",
        "Expected Assisted Goals (xA)", 
        "Passes Completed (Total)", 
        "Passes Completed (Short)",  
        "Passes Completed (Medium)", 
        "Passes Completed (Long)",
        "Passes into Final Third", "Passes into Penalty Area", 
        "Crosses into Penalty Area", "Progressive Passes", 
        "Progressive Passes Received",
        "Progressive Carries", "Progressive Runs",
        "Carries into Final Third", "Carries into Penalty Area",
        "Successful Take-Ons", "Tackles Won", "Tackles Defensive Third", 
        "Challenges Tackled", 
        "Interceptions", "Clearances", "Blocks", 
        "Errors", "Touches", "Touches Attacking Third", 
        "Touches Attacking Penalty Area",
        "Yellow Cards", "Red Cards", "Second Yellow Cards",
        "Fouls Committed", "Fouls Drawn", "Penalties Won", 
        "Penalties Conceded", "Own Goals", 
        "Aerial Duels Won", "Total Aerial Duels", 
        "Total Duels won", "Ball Recoveries", "Ball Losses", 
        "Efficiency", "Progressive Actions (Total)",
        "% Aerial Duels", "% Passes (Total)", "% Passes (Short)",
        "% Passes (Medium)", "% Passes (Long)", "% Tackles/Duels", 
        "% Take-Ons"
    ]

def get_goalkeeper_stats():
    return [
        "Goals Against", "Saves", "Clean Sheets", "Penalties Winner" 
        "Launched Passes Completed", "Completed Long Passes", 
        "Through Balls", "Crosses Stopped", 
        "Sweeper Actions", "Defensive Actions Outside Penalty Area",
        "Efficiency", "% Saves", "% Long Passes", 
        "% Crosses Stopped"
    ]

# ----------------------- Streamlit UI ------------------------

st.set_page_config(page_title="Top Individual Season Performances")
st.title("Top Individual Season Performances")
st.markdown("""Explore the **top Individual Season Performances** across all leagues and positions.

- Start by selecting a **season** and one or several **positions**.
- Then choose a **statistic** (e.g. assists, interceptions, saves) to rank players by.
- You can filter results by **minimum minutes played** and adjust whether stats are shown as **totals** or **per 90 minutes**.
- You can also choose players from Other Leagues such as the Argentine Primera, Brazilian Série A, Dutch Eredivisie, MLS, Portuguese Primeira Liga, Copa Libertadores, English Championship, Italian Serie B, Liga MX, and Belgian Pro League.
- **Note:** Percentage-based statistics are **only available on a per-90-minute basis**, which may lead to missing or inconsistent values when another option is selected.
""")

# ----------------------- Sidebar ------------------------

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
    "adjusted_players": os.path.join(base_path, "centiles", f"{leagues_name}_adjusted.csv"),
    "adjusted_gk": os.path.join(base_path, "centiles", f"{leagues_name}_adjusted_gk.csv"),
    "aggregated_players": os.path.join(base_path, "centiles", f"{leagues_name}_aggregated.csv"),
    "aggregated_gk": os.path.join(base_path, "centiles", f"{leagues_name}_aggregated_gk.csv"),
    "ratings_players": os.path.join(base_path, "ratings", "data_players.csv"),
    "ratings_gk": os.path.join(base_path, "ratings", "data_goals.csv")
}

per_90 = st.sidebar.checkbox("Per 90 min?", value=True)

# ----------------------- Load Data ------------------------

if per_90:
    df_players = pd.read_csv(paths["adjusted_players"])
    df_gk = pd.read_csv(paths["adjusted_gk"])
else:
    df_players = pd.read_csv(paths["aggregated_players"])
    df_gk = pd.read_csv(paths["aggregated_gk"])

df_gk["Position"] = "GK"
df_all = pd.concat([df_players, df_gk], ignore_index=True)

if leagues_name == "TopLeagues":
    df_notes = pd.concat([
        pd.read_csv(paths["ratings_players"]),
        pd.read_csv(paths["ratings_gk"])
    ], ignore_index=True)
else:
    df_notes = pd.DataFrame(columns=["Player", "Rating", "Squad"])

# ----------------------- Filters ------------------------

positions = st.sidebar.multiselect("Position", sorted(df_all["Position"].unique()))
if not positions:
    st.stop()

is_only_gk = set(positions) == {"GK"}
stats_list = get_goalkeeper_stats() if is_only_gk else get_player_stats()
stat = st.sidebar.selectbox("Statistic to display", sorted(stats_list))
n = st.sidebar.slider("Number of top players to display", 5, 100, 30)
min_minutes = st.sidebar.slider("Minimum minutes played", 0, 4000, 2000)
age_max = st.sidebar.slider("Maximum age", 0, 50, 50)  

df_filtered = df_all[(df_all["Position"].isin(positions)) & (df_all[stat].notna())].copy()
df_top = df_filtered.copy()
df_top["Age"] = df_top["Age"].astype(str).str.split("-").str[0].astype(int)
df_top = df_top[df_top["Age"] <= age_max]

if not per_90:
    df_top = df_top[df_top["Minutes Played"] >= min_minutes]
    df_grouped = df_top.groupby("Player", as_index=False).agg({stat: "sum", "Minutes Played": "sum", "Age": "first"})
    df_grouped[stat] = round(df_grouped[stat], 2)
else:
    df_top["RawStat"] = df_top[stat]
    df_grouped = df_top.groupby("Player", as_index=False).agg({
        "RawStat": "sum", "Minutes Played": "sum"
    })
    df_grouped[stat] = round((df_grouped["RawStat"] / df_grouped["Minutes Played"]) * 90, 2)
    df_grouped.drop(columns=["RawStat"], inplace=True)

df_grouped = df_grouped[df_grouped["Minutes Played"] >= min_minutes]

# ----------------------- Join Data ------------------------

if not df_notes.empty:
    df_rating = df_notes.groupby("Player", as_index=False)["Rating"].mean().rename(columns={"Rating": "Average Rating"})
    df_rating["Average Rating"] = df_rating["Average Rating"].round(2)
    df_club = df_notes.groupby("Player")["Team"].agg(lambda x: ", ".join(sorted(set(x)))).reset_index()
    df_league = df_notes.groupby("Player")["League"].agg(lambda x: ", ".join(sorted(set(x)))).reset_index()
    df_total = df_grouped.merge(df_rating, on="Player", how="left") \
                            .merge(df_club, on="Player", how="left") \
                            .merge(df_all, on="Player", how="left") \
                            .merge(df_league, on="Player", how="left")
else:
    df_rating = pd.DataFrame(columns=["Player", "Average Rating"])
    df_aggregated_players = pd.read_csv(paths["aggregated_players"])
    df_aggregated_gk = pd.read_csv(paths["aggregated_gk"])
    df_aggregated_gk["Position"] = "GK"
    df_aggregated_all = pd.concat([df_aggregated_players, df_aggregated_gk], ignore_index=True)
    df_club = df_aggregated_all[["Player", "Team"]].drop_duplicates()
    df_total = df_grouped.merge(df_rating, on="Player", how="left") \
                            .merge(df_club, on="Player", how="left") \
                            .merge(df_all, on="Player", how="left")
                        
cols_x = [col for col in df_total.columns if col.endswith('_x')]
rename_dict = {col: col.replace('_x', '') for col in cols_x}
df_total = df_total.rename(columns=rename_dict)
df_total = df_total.drop(columns=[col for col in df_total.columns if '_y' in col or '_x' in col], errors='ignore')
df_total = df_total.sort_values(by=stat, ascending=False).head(n)

# ----------------------- Display ------------------------

if leagues_name == "TopLeagues":
    df_display = df_total.rename(columns={
        "Team": "Team(s)", "League": "League(s)", "Minutes": "Minutes Played"
    })[["Player", "Age", stat, "Average Rating", "Minutes Played", "Team(s)", "League(s)"]]
else:
    df_display = df_total.rename(columns={
        "Team": "Team(s)", "Minutes": "Minutes Played"
    })[["Player", "Age", stat, "Minutes Played", "Team(s)"]]

st.dataframe(df_display.set_index("Player"), use_container_width=True)
