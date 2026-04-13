import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Fellow Dashboard", layout="wide")

# =========================
# CONFIG
# =========================
CSV_PATH = "employbility_clean_data.csv"

# Optional: set this if you want to compare against onboarded target
ONBOARDED_TARGET = 24000

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Clean text columns
    text_cols = ["Email", "Full Name", "Gender", "State", "Region",
                 "Placement Tier", "MBTI Type", "Strength Area",
                 "Development Area", "Primary Sector", "Secondary Sector"]
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
def pct(series):
    return (series / series.sum() * 100).round(1)

def count_pct_table(series, col_name="Category"):
    counts = series.value_counts(dropna=False).rename_axis(col_name).reset_index(name="Count")
    counts["Percent"] = (counts["Count"] / counts["Count"].sum() * 100).round(1)
    return counts

def top_n_table(data, sort_col, n=10):
    cols = ["Full Name", "Email", "Gender", "Region", "Primary Sector", sort_col]
    cols = [c for c in cols if c in data.columns]
    return data[cols].sort_values(sort_col, ascending=False).head(n)

# =========================
# TITLE
# =========================
st.title("Fellow Performance and Distribution Dashboard")

st.markdown("This dashboard uses a deduplicated fellow-level view for KPIs and keeps the raw table available where needed.")

# =========================
# KPI SECTION
# =========================
total_rows = len(df)
total_fellows = fellows["Email"].nunique()
completion_rate = round((total_fellows / ONBOARDED_TARGET) * 100, 1) if ONBOARDED_TARGET else None
avg_merit_score = fellows["Overall Average"].mean()
avg_merit_out_of_10 = avg_merit_score / 10 if pd.notna(avg_merit_score) else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Entry", f"{total_rows:,}")
c2.metric("Total Fellows", f"{total_fellows:,}")
c3.metric("Completion Rate", f"{completion_rate}%" if completion_rate is not None else "N/A")
c4.metric("Average Merit Score", f"{avg_merit_score:.1f}" if pd.notna(avg_merit_score) else "N/A")

c5, c6, c7 = st.columns(3)
c5.metric("Average Merit (out of 10)", f"{avg_merit_out_of_10:.2f}" if avg_merit_out_of_10 is not None else "N/A")
c6.metric("Female Fellows", f"{(fellows['Gender'] == 'Female').sum():,}" if "Gender" in fellows.columns else "N/A")
c7.metric("Male Fellows", f"{(fellows['Gender'] == 'Male').sum():,}" if "Gender" in fellows.columns else "N/A")

# =========================
# GENDER + REGION
# =========================
left, right = st.columns(2)

with left:
    st.subheader("Gender Split (Overall)")
    gender_df = count_pct_table(fellows["Gender"], "Gender")
    fig_gender = px.pie(
        gender_df,
        names="Gender",
        values="Count",
        hole=0.4
    )
    st.plotly_chart(fig_gender, use_container_width=True)
    st.dataframe(gender_df, use_container_width=True)

with right:
    st.subheader("Geopolitical Spread (Overall)")
    region_df = count_pct_table(fellows["Region"], "Region")
    fig_region = px.bar(
        region_df,
        x="Region",
        y="Count",
        text="Percent"
    )
    fig_region.update_traces(texttemplate="%{text}%", textposition="outside")
    st.plotly_chart(fig_region, use_container_width=True)
    st.dataframe(region_df, use_container_width=True)

# =========================
# STATE DISTRIBUTION
# =========================
st.subheader("State Distribution")

all_states = sorted(fellows["State"].dropna().unique().tolist())

selected_states = st.multiselect(
    "Select state(s)",
    options=all_states,
    default=all_states
)

filtered_states_df = fellows[fellows["State"].isin(selected_states)]

state_df = (
    filtered_states_df["State"]
    .value_counts()
    .reset_index()
)
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
    width=1400,
    height=600
)

st.plotly_chart(fig_state, use_container_width=True)
st.dataframe(state_df, use_container_width=True)

st.subheader("Placement Tier Breakdown")

tier_df = count_pct_table(fellows["Placement Tier"], "Placement Tier")

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
    xaxis_tickangle=0,   # 🔥 straight labels (fixes slanted text)
    height=500           # 🔥 better height (not too flat)
)

st.plotly_chart(fig_tier, use_container_width=True)
st.dataframe(tier_df, use_container_width=True)

# =========================
# TOP PERFORMERS
# =========================
st.subheader("Top Performing Learners")
top_n = st.slider("Select number of top learners", 5, 50, 10)

top_df = top_n_table(fellows, "Overall Average", n=top_n)
st.dataframe(top_df, use_container_width=True)

# =========================
# SECTOR VIEWS
# =========================
st.subheader("% of Sectors by Region")

sector_region = (
    fellows.groupby(["Region", "Primary Sector"])
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

# =========================
# MENTEE-LIKE FILTER TABLE
# =========================
st.subheader("Filtered Fellow List")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    region_options = ["All"] + sorted(fellows["Region"].dropna().unique().tolist())
    selected_region = st.selectbox("Filter by Region", region_options)

with filter_col2:
    sector_options = ["All"] + sorted(fellows["Primary Sector"].dropna().unique().tolist())
    selected_sector = st.selectbox("Filter by Primary Sector", sector_options)

with filter_col3:
    gender_options = ["All"] + sorted(fellows["Gender"].dropna().unique().tolist())
    selected_gender = st.selectbox("Filter by Gender", gender_options)

filtered = fellows.copy()

if selected_region != "All":
    filtered = filtered[filtered["Region"] == selected_region]

if selected_sector != "All":
    filtered = filtered[filtered["Primary Sector"] == selected_sector]

if selected_gender != "All":
    filtered = filtered[filtered["Gender"] == selected_gender]

display_cols = ["Full Name", "Email", "Gender", "Region", "State", "Primary Sector", "Secondary Sector", "Placement Tier", "Overall Average"]
display_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(filtered[display_cols].sort_values("Overall Average", ascending=False), use_container_width=True)

# =========================
# DOWNLOAD CLEANED FELLOW TABLE
# =========================
st.subheader("Download Deduplicated Fellow Table")
csv_download = fellows.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download fellow-level CSV",
    data=csv_download,
    file_name="fellows_deduplicated.csv",
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