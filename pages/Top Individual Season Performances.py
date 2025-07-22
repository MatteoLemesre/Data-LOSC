import streamlit as st
import pandas as pd
import os

# ----------------------- Stats ------------------------
def get_player_stats():
    return [
        "Goals", "Expected Goals (xG)", "Shots", "Shots on Target", 
        "Penalties Scored", "Penalties Attempted",
        "Key Passes", "Actions created", "Actions in the Penalty Area",
        "Expected Assisted Goals (xA)", 
        "Passes Completed (Total)", "Passes Attempted (Total)",
        "Passes Completed (Short)", "Passes Attempted (Short)", 
        "Passes Completed (Medium)", "Passes Attempted (Medium)",
        "Passes Completed (Long)", "Passes Attempted (Long)", 
        "Passes into Final Third", "Passes into Penalty Area", 
        "Crosses into Penalty Area", "Progressive Passes", 
        "Progressive Passes Received", "Passes Received",
        "Carries", "Progressive Carries", "Progressive Runs",
        "Carries into Final Third", "Carries into Penalty Area",
        "Successful Take-Ons", "Take-Ons Attempted",
        "Tackles", "Tackles Won", "Tackles Defensive Third", 
        "Tackles Middle Third", "Tackles Attacking Third", 
        "Challenges Tackled", "Challenges Attempted", "Challenges Lost", 
        "Interceptions", "Clearances", "Blocks", 
        "Errors", "Touches", "Touches Defensive Penalty Area", "Touches Defensive Third", 
        "Touches Middle Third", "Touches Attacking Third", 
        "Touches Attacking Penalty Area", "Live-Ball Touches",
        "Yellow Cards", "Red Cards", "Second Yellow Cards",
        "Fouls Committed", "Fouls Drawn", "Penalties Won", 
        "Penalties Conceded", "Own Goals", 
        "Aerial Duels Won", "Aerial Duels Lost", "Total Aerial Duels", 
        "Total Duels won", "Ball Recoveries", "Ball Losses", 
        "Efficiency", "Progressive Actions (Total)",
        "% Aerial Duels", "% Passes (Total)", "% Passes (Short)",
        "% Passes (Medium)", "% Passes (Long)", "% Tackles/Duels", 
        "% Take-Ons"
    ]

def get_goalkeeper_stats():
    return [
        "Goals Against", "Saves", 
        "Post-Shot Expected Goals (PSxG)", "Clean Sheets", "Penaltys Winner",
        "Passes Attempted (GK)", "Launched Passes Attempted", 
        "Launched Passes Completed", "Completed Long Passes", 
        "Through Balls", "Crosses Stopped", 
        "Sweeper Actions", "Defensive Actions Outside Penalty Area",
        "Efficiency", "% Saves", "% Long Passes", 
        "% Crosses Stopped"
    ]

# ----------------------- Streamlit UI ------------------------

st.set_page_config(page_title="Top Individual Season Performances")
st.title("📈 Top Individual Season Performances")
st.markdown("""
Explore the **top Individual Season Performances** across all leagues and positions.

- Start by selecting a **season** and one or several **positions**.
- Then choose a **statistic** (e.g. assists, interceptions, saves) to rank players by.
- You can filter results by **minimum minutes played** and adjust whether stats are shown as **totals** or **per 90 minutes**.
- You can also choose players from Other Leagues such as the Argentine Primera, Brazilian Série A, Dutch Eredivisie, MLS, Portuguese Primeira Liga, Copa Libertadores, English Championship, Italian Serie B, Liga MX, and Belgian Pro League.
- **Note:** Percentage-based statistics are **not available per 90 minutes**, which may result in missing or inconsistent values when that option is selected.
""")

# ----------------------- Sidebar ------------------------

st.sidebar.title("Select Parameters")

selected_season = st.sidebar.selectbox("Season", ["2025 2026", "2024 2025", "2023 2024"], index=1)

season = None
if selected_season == "2023 2024":
    season_code = "23_24"
elif selected_season == "2024 2025":
    season_code = "24_25"
elif selected_season == "2025 2026":
    season_code = "25_26"

league_group = st.sidebar.selectbox("League Group", ["Big 5 + UCL + UEL + UECL", "Others Leagues"])
leagues_name = "TopLeagues" if league_group == "Big 5 + UCL + UEL + UECL" else "OthersLeagues"

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

df_filtered = df_all[(df_all["Position"].isin(positions)) & (df_all[stat].notna())].copy()

if not per_90:
    df_filtered = df_filtered[df_filtered["Minutes Played"] >= min_minutes]
    df_grouped = df_filtered.groupby("Player", as_index=False).agg({stat: "sum", "Minutes Played": "sum"})
    df_grouped[stat] = round(df_grouped[stat], 2)
else:
    df_filtered["RawStat"] = df_filtered[stat] * df_filtered["Minutes Played"] / 90
    df_grouped = df_filtered.groupby("Player", as_index=False).agg({
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
    df_final = df_grouped.merge(df_rating, on="Player", how="left") \
                     .merge(df_club, on="Player", how="left") \
                     .merge(df_league, on="Player", how="left")
else:
    df_rating = pd.DataFrame(columns=["Player", "Average Rating"])
    df_aggregated_players = pd.read_csv(paths["aggregated_players"])
    df_aggregated_gk = pd.read_csv(paths["aggregated_gk"])
    df_aggregated_gk["Position"] = "GK"
    df_aggregated_all = pd.concat([df_aggregated_players, df_aggregated_gk], ignore_index=True)
    df_club = df_aggregated_all[["Player", "Team"]].drop_duplicates()
    df_final = df_grouped.merge(df_rating, on="Player", how="left") \
                     .merge(df_club, on="Player", how="left")

df_final = df_final.sort_values(by=stat, ascending=False).head(n)

# ----------------------- Display ------------------------

if leagues_name == "TopLeagues":
    df_display = df_final.rename(columns={
        "Team": "Team(s)", "League": "League(s)", "Minutes": "Minutes Played"
    })[["Player", stat, "Average Rating", "Minutes Played", "Team(s)", "League(s)"]]
else:
    df_display = df_final.rename(columns={
        "Team": "Team(s)", "Minutes": "Minutes Played"
    })[["Player", stat, "Minutes Played", "Team(s)"]]

st.dataframe(df_display.set_index("Player"), use_container_width=True)
