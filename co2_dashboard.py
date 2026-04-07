import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="CO2 Emissions Dashboard",
    page_icon="🌍",
    layout="wide"
)

FILE_PATH = "task2_co2/EDGARv7.0_FT2021_fossil_CO2_booklet_2022.xlsx"

# Helpers
def get_year_columns(df: pd.DataFrame) -> list[int]:
    year_cols = []
    for col in df.columns:
        if isinstance(col, int):
            year_cols.append(col)
        elif isinstance(col, str) and col.isdigit():
            year_cols.append(int(col))
    return sorted(year_cols)


def melt_years(
    df: pd.DataFrame,
    id_vars: list[str],
    value_name: str
) -> pd.DataFrame:
    year_cols = get_year_columns(df)
    melted = df.melt(
        id_vars=id_vars,
        value_vars=year_cols,
        var_name="year",
        value_name=value_name
    )
    melted["year"] = melted["year"].astype(int)
    melted[value_name] = pd.to_numeric(melted[value_name], errors="coerce")
    return melted


def clean_country_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Country"] = df["Country"].astype(str).str.strip()
    return df


def remove_special_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    exclude = {
        "International Aviation",
        "International Shipping"
    }
    return df[~df["Country"].isin(exclude)].copy()


def prepare_sector_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Sector"] = df["Sector"].astype(str).str.strip()

    sector_map = {
        "Power Industry": "Power Industry",
        "Manufacturing industries and construction": "Manufacturing",
        "Road Transportation": "Road Transport",
        "Other Transportation": "Other Transport",
        "Residential and commercial and other sectors": "Residential/Commercial",
        "Fuel exploitation": "Fuel Exploitation",
        "Industrial Processes": "Industrial Processes",
        "Other sectors": "Other Sectors",
    }

    df["Sector_clean"] = df["Sector"].map(sector_map).fillna(df["Sector"])
    return df


# Data loading
@st.cache_data
def load_data():
    totals_raw = pd.read_excel(FILE_PATH, sheet_name="fossil_CO2_totals_by_country")
    per_capita_raw = pd.read_excel(FILE_PATH, sheet_name="fossil_CO2_per_capita_by_countr")
    per_gdp_raw = pd.read_excel(FILE_PATH, sheet_name="fossil_CO2_per_GDP_by_country")
    sector_raw = pd.read_excel(FILE_PATH, sheet_name="fossil_CO2_by_sector_and_countr")

    # Clean basic fields
    totals_raw = clean_country_names(totals_raw)
    per_capita_raw = clean_country_names(per_capita_raw)
    per_gdp_raw = clean_country_names(per_gdp_raw)
    sector_raw = clean_country_names(sector_raw)

    totals_raw = remove_special_aggregates(totals_raw)
    per_capita_raw = remove_special_aggregates(per_capita_raw)
    per_gdp_raw = remove_special_aggregates(per_gdp_raw)
    sector_raw = remove_special_aggregates(sector_raw)

    sector_raw = prepare_sector_labels(sector_raw)

    # Melt wide year columns into long format
    totals = melt_years(
        totals_raw,
        id_vars=["Substance", "EDGAR Country Code", "Country"],
        value_name="co2_total_mt"
    )

    per_capita = melt_years(
        per_capita_raw,
        id_vars=["Substance", "EDGAR Country Code", "Country"],
        value_name="co2_per_capita"
    )

    per_gdp = melt_years(
        per_gdp_raw,
        id_vars=["Substance", "EDGAR Country Code", "Country"],
        value_name="co2_per_gdp"
    )

    sector = melt_years(
        sector_raw,
        id_vars=["Substance", "Sector", "EDGAR Country Code", "Country", "Sector_clean"],
        value_name="sector_emissions_mt"
    )


    # Exclude GLOBAL TOTAL
    EXCLUDE = ["GLOBAL TOTAL"]
    totals = totals[~totals["Country"].isin(EXCLUDE)]
    per_capita = per_capita[~per_capita["Country"].isin(EXCLUDE)]
    per_gdp = per_gdp[~per_gdp["Country"].isin(EXCLUDE)]
    sector = sector[~sector["Country"].isin(EXCLUDE)]

    # Keep only CO2 rows if anything else appears
    totals = totals[totals["Substance"] == "CO2"].copy()
    per_capita = per_capita[per_capita["Substance"] == "CO2"].copy()
    per_gdp = per_gdp[per_gdp["Substance"] == "CO2"].copy()
    sector = sector[sector["Substance"] == "CO2"].copy()

    # Drop missing values
    totals = totals.dropna(subset=["co2_total_mt"])
    per_capita = per_capita.dropna(subset=["co2_per_capita"])
    per_gdp = per_gdp.dropna(subset=["co2_per_gdp"])
    sector = sector.dropna(subset=["sector_emissions_mt"])

    return totals, per_capita, per_gdp, sector


