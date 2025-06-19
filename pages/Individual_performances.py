import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Paths ---
path_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "csv", "csv24_25"))

# --- Functions to get features by position ---
def get_features_for_players(positions):
    features = set()
    for pos in positions:
        if pos == 'FW':
            features.update([
                'Goals', 'Passes into Penalty Area', 'Shots on Target', 'Shot-Creating Actions (SCA)', 
                'Goal-Creating Actions (GCA)', 'Expected Assists (xA)', 'Key Passes', 
                'Passes Completed', 'Progressive Passes', 'Successful Take-Ons'
            ])
        elif pos == 'MF':
            features.update([
                'Passes Completed', 'Progressive Passes', 'Interceptions', 'Tackles Won', 
                'Blocks', 'Ball Recoveries', 'Key Passes', 
                'Fouls Committed', 'Fouls Drawn', 'Touches in Middle Third'
            ])
        elif pos == 'DF':
            features.update([
                'Clearances', 'Blocks', 'Interceptions', 'Tackles Won', 'Aerials Won', 
                'Touches', 'Fouls Committed', 'Passes Completed', 
                'Progressive Passes', 'Ball Recoveries'
            ])
    return list(features)

def get_features_for_goalkeepers():
    return ['Goals Against', 'Saves', 'Save Efficiency', 'Clean Sheets', 'Completed Long Passes', 'Crosses Stopped', 
            'Defensive Actions Outside Penalty Area']

def get_features(positions):
    if 'GK' in positions:
        return get_features_for_goalkeepers()
    else:
        return get_features_for_players(positions)

# --- Load radar dataframe depending on position ---
def get_df(positions):
    if 'GK' in positions:
        df_radar = pd.read_csv(os.path.join(path_folder, "centiles/data_goals_centiles.csv"))
    else:
        df_radar = pd.read_csv(os.path.join(path_folder, "centiles/data_players_centiles.csv"))
    df_radar.rename(columns={df_radar.columns[0]: "Player"}, inplace=True)
    return df_radar

# --- Compute average ratings for given positions ---
def get_average_scores(positions):
    if 'GK' in positions:
        df_scores = pd.read_csv(os.path.join(path_folder, "ratings/data_goals.csv"))
    else:
        df_scores = pd.read_csv(os.path.join(path_folder, "ratings/data_players.csv"))

    df_scores = df_scores.dropna(subset=['Rating', 'Minutes'])
    df_scores['Rating'] = pd.to_numeric(df_scores['Rating'], errors='coerce')
    df_scores['Minutes'] = pd.to_numeric(df_scores['Minutes'], errors='coerce')
    df_scores = df_scores[df_scores['Minutes'] > 0]

    avg_simple = df_scores.groupby('Player')['Rating'].mean().reset_index()
    avg_simple.rename(columns={'Rating': 'Average Rating'}, inplace=True)

    return avg_simple

# --- Streamlit setup ---
st.set_page_config(page_title="Individual Performances")
st.sidebar.title("Select Parameters")

# --- Load combined scores ---
df_scores_players = pd.read_csv(os.path.join(path_folder, "ratings/data_players.csv"))
df_scores_goalkeepers = pd.read_csv(os.path.join(path_folder, "ratings/data_goals.csv"))
df_scores = pd.concat([df_scores_players, df_scores_goalkeepers], ignore_index=True)

# --- Position selection ---
positions = st.sidebar.multiselect("Positions", df_scores['Position'].unique())
df_radar = get_df(positions) if positions else pd.DataFrame()
selected_features = get_features(positions) if positions else []

# --- Player selection depending on position ---
if positions:
    if 'GK' in positions:
        selected_players = st.sidebar.multiselect("Players", df_radar['Player'].unique())
        df_global = pd.read_csv(os.path.join(path_folder, "centiles/data_goals_aggregated.csv"))
    else:
        filtered_players = df_radar[df_radar['Position'].isin(positions)]
        selected_players = st.sidebar.multiselect("Players", filtered_players['Player'].unique())
        df_global = pd.read_csv(os.path.join(path_folder, "centiles/data_players_aggregated.csv"))
    df_global = df_global[df_global['Matches'] > 0].copy()
else:
    selected_players = []

# --- Title and subtitle ---
st.title("⚽ Individual Performances")
st.subheader("📋 Global Player Statistics")

# --- Display global stats for selected players ---
if selected_players:
    df_global = df_global[df_global['Player'].isin(selected_players)]

    df_global = df_global.groupby('Player', as_index=False).sum()

    df_averages = get_average_scores(positions)
    df_global = df_global.merge(df_averages, on='Player', how='left')

    if df_global.empty:
        st.warning("Aucune donnée disponible pour les joueurs sélectionnés.")
    else:
        if 'GK' in positions:
            cols_to_show = ['Player', 'Average Rating', 'Matches', 'Minutes', 'Goals Against', 'Clean Sheets']
        else:
            cols_to_show = ['Player', 'Average Rating', 'Matches', 'Minutes', 'Goals', 'Assists', 'Yellow Cards', 'Red Cards']

        df_display = df_global[cols_to_show].set_index('Player').sort_values('Average Rating', ascending=False).round(2)
        st.dataframe(df_display, use_container_width=True)

# --- Radar plot function ---
def plot_radar(players_data, features, players):
    if len(features) < 3:
        st.warning("Please select at least 3 features for a proper display.")
        return

    angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})

    for player in players:
        values = players_data.loc[players_data["Player"] == player, features].values.flatten().tolist()
        values += values[:1]
        ax.plot(angles, values, label=player, linewidth=2)
        ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(features, fontsize=10)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    st.pyplot(fig)

# --- Display radar chart and percentiles ---
st.subheader("📌 Player Radar Statistics")

if selected_players and selected_features:
    plot_radar(df_radar, selected_features, selected_players)
    df_selected = df_radar[df_radar["Player"].isin(selected_players)][["Player"] + selected_features].set_index("Player")
    
    st.subheader("📈 Player Percentiles")
    st.dataframe(df_selected.T)
