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
        "Development Area", "Primary Sector", "Secondary Sector",
        "Mapped_Sector", "Assigned Mentor", "Assigned Mentor State",
        "Assigned Mentor Region", "Match Type"
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
            )

    # Standardize state names
    if "State" in df.columns:
        df["State"] = (
            df["State"]
            .str.replace("State", "", case=False, regex=False)
            .str.strip()
            .str.title()
            .replace({"Abuja": "Federal Capital Territory"})
        )

    if "Assigned Mentor State" in df.columns:
        df["Assigned Mentor State"] = (
            df["Assigned Mentor State"]
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

    if "Assigned Mentor Region" in df.columns:
        df["Assigned Mentor Region"] = (
            df["Assigned Mentor Region"]
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

# One row per mentee/fellow
fellows = df.drop_duplicates(subset="Email").copy()

# =========================
# HELPERS
# =========================
def count_pct_table(series, col_name="Category"):
    counts = series.value_counts(dropna=False).rename_axis(col_name).reset_index(name="Count")
    counts["Percent"] = (counts["Count"] / counts["Count"].sum() * 100).round(1)
    return counts

def safe_options(data, col):
    if col not in data.columns:
        return ["All"]
    return ["All"] + sorted(data[col].dropna().unique().tolist())

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Filter Dashboard")

# Region
region_options = safe_options(fellows, "Region")
selected_region = st.sidebar.selectbox("Region", region_options)

region_filtered_for_state = fellows.copy()
if selected_region != "All":
    region_filtered_for_state = region_filtered_for_state[
        region_filtered_for_state["Region"] == selected_region
    ]

# State
state_options = safe_options(region_filtered_for_state, "State")
selected_state = st.sidebar.selectbox("State", state_options)

sector_filtered_base = region_filtered_for_state.copy()
if selected_state != "All":
    sector_filtered_base = sector_filtered_base[sector_filtered_base["State"] == selected_state]

# Primary Sector
sector_options = safe_options(sector_filtered_base, "Primary Sector")
selected_sector = st.sidebar.selectbox("Primary Sector", sector_options)

# Mentor Region
mentor_region_base = sector_filtered_base.copy()
if selected_sector != "All":
    mentor_region_base = mentor_region_base[mentor_region_base["Primary Sector"] == selected_sector]

mentor_region_options = safe_options(mentor_region_base, "Assigned Mentor Region")
selected_mentor_region = st.sidebar.selectbox("Assigned Mentor Region", mentor_region_options)

# Mentor State
mentor_state_base = mentor_region_base.copy()
if selected_mentor_region != "All":
    mentor_state_base = mentor_state_base[
        mentor_state_base["Assigned Mentor Region"] == selected_mentor_region
    ]

mentor_state_options = safe_options(mentor_state_base, "Assigned Mentor State")
selected_mentor_state = st.sidebar.selectbox("Assigned Mentor State", mentor_state_options)

# Match Type
match_type_base = mentor_state_base.copy()
if selected_mentor_state != "All":
    match_type_base = match_type_base[
        match_type_base["Assigned Mentor State"] == selected_mentor_state
    ]

match_type_options = safe_options(match_type_base, "Match Type")
selected_match_type = st.sidebar.selectbox("Match Type", match_type_options)

# Mentor
mentor_base = match_type_base.copy()
if selected_match_type != "All":
    mentor_base = mentor_base[mentor_base["Match Type"] == selected_match_type]

mentor_options = safe_options(mentor_base, "Assigned Mentor")
selected_mentor = st.sidebar.selectbox("Assigned Mentor", mentor_options)

# =========================
# APPLY ALL FILTERS
# =========================
filtered_fellows = fellows.copy()

if selected_region != "All":
    filtered_fellows = filtered_fellows[filtered_fellows["Region"] == selected_region]

if selected_state != "All":
    filtered_fellows = filtered_fellows[filtered_fellows["State"] == selected_state]

if selected_sector != "All":
    filtered_fellows = filtered_fellows[filtered_fellows["Primary Sector"] == selected_sector]

if selected_mentor_region != "All":
    filtered_fellows = filtered_fellows[
        filtered_fellows["Assigned Mentor Region"] == selected_mentor_region
    ]

if selected_mentor_state != "All":
    filtered_fellows = filtered_fellows[
        filtered_fellows["Assigned Mentor State"] == selected_mentor_state
    ]

if selected_match_type != "All":
    filtered_fellows = filtered_fellows[filtered_fellows["Match Type"] == selected_match_type]

if selected_mentor != "All":
    filtered_fellows = filtered_fellows[filtered_fellows["Assigned Mentor"] == selected_mentor]

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

total_mentors = (
    filtered_fellows["Assigned Mentor"].dropna().nunique()
    if "Assigned Mentor" in filtered_fellows.columns else 0
)
total_mentees_assigned = (
    filtered_fellows["Assigned Mentor"].notna().sum()
    if "Assigned Mentor" in filtered_fellows.columns else 0
)

st.markdown("## Key Metrics")

# Row 1
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Responses", f"{total_rows:,}")
c2.metric("Total Fellows", f"{total_fellows:,}")
c3.metric("Completion Rate", f"{completion_rate}%" if completion_rate is not None else "N/A")
c4.metric("Total Mentors", f"{total_mentors:,}")
c5.metric("Total Mentees Assigned", f"{total_mentees_assigned:,}")

st.markdown("---")

# Row 2
c6, c7 = st.columns(2)
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
    fig_state.update_layout(xaxis_tickangle=-35, height=600)

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

    fig_tier.update_traces(texttemplate="%{text}%", textposition="outside")
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
# MENTOR SUMMARY
# =========================
st.subheader("Mentor Summary")

if not filtered_fellows.empty and "Assigned Mentor" in filtered_fellows.columns:
    mentor_summary = (
        filtered_fellows.dropna(subset=["Assigned Mentor"])
        .groupby(
            [
                "Assigned Mentor",
                "Assigned Mentor State",
                "Assigned Mentor Region",
                "Primary Sector"   # 👈 added here
            ],
            dropna=False
        )
        .agg(
            Mentee_Count=("Email", "nunique")
        )
        .reset_index()
        .sort_values("Mentee_Count", ascending=False)
    )

    st.dataframe(mentor_summary, use_container_width=True)
else:
    st.info("No mentor data available for the selected filters.")




st.subheader("Mentee Sector Distribution")

if not filtered_fellows.empty and "Primary Sector" in filtered_fellows.columns:
    
    sector_df = (
        filtered_fellows
        .dropna(subset=["Assigned Mentor", "Primary Sector"])  # only assigned mentees
        ["Primary Sector"]
        .value_counts()
        .reset_index()
    )
    sector_df.columns = ["Primary Sector", "Mentee_Count"]

    fig_sector = px.pie(
        sector_df,
        names="Primary Sector",
        values="Mentee_Count",
        hole=0.4  # optional donut style
    )

    st.plotly_chart(fig_sector, use_container_width=True)
    st.dataframe(sector_df, use_container_width=True)

else:
    st.info("No sector data available.")




# =========================
# MENTEES UNDER SELECTED MENTOR
# =========================
st.subheader("Mentees Under Mentor")

if selected_mentor != "All":
    mentor_mentees = filtered_fellows.copy()

    mentee_cols = [
        "Assigned Mentor", "Full Name", "Email", "Gender", "Region", "State",
        "Primary Sector", "Secondary Sector", "Placement Tier",
        "Overall Average", "Assigned Mentor State", "Assigned Mentor Region", "Match Type"
    ]
    mentee_cols = [c for c in mentee_cols if c in mentor_mentees.columns]

    st.markdown(f"**Selected Mentor:** {selected_mentor}")
    st.dataframe(
        mentor_mentees[mentee_cols].sort_values("Overall Average", ascending=False),
        use_container_width=True
    )

elif not filtered_fellows.empty and "Assigned Mentor" in filtered_fellows.columns:
    st.info("Select a mentor from the sidebar to see the mentees under that mentor.")
else:
    st.info("No mentor data available.")

# =========================
# FILTERED FELLOW LIST
# =========================
st.subheader("Filtered Fellow List")

display_cols = [
    "Full Name", "Email", "Gender", "Region", "State",
    "Primary Sector", "Secondary Sector", "Placement Tier",
    "Overall Average", "Assigned Mentor", "Assigned Mentor State",
    "Assigned Mentor Region", "Match Type"
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