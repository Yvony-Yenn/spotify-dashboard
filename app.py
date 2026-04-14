import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spotify Tracks Explorer",
    page_icon="🎵",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f0f0f; }
    .block-container { padding-top: 2rem; }
    h1 { color: #1DB954; font-size: 2.2rem !important; }
    h2, h3 { color: #ffffff; }
    .stMetric label { color: #b3b3b3 !important; font-size: 0.85rem !important; }
    .stMetric value { color: #1DB954 !important; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1DB954;
        margin: 1.5rem 0 0.5rem 0;
        border-bottom: 1px solid #282828;
        padding-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("spotify-tracks-dataset.csv")
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    df = df.dropna(subset=["popularity", "track_genre"])
    df["duration_min"] = (df["duration_ms"] / 60000).round(2)
    return df

df = load_data()

AUDIO_FEATURES = {
    "Danceability": "danceability",
    "Energy": "energy",
    "Valence (Positivity)": "valence",
    "Acousticness": "acousticness",
    "Speechiness": "speechiness",
    "Instrumentalness": "instrumentalness",
    "Liveness": "liveness",
    "Tempo": "tempo",
}

ALL_GENRES = sorted(df["track_genre"].unique().tolist())

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🎵 Spotify Tracks Explorer")
st.markdown(
    "**What makes a Spotify track popular?** "
    "Explore how audio features relate to popularity across genres."
)
st.divider()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filters")

    selected_genres = st.multiselect(
        "Genres",
        options=ALL_GENRES,
        default=["pop", "hip-hop", "rock", "jazz", "classical"],
        help="Select one or more genres to explore",
    )

    pop_range = st.slider(
        "Popularity range",
        min_value=0, max_value=100,
        value=(20, 100),
        help="Filter tracks by popularity score (0–100)",
    )

    x_feature_label = st.selectbox(
        "X-axis feature (scatter plot)",
        options=list(AUDIO_FEATURES.keys()),
        index=0,
    )

    y_feature_label = st.selectbox(
        "Y-axis feature (scatter plot)",
        options=list(AUDIO_FEATURES.keys()),
        index=1,
    )

    sample_size = st.slider(
        "Max points on scatter plot",
        min_value=200, max_value=3000, value=1000, step=100,
        help="Reduce if the chart feels slow",
    )

    st.divider()
    st.markdown("**Data source:** [Spotify Tracks Dataset – Kaggle](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)")

# ── Filter data ────────────────────────────────────────────────────────────────
if not selected_genres:
    st.warning("Please select at least one genre from the sidebar.")
    st.stop()

filtered = df[
    df["track_genre"].isin(selected_genres) &
    df["popularity"].between(pop_range[0], pop_range[1])
].copy()

# ── KPI row ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tracks shown", f"{len(filtered):,}")
c2.metric("Avg popularity", f"{filtered['popularity'].mean():.1f}")
c3.metric("Avg danceability", f"{filtered['danceability'].mean():.2f}")
c4.metric("Avg energy", f"{filtered['energy'].mean():.2f}")

st.divider()

# ── Chart 1: Scatter – Audio feature vs Popularity ─────────────────────────────
st.markdown('<p class="section-header">Audio Feature vs Popularity</p>', unsafe_allow_html=True)

x_col = AUDIO_FEATURES[x_feature_label]
y_col = AUDIO_FEATURES[y_feature_label]

scatter_df = filtered.sample(n=min(sample_size, len(filtered)), random_state=42)

fig_scatter = px.scatter(
    scatter_df,
    x=x_col,
    y="popularity",
    color="track_genre",
    size_max=8,
    opacity=0.65,
    hover_data={
        "track_name": True,
        "artists": True,
        "track_genre": True,
        "popularity": True,
        x_col: ":.2f",
        y_col: False,
    },
    labels={
        x_col: x_feature_label,
        "popularity": "Popularity",
        "track_genre": "Genre",
    },
    title=f"{x_feature_label} vs Popularity",
    color_discrete_sequence=px.colors.qualitative.Vivid,
)
fig_scatter.update_layout(
    plot_bgcolor="#181818",
    paper_bgcolor="#181818",
    font_color="#ffffff",
    legend_title="Genre",
    height=480,
    xaxis=dict(gridcolor="#282828"),
    yaxis=dict(gridcolor="#282828"),
    hoverlabel=dict(bgcolor="#282828", font_color="#ffffff"),
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ── Charts 2 + 3: side by side ─────────────────────────────────────────────────
col_left, col_right = st.columns(2)

# ── Chart 2: Average audio features radar by genre ─────────────────────────────
with col_left:
    st.markdown('<p class="section-header">Genre Sound Profile (Radar)</p>', unsafe_allow_html=True)

    radar_features = ["danceability", "energy", "valence", "acousticness", "speechiness", "liveness"]
    radar_labels   = ["Danceability", "Energy", "Valence", "Acousticness", "Speechiness", "Liveness"]

    genre_avg = (
        filtered.groupby("track_genre")[radar_features]
        .mean()
        .reset_index()
    )

    fig_radar = go.Figure()
    colors = px.colors.qualitative.Vivid
    for i, row in genre_avg.iterrows():
        vals = row[radar_features].tolist()
        vals += vals[:1]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals,
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            name=row["track_genre"],
            line_color=colors[i % len(colors)],
            opacity=0.6,
        ))

    fig_radar.update_layout(
        polar=dict(
            bgcolor="#181818",
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="#333"),
            angularaxis=dict(gridcolor="#333"),
        ),
        plot_bgcolor="#181818",
        paper_bgcolor="#181818",
        font_color="#ffffff",
        showlegend=True,
        legend=dict(font_size=11),
        height=420,
        margin=dict(t=30, b=20),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ── Chart 3: Popularity distribution by genre ──────────────────────────────────
with col_right:
    st.markdown('<p class="section-header">Popularity Distribution by Genre</p>', unsafe_allow_html=True)

    fig_box = px.box(
        filtered,
        x="track_genre",
        y="popularity",
        color="track_genre",
        points=False,
        labels={"track_genre": "Genre", "popularity": "Popularity"},
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig_box.update_layout(
        plot_bgcolor="#181818",
        paper_bgcolor="#181818",
        font_color="#ffffff",
        showlegend=False,
        height=420,
        margin=dict(t=30, b=20),
        xaxis=dict(gridcolor="#282828", tickangle=-30),
        yaxis=dict(gridcolor="#282828"),
    )
    st.plotly_chart(fig_box, use_container_width=True)

# ── Chart 4: Top 20 most popular tracks table ─────────────────────────────────
st.divider()
st.markdown('<p class="section-header">Top 20 Most Popular Tracks</p>', unsafe_allow_html=True)

top20 = (
    filtered
    .sort_values("popularity", ascending=False)
    .drop_duplicates(subset=["track_name", "artists"])
    [["track_name", "artists", "track_genre", "popularity", "danceability", "energy", "valence", "duration_min"]]
    .head(20)
    .rename(columns={
        "track_name": "Track",
        "artists": "Artist",
        "track_genre": "Genre",
        "popularity": "Popularity",
        "danceability": "Danceability",
        "energy": "Energy",
        "valence": "Valence",
        "duration_min": "Duration (min)",
    })
    .reset_index(drop=True)
)

st.dataframe(
    top20,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Popularity": st.column_config.ProgressColumn(
            "Popularity", min_value=0, max_value=100, format="%d"
        ),
        "Danceability": st.column_config.ProgressColumn(
            "Danceability", min_value=0, max_value=1, format="%.2f"
        ),
        "Energy": st.column_config.ProgressColumn(
            "Energy", min_value=0, max_value=1, format="%.2f"
        ),
    },
)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#535353; font-size:0.8rem;'>"
    "Built with Streamlit · Data: Spotify Tracks Dataset (Kaggle) · Assignment 5"
    "</p>",
    unsafe_allow_html=True,
)
