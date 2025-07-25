import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ------------------------- Functions -------------------------
def get_features_for_players(positions):
    features = set()
    for pos in positions:
        if pos in ['FW', 'MO']:
            features.update([
                'Goals', 'Efficiency', '% Take-Ons', 'Actions created',
                'Expected Assists (xA)', "Actions in the Penalty Area", 'Key Passes',
                '% Aerial Duels', 'Progressive Actions (Total)', 'Successful Take-Ons'
            ])
        elif pos == 'MF':
            features.update([
                'Progressive Actions (Total)', 'Interceptions', 'Tackles Won',
                'Blocks', 'Ball Recoveries', 'Key Passes',
                'Fouls Committed', '% Tackles/Duels', 'Touches Middle Third', '% Aerial Duels'
            ])
        elif pos == 'DF':
            features.update([
                'Clearances', 'Blocks', 'Interceptions', '% Aerial Duels',
                'Touches', 'Fouls Committed', 'Aerial Duels Won',
                'Progressive Passes', 'Ball Recoveries', '% Tackles/Duels'
            ])
    return list(features)

def get_features_for_goalkeepers():
    return [
        'Clean Sheets', 'Crosses Stopped', 'Sweeper Actions', 'Saves',
        'Goals Against', 'Efficiency', 'Penalties Winner', '% Saves', '% Long Passes', 
        '% Crosses Stopped'
    ]

def get_features(positions):
    if 'GK' in positions:
        return get_features_for_goalkeepers()
    else:
        return get_features_for_players(positions)

def get_df(leagues_name, path_folder, positions):
    try:
        file_suffix = "_centiles_gk.csv" if 'GK' in positions else "_centiles.csv"
        df_path = os.path.join(path_folder, f"centiles/{leagues_name}{file_suffix}")
        df_radar = pd.read_csv(df_path)
        df_radar.rename(columns={df_radar.columns[0]: "Player"}, inplace=True)
        return df_radar
    except FileNotFoundError:
        st.error(f"Data file for league '{leagues_name}' not found in folder '{path_folder}'. Please check your selections and data.")
        return pd.DataFrame()
    
import os
import pandas as pd

def get_average_scores(positions, path_folder):
    if 'GK' in positions:
        path = os.path.join(path_folder, "ratings/data_goals.csv")
    else:
        path = os.path.join(path_folder, "ratings/data_players.csv")

    df = pd.read_csv(path)
    
    df = df.dropna(subset=['Rating', 'Minutes'])
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    df['Minutes'] = pd.to_numeric(df['Minutes'], errors='coerce')
    df = df[df['Minutes'] > 0]

    df['WeightedRating'] = df['Rating'] * df['Minutes']
    grouped = df.groupby('Player').agg({
        'WeightedRating': 'sum',
        'Minutes': 'sum',
        'Team': lambda x: ', '.join(sorted(set(x))),
        'League': lambda x: ', '.join(sorted(set(x)))
    }).reset_index()

    grouped['Average Rating'] = grouped['WeightedRating'] / grouped['Minutes']
    grouped.rename(columns={'Team': 'Team(s)', 'League': 'League(s)'}, inplace=True)
    return grouped[['Player', 'Average Rating', 'Team(s)', 'League(s)']]


def plot_radar(players_data, features, players):
    if len(features) < 3:
        st.warning("Please select at least 3 features for a proper radar chart display.")
        return

    angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})

    for player in players:
        values = players_data.loc[players_data["Player"] == player, features].values.flatten().tolist()
        if len(values) != len(features):
            st.warning(f"Not enough data for player {player} to plot radar.")
            continue
        values += values[:1]
        ax.plot(angles, values, label=player, linewidth=2)
        ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(features, fontsize=10)
    ax.set_yticklabels([])
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    st.pyplot(fig)

# ------------------------- Streamlit App -------------------------
st.set_page_config(page_title="Individual Player Performances")
st.sidebar.title("Select Parameters")

st.title("Individual Player Performances")
st.markdown("""This page allows you to explore individual player performances from various leagues.  

- Select one or more players from the **Big 5 Leagues, UCL, UEL, or UECL** to view detailed stats, including a **percentile radar chart** based on their position and **average match rating**.  
- You can also choose players from **Other Leagues** such as the Argentine Primera, Brazilian Série A, Dutch Eredivisie, MLS, Portuguese Primeira Liga, Copa Libertadores, English Championship, Italian Serie B, Liga MX, and Belgian Pro League. For players from these other leagues, only the performance stats will be shown — **no match rating is available**.
""")

selected_season = st.sidebar.selectbox("Season", ["2025-2026", "2024-2025", "2023-2024"], index=1)

season = None
if selected_season == "2023-2024":
    season_code = "23_24"
elif selected_season == "2024-2025":
    season_code = "24_25"
elif selected_season == "2025-2026":
    season_code = "25_26"

