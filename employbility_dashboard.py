import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Fellow Dashboard", layout="wide")

# =========================
# CONFIG
# =========================
CSV_PATH = "employbility_clean_data.csv"
ONBOARDED_TARGET = 24000

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Clean text columns
    text_cols = [
        "Email", "Full Name", "Gender", "State", "Region",
        "Placement Tier", "MBTI Type", "Strength Area",
        "Development Area", "Primary Sector", "Secondary Sector"
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Standardize state names
    if "State" in df.columns:
        df["State"] = (
            df["State"]
            .str.replace("State", "", case=False, regex=False)
            .str.strip()
            .str.title()
            .replace({"Abuja": "Federal Capital Territory"})
        )

    # Standardize region names
    if "Region" in df.columns:
        df["Region"] = (
            df["Region"]
            .str.strip()
            .replace({"North-north east": "North-East"})
        )

    # Convert numeric columns
    numeric_cols = [
        "Assessment Time (min)",
        "SJT Score",
        "Employability Score",
        "Cognitive Score",
        "Personality Score",
        "Logic",
        "Numeric",
        "Verbal",
        "Overall Average",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df = load_data(CSV_PATH)

# Fellow-level table: one row per fellow
fellows = df.drop_duplicates(subset="Email").copy()

# =========================
# HELPERS
# =========================
def count_pct_table(series, col_name="Category"):
    counts = series.value_counts(dropna=False).rename_axis(col_name).reset_index(name="Count")
    counts["Percent"] = (counts["Count"] / counts["Count"].sum() * 100).round(1)
    return counts

def top_n_table(data, sort_col, n=10):
    cols = ["Full Name", "Email", "Gender", "Region", "State", "Primary Sector", sort_col]
    cols = [c for c in cols if c in data.columns]
    return data[cols].sort_values(sort_col, ascending=False).head(n)

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Filter Dashboard")

region_options = ["All"] + sorted(fellows["Region"].dropna().unique().tolist())

# State options can depend on selected region
selected_region = st.sidebar.selectbox("Region", region_options)

region_filtered_for_state = fellows.copy()
if selected_region != "All":
    region_filtered_for_state = region_filtered_for_state[
        region_filtered_for_state["Region"] == selected_region
    ]

state_options = ["All"] + sorted(region_filtered_for_state["State"].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("State", state_options)

# Primary sector options can depend on selected region + state
sector_filtered_base = fellows.copy()
if selected_region != "All":
    sector_filtered_base = sector_filtered_base[sector_filtered_base["Region"] == selected_region]
if selected_state != "All":
    sector_filtered_base = sector_filtered_base[sector_filtered_base["State"] == selected_state]

sector_options = ["All"] + sorted(sector_filtered_base["Primary Sector"].dropna().unique().tolist())
selected_sector = st.sidebar.selectbox("Primary Sector", sector_options)

# Apply all filters
filtered_fellows = fellows.copy()

if selected_region != "All":
    filtered_fellows = filtered_fellows[filtered_fellows["Region"] == selected_region]

if selected_state != "All":
    filtered_fellows = filtered_fellows[filtered_fellows["State"] == selected_state]

if selected_sector != "All":
    filtered_fellows = filtered_fellows[filtered_fellows["Primary Sector"] == selected_sector]

# =========================
# TITLE
# =========================
st.title("Fellow Performance and Distribution Dashboard")
st.markdown("UNDP Employability Survey Dashboard.")

# =========================
# KPI SECTION
# =========================
total_rows = len(df)
total_fellows = filtered_fellows["Email"].nunique()
completion_rate = round((total_fellows / ONBOARDED_TARGET) * 100, 1) if ONBOARDED_TARGET else None
avg_merit_score = filtered_fellows["Overall Average"].mean()
avg_merit_out_of_10 = avg_merit_score / 10 if pd.notna(avg_merit_score) else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Response", f"{total_rows:,}")
c2.metric("Total Fellows", f"{total_fellows:,}")
c3.metric("Completion Rate", f"{completion_rate}%" if completion_rate is not None else "N/A")
c4.metric("Average Merit Score", f"{avg_merit_score:.1f}" if pd.notna(avg_merit_score) else "N/A")

c5, c6, c7 = st.columns(3)
c5.metric("Average Merit (out of 10)", f"{avg_merit_out_of_10:.2f}" if avg_merit_out_of_10 is not None else "N/A")
c6.metric(
    "Female Fellows",
    f"{(filtered_fellows['Gender'] == 'Female').sum():,}" if "Gender" in filtered_fellows.columns else "N/A"
)
c7.metric(
    "Male Fellows",
    f"{(filtered_fellows['Gender'] == 'Male').sum():,}" if "Gender" in filtered_fellows.columns else "N/A"
)

# =========================
# GENDER + REGION
# =========================
left, right = st.columns(2)

with left:
    st.subheader("Gender Split (Overall)")
    if not filtered_fellows.empty:
        gender_df = count_pct_table(filtered_fellows["Gender"], "Gender")
        fig_gender = px.pie(
            gender_df,
            names="Gender",
            values="Count",
            hole=0.4
        )
        st.plotly_chart(fig_gender, use_container_width=True)
        st.dataframe(gender_df, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

with right:
    st.subheader("Geopolitical Spread (Overall)")
    if not filtered_fellows.empty:
        region_df = count_pct_table(filtered_fellows["Region"], "Region")
        fig_region = px.bar(
            region_df,
            x="Region",
            y="Count",
            text="Percent"
        )
        fig_region.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig_region, use_container_width=True)
        st.dataframe(region_df, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

# =========================
# STATE DISTRIBUTION
# =========================
st.subheader("State Distribution")

if not filtered_fellows.empty:
    state_df = filtered_fellows["State"].value_counts().reset_index()
    state_df.columns = ["State", "Count"]
    state_df["Percent"] = (state_df["Count"] / state_df["Count"].sum() * 100).round(1)

    fig_state = px.bar(
        state_df,
        x="State",
        y="Count",
        text="Percent",
        title="State Distribution"
    )

    fig_state.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_state.update_layout(
        xaxis_tickangle=-35,
        height=600
    )

    st.plotly_chart(fig_state, use_container_width=True)
    st.dataframe(state_df, use_container_width=True)
else:
    st.info("No data available for the selected filters.")

# =========================
# PLACEMENT TIER BREAKDOWN
# =========================
st.subheader("Placement Tier Breakdown")

if not filtered_fellows.empty:
    tier_df = count_pct_table(filtered_fellows["Placement Tier"], "Placement Tier")

    fig_tier = px.bar(
        tier_df,
        x="Placement Tier",
        y="Count",
        text="Percent",
        title="Placement Tier Breakdown"
    )

    fig_tier.update_traces(
        texttemplate="%{text}%",
        textposition="outside"
    )

    fig_tier.update_layout(
        xaxis_title="Placement Tier",
        yaxis_title="Count",
        xaxis_tickangle=0,
        height=500
    )

    st.plotly_chart(fig_tier, use_container_width=True)
    st.dataframe(tier_df, use_container_width=True)
else:
    st.info("No data available for the selected filters.")

# =========================
# TOP PERFORMERS
# =========================
st.subheader("Top Performing Learners")
top_n = st.slider("Select number of top learners", 5, 50, 10)

if not filtered_fellows.empty:
    top_df = top_n_table(filtered_fellows, "Overall Average", n=top_n)
    st.dataframe(top_df, use_container_width=True)
else:
    st.info("No data available for the selected filters.")

# =========================
# SECTOR VIEWS
# =========================
st.subheader("% of Sectors by Region")

if not filtered_fellows.empty:
    sector_region = (
        filtered_fellows.groupby(["Region", "Primary Sector"])
        .size()
        .reset_index(name="Count")
    )

    sector_region["Region Total"] = sector_region.groupby("Region")["Count"].transform("sum")
    sector_region["Percent"] = (sector_region["Count"] / sector_region["Region Total"] * 100).round(1)

    fig_sector_region = px.bar(
        sector_region,
        x="Region",
        y="Percent",
        color="Primary Sector",
        text="Percent"
    )
    fig_sector_region.update_traces(texttemplate="%{text}%", textposition="inside")
    st.plotly_chart(fig_sector_region, use_container_width=True)
else:
    st.info("No data available for the selected filters.")

# =========================
# FILTERED FELLOW LIST
# =========================
st.subheader("Filtered Fellow List")

display_cols = [
    "Full Name", "Email", "Gender", "Region", "State",
    "Primary Sector", "Secondary Sector", "Placement Tier", "Overall Average"
]
display_cols = [c for c in display_cols if c in filtered_fellows.columns]

if not filtered_fellows.empty:
    st.dataframe(
        filtered_fellows[display_cols].sort_values("Overall Average", ascending=False),
        use_container_width=True
    )
else:
    st.info("No data available for the selected filters.")

# =========================
# DOWNLOAD FILTERED TABLE
# =========================
st.subheader("Download Filtered Fellow Table")
csv_download = filtered_fellows.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered fellow CSV",
    data=csv_download,
    file_name="filtered_fellows.csv",
    mime="text/csv"
)

# =========================
# MISSING KPI NOTICE
# =========================
with st.expander("Metrics requested but not present in this CSV"):
    st.markdown("""
The following requested KPIs cannot be built from the current file because their fields are not present yet:

- Total mentors
- Total mentees assigned
""")