import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="UFO Dashboard", page_icon="🚀", layout="wide")

st.title("UFO Dashboard 🚀")
st.markdown("""
### UFO Sightings Have Increased Dramatically Since the 1990s,
### With ‘Light’ and ‘Triangle’ Objects Dominating Reports
""")

@st.cache_data
def load_data():
    df = pd.read_csv(
        "complete.csv",
        engine="python",
        on_bad_lines="skip"
    )

    # Clean column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Parse and clean fields
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df["year"] = df["datetime"].dt.year

    df["country"] = df["country"].astype(str).str.strip().str.upper()
    df["shape"] = df["shape"].astype(str).str.strip().str.lower()

    # Remove invalid rows
    df = df.dropna(subset=["datetime", "year"])
    df = df[df["shape"].notna()]
    df = df[df["shape"] != ""]
    df = df[df["shape"] != "nan"]

    return df


def add_shape_groups(df, top_n=5):
    top_shapes = df["shape"].value_counts().head(top_n).index.tolist()
    df = df.copy()
    df["shape_group"] = df["shape"].apply(lambda x: x if x in top_shapes else "other")
    return df, top_shapes


df = load_data()
df, top_shapes = add_shape_groups(df, top_n=5)

color_map = {
    "light": "#FFD700",
    "triangle": "#00CC96",
    "circle": "#636EFA",
    "fireball": "#EF553B",
    "unknown": "#AB63FA",
    "other": "#888888"
}

# Sidebar filters
st.sidebar.header("Explore Data")

countries = sorted(df["country"].dropna().unique().tolist())
default_country = "US" if "US" in countries else countries[0]

selected_country = st.sidebar.selectbox(
    "Select country",
    countries,
    index=countries.index(default_country)
)

min_year = int(df["year"].min())
max_year = int(df["year"].max())

selected_years = st.sidebar.slider(
    "Select year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

available_shapes = top_shapes + ["other"]
default_shapes = [shape for shape in available_shapes if shape != "other"]

st.sidebar.caption("‘Other’ includes less common UFO shapes and is hidden by default to reduce clutter.")

selected_shapes = st.sidebar.multiselect(
    "Select shapes",
    available_shapes,
    default=default_shapes
)

# Apply filters to the whole dashboard
filtered_df = df[
    (df["country"] == selected_country) &
    (df["year"].between(selected_years[0], selected_years[1])) &
    (df["shape_group"].isin(selected_shapes))
].copy()

# Remove last incomplete year to avoid misleading drop
dataset_max_year = df["year"].max()
filtered_df = filtered_df[filtered_df["year"] < dataset_max_year]

# KPI row
col1, col2, col3 = st.columns(3)
col1.metric("Total sightings", f"{len(filtered_df):,}")
col2.metric("Years covered", f"{filtered_df['year'].nunique():,}")
col3.metric("Shapes shown", f"{filtered_df['shape_group'].nunique():,}")

st.markdown("""
This dashboard shows a clear increase in UFO sightings after 1995.
The most commonly reported shapes are light-based objects, followed by triangles and circles.
Use the filters to explore how these patterns change across time and location.
""")

# Main chart: sightings over time by shape
yearly_shape_counts = (
    filtered_df.groupby(["year", "shape_group"])
    .size()
    .reset_index(name="sightings")
)

fig_line = px.line(
    yearly_shape_counts,
    x="year",
    y="sightings",
    color="shape_group",
    markers=True,
    title="UFO Sightings Over Time by Shape",
    labels={
        "year": "Year",
        "sightings": "Number of sightings",
        "shape_group": "Shape"
    },
    hover_data={"year": True, "sightings": True, "shape_group": True},
    color_discrete_map=color_map
)
fig_line.update_layout(legend_title_text="Shape")

# Supporting chart: most common shapes
shape_counts = (
    filtered_df["shape_group"]
    .value_counts()
    .reset_index()
)
shape_counts.columns = ["shape_group", "sightings"]
shape_counts = shape_counts.sort_values(by="sightings", ascending=False)

fig_bar = px.bar(
    shape_counts,
    x="shape_group",
    y="sightings",
    color="shape_group",
    title="Most Common UFO Shapes",
    labels={
        "shape_group": "Shape",
        "sightings": "Number of sightings"
    },
    hover_data={"shape_group": True, "sightings": True},
    color_discrete_map=color_map
)
fig_bar.update_layout(showlegend=False)

# Layout
left_col, right_col = st.columns([2, 1])

with left_col:
    st.plotly_chart(fig_line, use_container_width=True)

with right_col:
    st.plotly_chart(fig_bar, use_container_width=True)

with st.expander("Show filtered data preview"):
    st.dataframe(
        filtered_df[["datetime", "year", "country", "shape", "shape_group"]].head(100)
    )