if season_code:
    path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", f"csv{season_code}"))
    
    df_scores_players = pd.read_csv(os.path.join(path_folder, "ratings/data_players.csv"))
    df_scores_goalkeepers = pd.read_csv(os.path.join(path_folder, "ratings/data_goals.csv"))
    df_scores = pd.concat([df_scores_players, df_scores_goalkeepers], ignore_index=True)

    selected_leagues = st.sidebar.multiselect("League Group", ["Big 5 + UCL + UEL + UECL", "Others Leagues"])
    leagues_name = ""

    if selected_leagues:
        if "Big 5 + UCL + UEL + UECL" in selected_leagues:
            leagues_name = "TopLeagues"
        elif "Others Leagues" in selected_leagues:
            leagues_name = "OthersLeagues"

    if leagues_name:
        positions = st.sidebar.multiselect("Position", df_scores['Position'].unique())

        if positions:
            df_radar = get_df(leagues_name, path_folder, positions)
            if df_radar.empty:
                st.stop()

            selected_features = get_features(positions)

            file_name = f"{leagues_name}_aggregated_gk.csv" if 'GK' in positions else f"{leagues_name}_aggregated.csv"
            df_global_path = os.path.join(path_folder, f"centiles/{file_name}")
            df_global = pd.read_csv(df_global_path)
            df_global = df_global[df_global['Matches Played'] > 0].copy()

            filtered_players = df_radar[df_radar['Position'].isin(positions)]
            players_all = filtered_players['Player'].unique().tolist()

            selected_players = st.sidebar.multiselect("Players", players_all)

            if selected_players:
                df_global = df_global[df_global['Player'].isin(selected_players)]
                
                show_ratings = leagues_name == "TopLeagues"
                
                nationality_map = (
                        df_radar[["Player", "Nation"]]
                        .drop_duplicates("Player")
                        .set_index("Player")["Nation"]
                    )               

                if leagues_name == "TopLeagues":
                    df_global["Nation"] = df_global["Player"].map(nationality_map)
                else:
                    df_global["Nation"] = df_global["Player"].map(nationality_map)
                df_global["Nation"] = df_global["Nation"].astype(str).str.split(" ").str[1]
                
                if show_ratings:
                    df_global_agg = df_global.groupby('Player', as_index=False).sum()
                    df_averages = get_average_scores(positions, path_folder)
                    df_global = df_global.merge(df_averages, on='Player', how='left')

                    if 'GK' in positions:
                        columns = ['Player', 'Average Rating', 'Age', 'Nation', 'Matches Played', 'Minutes Played', 'Goals Against', 'Clean Sheets', 'Team(s)', 'League(s)']
                    else:
                        columns = ['Player', 'Average Rating', 'Age', 'Nation', 'Matches Played', 'Minutes Played', 'Goals', 'Assists', 'Yellow Cards', 'Red Cards', 'Team(s)', 'League(s)']

                    st.subheader("📋 Global Player Statistics")
                    df_display = df_global[columns].set_index('Player').sort_values('Average Rating', ascending=False).round(2)
                    st.dataframe(df_display, use_container_width=True)
                else:
                    df_global_agg = df_global.groupby('Player', as_index=False).sum()

                    if 'GK' in positions:
                        columns = ['Player', 'Age', 'Nation', 'Matches Played', 'Minutes Played', 'Goals Against', 'Clean Sheets', 'Team']
                    else:
                        columns = ['Player', 'Age', 'Nation', 'Matches Played', 'Minutes Played', 'Goals', 'Assists', 'Yellow Cards', 'Red Cards', 'Team']

                    df_global_agg["Age"] = df_global_agg["Age"].astype(str).str.split("-").str[0].astype(int)
                    df_display = df_global_agg[columns].set_index('Player').round(2)
                    df_display = df_display.rename(columns={"Team": "Team(s)"})
                    st.dataframe(df_display, use_container_width=True)

                st.subheader("📌 Player Radar Statistics")
                if selected_players and selected_features:
                    plot_radar(df_radar, selected_features, selected_players)
                    df_selected = df_radar[df_radar["Player"].isin(selected_players)][["Player"] + selected_features].set_index("Player")
                    st.subheader("📈 Player Percentiles")
                    st.dataframe(df_selected.T)

                    st.subheader("🧮 Adjusted Stats + Percentiles (All Features)")
                    for player in selected_players:
                        file_name = f"{leagues_name}_adjusted_gk.csv" if 'GK' in positions else f"{leagues_name}_adjusted.csv"
                        df_adj_path = os.path.join(path_folder, f"centiles/{file_name}")
                        df_adj = pd.read_csv(df_adj_path)
                        stats_absolute = df_adj[df_adj["Player"] == player].copy()
                        stats_percentiles = df_radar[df_radar["Player"] == player].copy()

                        common_stats = [col for col in stats_percentiles.columns if col in stats_absolute.columns and col not in ['Player', 'Position']]
                        deleted_stats = ['Matches Played', 'Minutes Played', 'Age', 'Nation', 'Born', 'Squad', 'Team(s)', 'Starts']

                        valid_stats = []
                        for stat in common_stats:
                            if stat not in deleted_stats:
                                if not (stats_absolute[stat].isnull().all() or stats_absolute[stat].sum() == 0):
                                    valid_stats.append(stat)

                        df_combined = pd.DataFrame({
                            "Stat": valid_stats,
                            "Per 90 min or Percentage": [stats_absolute[stat].values[0] for stat in valid_stats],
                            "Percentile": [stats_percentiles[stat].values[0] for stat in valid_stats]
                        }).set_index("Stat")

                        st.markdown(f"### 🔎 {player}")
                        st.dataframe(df_combined.sort_index(), use_container_width=True)