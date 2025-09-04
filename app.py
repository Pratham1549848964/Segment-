import streamlit as st
import pandas as pd
import traceback

# ================== Streamlit Setup ==================
st.set_page_config(page_title="Agent Performance Dashboard", layout="wide")

# ================== Custom CSS ==================
st.markdown(
    """
    <style>
    /* Main background */
    .main {
        background-color: #f8f9fa;
    }
    /* Navbar */
    .navbar {
        background-color: #1f2937;
        padding: 15px 30px;
        border-radius: 10px;
        margin-bottom: 25px;
    }
    .navbar h1 {
        color: white !important;
        font-size: 28px !important;
        text-align: center;
    }
    /* File uploader + filters as cards */
    .stFileUploader, .stSelectbox, .stMultiSelect, .stTextInput {
        background: white;
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.1);
        margin-bottom: 12px;
    }
    /* Buttons */
    .stButton>button {
        background: #2563eb;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 20px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #1e40af;
        transform: translateY(-2px);
    }
    /* Dataframe card */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ================== Navbar ==================
st.markdown('<div class="navbar"><h1>📊 Agent Performance Dashboard</h1></div>', unsafe_allow_html=True)

# ================== File Upload ==================
st.sidebar.header("📂 Upload Files")
june_file = st.sidebar.file_uploader("Upload June Excel File", type=["xlsx"])
july_file = st.sidebar.file_uploader("Upload July Excel File", type=["xlsx"])
august_file = st.sidebar.file_uploader("Upload August Excel File", type=["xlsx"])

# ================== Cached Functions ==================
@st.cache_data
def load_excel(file):
    df = pd.read_excel(file, sheet_name="Agent Wise", header=1)
    df.columns = df.columns.str.strip()
    return df

@st.cache_data
def get_dropdown_options(df):
    return {
        "processes": df["Process_Final"].dropna().unique().tolist(),
        "reporting_1": df["1st Reporting"].dropna().unique().tolist(),
        "reporting_2": df["2nd Reporting"].dropna().unique().tolist(),
        "managers": df["Manager"].dropna().unique().tolist(),
        "ageing": df["Ageing"].dropna().unique().tolist()
    }

# ================== Main Dashboard ==================
if june_file and july_file and august_file:
    try:
        months = ["June", "July", "August"]
        file_paths = [june_file, july_file, august_file]

        # Load Excel Files (cached)
        dfs = {month: load_excel(file) for month, file in zip(months, file_paths)}

        # Dropdown Options (cached)
        options = get_dropdown_options(dfs["August"])
        all_processes = options["processes"]
        all_reporting_1 = options["reporting_1"]
        all_reporting_2 = options["reporting_2"]
        all_managers = options["managers"]
        all_ageing = options["ageing"]

        # ================== Helper Functions ==================
        def format_columns(df):
            df = df.copy()
            for col in ["APE", "ATS", "APE/Leads"]:
                if col in df.columns:
                    df[col] = df[col].round(0).astype(int)
            if "Con.%" in df.columns:
                df["Con.%"] = (df["Con.%"] * 100).round(1)
            return df

        def filter_and_merge(ecodes, extra_cols=[]):
            august_data = dfs["August"][dfs["August"]["Ecode"].astype(str).isin(ecodes)]
            ageing_map = august_data.set_index("Ecode")["Ageing"].to_dict()

            merged = None
            for month in months:
                df = dfs[month]
                subset = df[df["Ecode"].astype(str).isin(ecodes)].copy()
                if not subset.empty:
                    base_cols = ["Ecode", "Employee Name", "Status",
                                 "Process_Final", "Leads", "Bkgs", "APE", "ATS", "Con.%", "APE/Leads"]
                    subset = subset[base_cols]
                    for col in extra_cols:
                        if col in df.columns:
                            subset[col] = df.loc[subset.index, col]
                    subset["Ageing"] = subset["Ecode"].map(ageing_map)
                    subset = format_columns(subset)

                    rename_map = {
                        col: f"{month}_{col}" for col in subset.columns
                        if col not in ["Ecode", "Employee Name", "Status", "Ageing"]
                    }
                    subset = subset.rename(columns=rename_map)

                    if merged is None:
                        merged = subset
                    else:
                        merged = pd.merge(
                            merged, subset,
                            on=["Ecode", "Employee Name", "Status", "Ageing"],
                            how="outer"
                        )

            if merged is not None:
                merged = merged.sort_values(by="Ecode", ascending=True)
                cols = merged.columns.tolist()
                if "Ageing" in cols:
                    cols.remove("Ageing")
                    status_index = cols.index("Status")
                    cols = cols[:status_index+1] + ["Ageing"] + cols[status_index+1:]
                    merged = merged[cols]
                return merged
            else:
                return None

        # ================== Mode Selection ==================
        st.sidebar.header("⚙️ Filters")
        mode = st.sidebar.selectbox("Select Mode:", [
            "Agent-wise", "Process-wise", "1st Reporting-wise",
            "2nd Reporting-wise", "Manager-wise", "Ageing-wise"
        ])

        # ================== Display Data ==================
        ecode_input = st.text_input("Enter Ecode (for Agent-wise mode):") if mode == "Agent-wise" else None
        selected_multi = None
        if mode in ["Process-wise", "1st Reporting-wise", "2nd Reporting-wise", "Manager-wise", "Ageing-wise"]:
            prompt_dict = {
                "Process-wise": ("Select Process(es):", all_processes),
                "1st Reporting-wise": ("Select 1st Reporting Head(s):", all_reporting_1),
                "2nd Reporting-wise": ("Select 2nd Reporting Head(s):", all_reporting_2),
                "Manager-wise": ("Select Manager(s):", all_managers),
                "Ageing-wise": ("Select Ageing Bucket(s):", all_ageing)
            }
            prompt, options_list = prompt_dict[mode]
            selected_multi = st.multiselect(prompt, options_list)

        if st.button("Show Results"):
            try:
                ecodes = []
                extra_cols = []

                if mode == "Agent-wise" and ecode_input:
                    ecodes = [ecode_input]
                elif mode == "Process-wise" and selected_multi:
                    august_data = dfs["August"][dfs["August"]["Process_Final"].isin(selected_multi)]
                    ecodes = august_data["Ecode"].astype(str).unique().tolist()
                elif mode == "1st Reporting-wise" and selected_multi:
                    august_data = dfs["August"][dfs["August"]["1st Reporting"].isin(selected_multi)]
                    ecodes = august_data["Ecode"].astype(str).unique().tolist()
                    extra_cols = ["1st Reporting"]
                elif mode == "2nd Reporting-wise" and selected_multi:
                    august_data = dfs["August"][dfs["August"]["2nd Reporting"].isin(selected_multi)]
                    ecodes = august_data["Ecode"].astype(str).unique().tolist()
                    extra_cols = ["2nd Reporting"]
                elif mode == "Manager-wise" and selected_multi:
                    august_data = dfs["August"][dfs["August"]["Manager"].isin(selected_multi)]
                    ecodes = august_data["Ecode"].astype(str).unique().tolist()
                    extra_cols = ["Manager"]
                elif mode == "Ageing-wise" and selected_multi:
                    august_data = dfs["August"][dfs["August"]["Ageing"].isin(selected_multi)]
                    ecodes = august_data["Ecode"].astype(str).unique().tolist()

                if ecodes:
                    results = filter_and_merge(ecodes, extra_cols)
                    if results is not None and not results.empty:
                        st.subheader("📋 Results")
                        st.dataframe(results.style.highlight_max(axis=0, color="lightgreen"))
                    else:
                        st.warning("⚠️ No data found for the selected input.")
                else:
                    st.warning("⚠️ Please provide input or select at least one option.")
            except Exception as e:
                st.error(f"Error while processing data: {e}")
                st.text(traceback.format_exc())

    except Exception as e:
        st.error(f"Error loading files or initializing dashboard: {e}")
        st.text(traceback.format_exc())
