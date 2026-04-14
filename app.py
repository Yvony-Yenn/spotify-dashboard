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

# ── Light Theme CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #F7F7F7; }
    .block-container { padding-top: 2rem; }
    h1 { color: #1DB954; font-size: 2.2rem !important; }
    h2, h3 { color: #191414; }
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    .stMetric label { color: #535353 !important; font-size: 0.85rem !important; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1DB954;
        margin: 1.5rem 0 0.5rem 0;
        border-bottom: 2px solid #1DB954;
        padding-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Data/spotify-tracks-dataset.csv")
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

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Feature vs Popularity", "🎸 Genre Analysis", "🔍 Track Explorer"])

# ━━━ Tab 1: Scatter + Box ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 2])
    with ctrl1:
        x_feature_label = st.selectbox(
            "X-axis feature", list(AUDIO_FEATURES.keys()), index=0, key="t1_x"
        )
    with ctrl2:
        y_options = {"Popularity": "popularity", **AUDIO_FEATURES}
        y_feature_label = st.selectbox(
            "Y-axis feature", list(y_options.keys()), index=0, key="t1_y"
        )
    with ctrl3:
        sample_size = st.slider("Max points on scatter", 200, 3000, 1000, 100, key="t1_sample")

    x_col = AUDIO_FEATURES[x_feature_label]
    y_col = y_options[y_feature_label]
    scatter_df = filtered.sample(n=min(sample_size, len(filtered)), random_state=42)

    fig_scatter = px.scatter(
        scatter_df,
        x=x_col, y=y_col,
        color="track_genre",
        opacity=0.65,
        hover_data={"track_name": True, "artists": True, "track_genre": True, "popularity": True},
        labels={x_col: x_feature_label, y_col: y_feature_label, "track_genre": "Genre"},
        title=f"{x_feature_label} vs {y_feature_label}",
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig_scatter.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_color="#191414", height=480,
        xaxis=dict(gridcolor="#EEEEEE", showgrid=True),
        yaxis=dict(gridcolor="#EEEEEE", showgrid=True),
        hoverlabel=dict(bgcolor="white", font_color="#191414"),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown('<p class="section-header">Popularity Distribution by Genre</p>', unsafe_allow_html=True)
    fig_box = px.box(
        filtered, x="track_genre", y="popularity",
        color="track_genre", points=False,
        labels={"track_genre": "Genre", "popularity": "Popularity"},
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig_box.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_color="#191414", showlegend=False, height=400,
        xaxis=dict(gridcolor="#EEEEEE", tickangle=-30),
        yaxis=dict(gridcolor="#EEEEEE"),
    )
    st.plotly_chart(fig_box, use_container_width=True)

# ━━━ Tab 2: Genre Analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<p class="section-header">Genre Sound Profile (Radar)</p>', unsafe_allow_html=True)
        radar_features = ["danceability", "energy", "valence", "acousticness", "speechiness", "liveness"]
        radar_labels   = ["Danceability", "Energy", "Valence", "Acousticness", "Speechiness", "Liveness"]
        genre_avg = filtered.groupby("track_genre")[radar_features].mean().reset_index()

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
                bgcolor="white",
                radialaxis=dict(visible=True, range=[0, 1], gridcolor="#DDD"),
                angularaxis=dict(gridcolor="#DDD"),
            ),
            plot_bgcolor="white", paper_bgcolor="white",
            font_color="#191414",
            height=420, margin=dict(t=30, b=20),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_right:
        st.markdown('<p class="section-header">Feature Correlation Heatmap</p>', unsafe_allow_html=True)
        feat_cols = list(AUDIO_FEATURES.values()) + ["popularity"]
        corr = filtered[feat_cols].corr()
        fig_heat = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdYlGn",
            zmin=-1, zmax=1,
            labels=dict(color="Correlation"),
        )
        fig_heat.update_layout(
            paper_bgcolor="white", font_color="#191414",
            height=420, margin=dict(t=30, b=20),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<p class="section-header">Average Feature by Genre</p>', unsafe_allow_html=True)
    bar_feature_label = st.selectbox(
        "Select feature to compare across genres",
        list(AUDIO_FEATURES.keys()),
        key="t2_bar",
    )
    bar_col = AUDIO_FEATURES[bar_feature_label]
    bar_df = (
        filtered.groupby("track_genre")[bar_col]
        .mean().reset_index()
        .sort_values(bar_col, ascending=False)
    )
    fig_bar = px.bar(
        bar_df, x="track_genre", y=bar_col,
        color="track_genre",
        labels={"track_genre": "Genre", bar_col: bar_feature_label},
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig_bar.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_color="#191414", showlegend=False, height=350,
        xaxis=dict(gridcolor="#EEEEEE", tickangle=-30),
        yaxis=dict(gridcolor="#EEEEEE"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ━━━ Tab 3: Track Explorer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.markdown('<p class="section-header">Search & Filter Tracks</p>', unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        artist_query = st.text_input("Search by artist name", placeholder="e.g. Taylor Swift, Drake…")
    with col_s2:
        sort_by = st.selectbox("Sort by", ["Popularity", "Danceability", "Energy", "Valence (Positivity)"])

    with st.expander("🎚️ Advanced: Filter by audio features"):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            dance_range = st.slider("Danceability", 0.0, 1.0, (0.0, 1.0), 0.05, key="t3_dance")
            energy_range = st.slider("Energy", 0.0, 1.0, (0.0, 1.0), 0.05, key="t3_energy")
        with fc2:
            valence_range = st.slider("Valence (Positivity)", 0.0, 1.0, (0.0, 1.0), 0.05, key="t3_valence")
            acoustic_range = st.slider("Acousticness", 0.0, 1.0, (0.0, 1.0), 0.05, key="t3_acoustic")
        with fc3:
            tempo_min = float(df["tempo"].min())
            tempo_max = float(df["tempo"].max())
            tempo_range = st.slider("Tempo (BPM)", tempo_min, tempo_max, (tempo_min, tempo_max), 1.0, key="t3_tempo")

    sort_col_map = {
        "Popularity": "popularity",
        "Danceability": "danceability",
        "Energy": "energy",
        "Valence (Positivity)": "valence",
    }
    sort_col = sort_col_map[sort_by]

    explorer_df = filtered.copy()
    if artist_query:
        explorer_df = explorer_df[
            explorer_df["artists"].str.contains(artist_query, case=False, na=False)
        ]

    explorer_df = explorer_df[
        explorer_df["danceability"].between(*dance_range) &
        explorer_df["energy"].between(*energy_range) &
        explorer_df["valence"].between(*valence_range) &
        explorer_df["acousticness"].between(*acoustic_range) &
        explorer_df["tempo"].between(*tempo_range)
    ]

    st.caption(f"**{len(explorer_df):,}** tracks match your filters (showing top 50)")

    display_df = (
        explorer_df
        .sort_values(sort_col, ascending=False)
        .drop_duplicates(subset=["track_name", "artists"])
        [["track_name", "artists", "track_genre", "popularity",
          "danceability", "energy", "valence", "tempo", "duration_min"]]
        .head(50)
        .rename(columns={
            "track_name": "Track", "artists": "Artist", "track_genre": "Genre",
            "popularity": "Popularity", "danceability": "Danceability",
            "energy": "Energy", "valence": "Valence",
            "tempo": "Tempo (BPM)", "duration_min": "Duration (min)",
        })
        .reset_index(drop=True)
    )

    st.dataframe(
        display_df,
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