totals_df, per_capita_df, per_gdp_df, sector_df = load_data()

# Sidebar
st.title("🌍 Worldwide CO₂ Emissions Dashboard")
st.markdown(
    """
    ### Total emissions, emissions per person, carbon intensity, and sector structure
    This dashboard compares countries from multiple perspectives to show that the biggest emitters
    are not always the highest emitters per person, and that sector structure matters.
    """
)

st.sidebar.header("Explore Data")

available_years = sorted(set(totals_df["year"].unique()) &
                         set(per_capita_df["year"].unique()) &
                         set(per_gdp_df["year"].unique()) &
                         set(sector_df["year"].unique()))

default_year = 2021 if 2021 in available_years else max(available_years)

selected_year = st.sidebar.selectbox(
    "Select year",
    available_years,
    index=available_years.index(default_year)
)

all_countries = sorted(totals_df["Country"].dropna().unique().tolist())

selected_countries = st.sidebar.multiselect(
    "Highlight countries (optional)",
    all_countries,
    default=["China", "United States", "India"] if all(
        c in all_countries for c in ["China", "United States", "India"]
    ) else []
)

top_n = st.sidebar.slider(
    "Top N countries in rankings",
    min_value=5,
    max_value=20,
    value=10
)

# Filtered data
totals_year = totals_df[totals_df["year"] == selected_year].copy()
per_capita_year = per_capita_df[per_capita_df["year"] == selected_year].copy()
per_gdp_year = per_gdp_df[per_gdp_df["year"] == selected_year].copy()
sector_year = sector_df[sector_df["year"] == selected_year].copy()

# Rankings
top_total = totals_year.nlargest(top_n, "co2_total_mt").copy()
top_per_capita = per_capita_year.nlargest(top_n, "co2_per_capita").copy()

# Join totals + per capita + per GDP
merged = totals_year.merge(
    per_capita_year[["Country", "year", "co2_per_capita"]],
    on=["Country", "year"],
    how="inner"
).merge(
    per_gdp_year[["Country", "year", "co2_per_gdp"]],
    on=["Country", "year"],
    how="inner"
)

merged["highlight"] = merged["Country"].apply(
    lambda x: "Selected" if x in selected_countries else "Other countries"
)

# Sector breakdown for selected/highlighted countries
if selected_countries:
    sector_focus = sector_year[sector_year["Country"].isin(selected_countries)].copy()
else:
    top_sector_countries = top_total["Country"].head(5).tolist()
    sector_focus = sector_year[sector_year["Country"].isin(top_sector_countries)].copy()

sector_grouped = (
    sector_focus.groupby(["Country", "Sector_clean"], as_index=False)["sector_emissions_mt"]
    .sum()
)

# KPI row
col1, col2, col3 = st.columns(3)

col1.metric(
    f"Highest total emissions ({selected_year})",
    top_total.iloc[0]["Country"] if not top_total.empty else "N/A",
    f"{top_total.iloc[0]['co2_total_mt']:.1f} Mt CO₂/yr" if not top_total.empty else ""
)

col2.metric(
    f"Highest per capita ({selected_year})",
    top_per_capita.iloc[0]["Country"] if not top_per_capita.empty else "N/A",
    f"{top_per_capita.iloc[0]['co2_per_capita']:.2f} t CO₂/cap/yr" if not top_per_capita.empty else ""
)

