import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ------------------------- Functions -------------------------
def get_features():
    return [
        'Goals', 'Efficiency', 'Actions created', 'Actions in the Penalty Area', '% Aerial Duels',
        'Aerial Duels Won', 'Possession', 'Clean Sheets', 'Goals Against', 'Efficiency GK'
    ]

def load_centile_data(leagues_name, path_folder):
    path = os.path.join(path_folder, f"teams/{leagues_name}_centiles.csv")
    return pd.read_csv(path)

def load_adjusted_data(leagues_name, path_folder):
    path = os.path.join(path_folder, f"teams/{leagues_name}_adjusted.csv")
    return pd.read_csv(path)

def load_aggregated_data(leagues_name, path_folder):
    path = os.path.join(path_folder, f"teams/{leagues_name}_aggregated.csv")
    return pd.read_csv(path)

def plot_team_radar(df, features, selected_teams):
    angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})

    for team in selected_teams:
        values = df.loc[df["Team"] == team, features].values.flatten().tolist()
        values += values[:1]
        ax.plot(angles, values, label=team, linewidth=2)
        ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(features, fontsize=10)
    ax.set_yticklabels([])
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    st.pyplot(fig)

# ------------------------- Streamlit App -------------------------
st.set_page_config(page_title="Team Performances")
st.title("Team Performances")
st.markdown("""This page allows you to explore **team-level performances** from various leagues.  

- Select one or more teams from the **Big 5 Leagues, UCL, UEL, or UECL** to view detailed stats, including a **percentile radar chart**.  
- You can also view team stats from **Other Leagues** such as the Argentine Primera, Brazilian Série A, Dutch Eredivisie, MLS, Portuguese Primeira Liga, Copa Libertadores, English Championship, Italian Serie B, Liga MX, and Belgian Pro League.
""")

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

selected_leagues = st.sidebar.multiselect("League Group", ["Big 5 + UCL + UEL + UECL", "Others Leagues"])
leagues_name = "TopLeagues" if "Big 5 + UCL + UEL + UECL" in selected_leagues else "OthersLeagues" if "Others Leagues" in selected_leagues else None

if leagues_name:
    try:
        df_centiles = load_centile_data(leagues_name, path_folder)
        df_adjusted = load_adjusted_data(leagues_name, path_folder)
        df_agg = load_aggregated_data(leagues_name, path_folder)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    df_centiles = df_centiles[df_centiles['Matches Played'] > 0].copy()
    df_adjusted = df_adjusted[df_adjusted['Matches Played'] > 0].copy()
    df_agg = df_agg[df_agg['Matches Played'] > 0].copy()

    teams = df_centiles['Team'].unique().tolist()
    selected_teams = st.sidebar.multiselect("Select Teams", teams)

    selected_features = get_features()

    if selected_teams:
        st.subheader("📋 Global Team Stats")
        basic_cols = ['Team', 'Average Age', 'Matches Played', 'Goals', 'Goals Against', 'Clean Sheets', 'Yellow Cards', 'Red Cards']
        df_global = df_agg[df_agg['Team'].isin(selected_teams)].copy()
        st.dataframe(df_global[basic_cols].set_index("Team").round(2), use_container_width=True)

        if selected_features:
            st.subheader("📌 Radar Chart")
            plot_team_radar(df_centiles, selected_features, selected_teams)

            st.subheader("📈 Percentiles of Radar Stats")
            df_radar_percentiles = df_centiles[df_centiles['Team'].isin(selected_teams)][["Team"] + selected_features]
            st.dataframe(df_radar_percentiles.set_index("Team").T)

        st.subheader("🧮 Adjusted Stats + Percentiles")
        for team in selected_teams:
            df_abs = df_adjusted[df_adjusted["Team"] == team]
            df_pct = df_centiles[df_centiles["Team"] == team]

            common_stats = [col for col in df_pct.columns if col in df_abs.columns and col not in ['Team', 'Matches Played']]
            deleted = ['Age', 'Nation', 'Yellow Cards', 'Red Cards'] 
            valid_stats = [stat for stat in common_stats if stat not in deleted]

            df_combined = pd.DataFrame({
                "Stat": valid_stats,
                "Per 90 min or Percentage": [df_abs[stat].values[0] for stat in valid_stats],
                "Percentile": [df_pct[stat].values[0] for stat in valid_stats]
            }).set_index("Stat")

            st.markdown(f"### 🔎 {team}")
            st.dataframe(df_combined.sort_index(), use_container_width=True)
