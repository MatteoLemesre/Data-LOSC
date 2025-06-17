import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

path_folder = ""

def get_features_for_players(positions):
    features = set()
    for pos in positions:
        if pos == 'FW':
            features.update([
                'Goals',
                'Expected Goals (xG)',
                'Shots on Target',
                'Shot-Creating Actions (SCA)',
                'Goal-Creating Actions (GCA)',
                'Expected Assists (xA)',
                'Key Passes',
                'Passes into Final Third',
                'Progressive Passes',
                'Successful Take-Ons',
                'Dribbles Challenged',
                'Fouls Drawn',
                'Touches in Attacking Third'
            ])
        elif pos == 'MO':
            features.update([
                'Goals',
                'Expected Goals (xG)',
                'Expected Assists (xA)',
                'Key Passes',
                'Passes into Final Third',
                'Passes into Penalty Area',
                'Progressive Passes',
                'Through Balls',
                'Switches',
                'Successful Take-Ons',
                'Dribbles Challenged',
                'Fouls Drawn',
                'Touches in Attacking Third',
                'Touches'
            ])
        elif pos == 'MF':
            features.update([
                'Passes Completed',
                'Progressive Passes',
                'Interceptions',
                'Tackles Won',
                'Blocks',
                'Ball Recoveries',
                'Errors Leading to Shot',
                'Fouls Committed',
                'Fouls Drawn',
                'Yellow Cards',
                'Touches in Middle Third'
            ])
        elif pos == 'DF':
            features.update([
                'Clearances',
                'Blocks',
                'Interceptions',
                'Tackles',
                'Tackles Won',
                'Aerials Won',
                'Aerials Lost',
                'Errors Leading to Shot',
                'Fouls Committed',
                'Yellow Cards',
                'Touches'
            ])
    return list(features)


def get_features_for_goalkeepers():
    return [
        'Goals Against',
        'Saves',
        'Save Efficiency',
        'Clean Sheets',
        'Completed Long Passes',
        'Crosses Stopped',
        'Defensive Actions Outside Penalty Area',
    ]

def get_features(positions):
    if 'GK' in positions:
        return get_features_for_goalkeepers()
    else:
        return get_features_for_players(positions)


def get_df(positions):
    if 'GK' in positions:
        df_radar = pd.read_csv(os.path.join(path_folder, "csv/centiles/data_goals_centiles.csv"))
    else:
        df_radar = pd.read_csv(os.path.join(path_folder, "csv/centiles/data_players_centiles.csv"))
    df_radar.rename(columns={df_radar.columns[0]: "Player"}, inplace=True)
    return df_radar

def get_average_scores(position):
    if 'GK' in position:
        df_scores = pd.read_csv(os.path.join(path_folder, "csv/notes/data_goals.csv"))
    else:
        df_scores = pd.read_csv(os.path.join(path_folder, "csv/notes/data_players.csv"))

    df_scores = df_scores.dropna(subset=['Rate', 'Minutes'])
    df_scores['Rate'] = pd.to_numeric(df_scores['Rate'], errors='coerce')
    df_scores['Minutes'] = pd.to_numeric(df_scores['Minutes'], errors='coerce')

    df_scores = df_scores[df_scores['Minutes'] > 0]

    avg_simple = df_scores.groupby('Player')['Rate'].mean().reset_index()
    avg_simple.rename(columns={'Rate': 'Average Rating'}, inplace=True)

    return avg_simple

st.set_page_config(page_title="Individual Performances")
st.sidebar.title("Select Parameters")

df_scores_1 = pd.read_csv(os.path.join(path_folder, "csv/notes/data_players.csv"))
df_scores_2 = pd.read_csv(os.path.join(path_folder, "csv/notes/data_goals.csv"))
df_scores = pd.concat([df_scores_1, df_scores_2], ignore_index=True)

positions = st.sidebar.multiselect("Positions", df_scores['Position'].unique())

df_radar = get_df(positions) if positions else pd.DataFrame()
selected_features = get_features(positions) if positions else []

if positions:
    if 'GK' in positions:
        selected_players = st.sidebar.multiselect("Players", df_radar['Player'].unique())
        df_global = pd.read_csv(os.path.join(path_folder, "csv/centiles/data_goals_aggregated.csv"))
        df_global = df_global[df_global['Matches'] > 0].copy()
    else:
        filtered_players = df_radar[df_radar['Position'].isin(positions)]
        selected_players = st.sidebar.multiselect("Players", filtered_players['Player'].unique())
        df_global = pd.read_csv(os.path.join(path_folder, "csv/centiles/data_players_aggregated.csv"))
        df_global = df_global[df_global['Matches'] > 0].copy()
else:
    selected_players = []

st.title("⚽ Individual Performances")
st.subheader("📋 Global Player Statistics")

if selected_players:
    df_global = df_global[df_global['Player'].isin(selected_players)]

    df_averages = get_average_scores(positions)
    df_global = df_global.merge(df_averages, on='Player', how='left')

    if 'GK' in positions:
        df_display = df_global[['Player', 'Average Rating', 'Matches', 'Minutes', 'Goals Against', 'Clean Sheets']].copy()
    else:
        df_display = df_global[['Player', 'Average Rating', 'Matches', 'Minutes', 'Goals', 'Assists', 'Yellow Cards', 'Red Cards']].copy()

    df_display = df_display.set_index("Player").sort_values("Average Rating", ascending=False).round(2)
    st.dataframe(df_display, use_container_width=True)


st.subheader("📌 Player Radar Statistics")

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

if selected_players and selected_features:
    plot_radar(df_radar, selected_features, selected_players)
    df_selected = df_radar[df_radar["Player"].isin(selected_players)][["Player"] + selected_features].set_index("Player")

st.subheader("📈 Player Percentiles")

if selected_players and selected_features:
    st.dataframe(df_selected.T)