best_efficiency = per_gdp_year.nsmallest(1, "co2_per_gdp")
col3.metric(
    f"Lowest CO₂ per GDP ({selected_year})",
    best_efficiency.iloc[0]["Country"] if not best_efficiency.empty else "N/A",
    f"{best_efficiency.iloc[0]['co2_per_gdp']:.3f} t CO₂/kUSD/yr" if not best_efficiency.empty else ""
)

st.markdown(
    """
    Use the charts below to compare countries from four perspectives:
    total emissions, emissions per person, carbon intensity per GDP, and sector composition.
    """
)

# Chart 1: Total emissions
fig_total = px.bar(
    top_total.sort_values("co2_total_mt", ascending=True),
    x="co2_total_mt",
    y="Country",
    orientation="h",
    title=f"Top {top_n} countries by total CO₂ emissions ({selected_year})",
    labels={
        "co2_total_mt": "CO₂ emissions (Mt CO₂/yr)",
        "Country": "Country"
    },
    hover_data={"co2_total_mt": ":.2f"}
)
fig_total.update_layout(yaxis_title="Country", xaxis_title="CO₂ emissions (Mt CO₂/yr)")

# Chart 2: Per capita
fig_per_capita = px.bar(
    top_per_capita.sort_values("co2_per_capita", ascending=True),
    x="co2_per_capita",
    y="Country",
    orientation="h",
    title=f"Top {top_n} countries by CO₂ emissions per capita ({selected_year})",
    labels={
        "co2_per_capita": "CO₂ per capita (t CO₂/cap/yr)",
        "Country": "Country"
    },
    hover_data={"co2_per_capita": ":.2f"}
)
fig_per_capita.update_layout(yaxis_title="Country", xaxis_title="CO₂ per capita (t CO₂/cap/yr)")

# Chart 3: Scatter - total vs per GDP
fig_scatter = px.scatter(
    merged,
    x="co2_total_mt",
    y="co2_per_gdp",
    hover_name="Country",
    color="highlight",
    title=f"Total emissions vs carbon intensity per GDP ({selected_year})",
    labels={
        "co2_total_mt": "Total CO₂ emissions (Mt CO₂/yr)",
        "co2_per_gdp": "CO₂ per GDP (t CO₂/kUSD/yr)",
        "highlight": "Selection"
    },
    hover_data={
        "co2_total_mt": ":.2f",
        "co2_per_gdp": ":.3f",
        "co2_per_capita": ":.2f"
    },
    log_x=True
)

# Chart 4: Sector breakdown
fig_sector = px.bar(
    sector_grouped,
    x="Country",
    y="sector_emissions_mt",
    color="Sector_clean",
    title=f"Sector breakdown of CO₂ emissions ({selected_year})",
    labels={
        "sector_emissions_mt": "Sector emissions (Mt CO₂/yr)",
        "Country": "Country",
        "Sector_clean": "Sector"
    }
)
fig_sector.update_layout(
    xaxis_title="Country",
    yaxis_title="Sector emissions (Mt CO₂/yr)",
    legend_title="Sector"
)

# Layout
row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.plotly_chart(fig_total, use_container_width=True)
with row1_col2:
    st.plotly_chart(fig_per_capita, use_container_width=True)

st.plotly_chart(fig_scatter, use_container_width=True)
st.plotly_chart(fig_sector, use_container_width=True)

# Notes / limitations
with st.expander("Method and limitations"):
    st.markdown(
        """
        - This dashboard compares countries using four different CO₂ perspectives.
        - Total emissions and per capita emissions answer different questions and should not be interpreted as the same kind of impact.
        - The scatter plot uses a logarithmic x-axis because total emissions vary greatly across countries.
        - Some sector names were shortened to improve readability.
        - International aggregate categories such as aviation/shipping were excluded from country-level comparisons.
        """
    )

with st.expander("Preview cleaned data"):
    st.dataframe(merged.head(100))