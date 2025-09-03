import streamlit as st
import pandas as pd

# ================== Streamlit Setup ==================
st.set_page_config(page_title="Agent Performance Dashboard", layout="wide")
st.title("📊 Agent Performance Dashboard")

# ================== File Upload ==================
june_file = st.file_uploader("Upload June Excel File", type=["xlsx"])
july_file = st.file_uploader("Upload July Excel File", type=["xlsx"])
august_file = st.file_uploader("Upload August Excel File", type=["xlsx"])

# ================== Cache: Load Excel ==================
@st.cache_data
def load_excel(file):
    df = pd.read_excel(file, sheet_name="Agent Wise", header=1)
    df.columns = df.columns.str.strip()
    return df

# ================== Cache: Get Dropdown Options ==================
@st.cache_data
def get_dropdown_options(df):
    return {
        "processes": df["Process_Final"].dropna().unique().tolist(),
        "reporting_1": df["1st Reporting"].dropna().unique().tolist(),
        "reporting_2": df["2nd Reporting"].dropna().unique().tolist(),
        "managers": df["Manager"].dropna().unique().tolist(),
        "ageing": df["Ageing"].dropna().unique().tolist()
    }

# ================== Cache: Filter & Merge ==================
@st.cache_data
def cached_filter_and_merge(ecodes, extra_cols=[]):
    return filter_and_merge(ecodes, extra_cols)

if june_file and july_file and august_file:
    months = ["June", "July", "August"]
    file_paths = [june_file, july_file, august_file]

    # ================== Load Excel Files (Cached) ==================
    dfs = {month: load_excel(file) for month, file in zip(months, file_paths)}

    # ================== Dropdown Options (Cached) ==================
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

                # ✅ Rename with month prefix
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
    mode = st.selectbox("Select Mode:", [
        "Agent-wise", "Process-wise", "1st Reporting-wise",
        "2nd Reporting-wise", "Manager-wise", "Ageing-wise"
    ])

    # ======== Agent-wise ========
    if mode == "Agent-wise":
        ecode = st.text_input("Enter Ecode:")
        if st.button("Show Results") and ecode:
            ecodes = [ecode]
            results = cached_filter_and_merge(ecodes)
            if results is not None and not results.empty:
                st.dataframe(results)
            else:
                st.warning("No data found for this Ecode.")

    # ======== Process-wise ========
    elif mode == "Process-wise":
        selected = st.multiselect("Select Process(es):", all_processes)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["Process_Final"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = cached_filter_and_merge(ecodes)
            if results is not None and not results.empty:
                st.dataframe(results)
            else:
                st.warning("No data found for these processes.")

    # ======== 1st Reporting-wise ========
    elif mode == "1st Reporting-wise":
        selected = st.multiselect("Select 1st Reporting Head(s):", all_reporting_1)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["1st Reporting"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = cached_filter_and_merge(ecodes, extra_cols=["1st Reporting"])
            if results is not None and not results.empty:
                st.dataframe(results)
            else:
                st.warning("No data found for these reporting heads.")

    # ======== 2nd Reporting-wise ========
    elif mode == "2nd Reporting-wise":
        selected = st.multiselect("Select 2nd Reporting Head(s):", all_reporting_2)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["2nd Reporting"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = cached_filter_and_merge(ecodes, extra_cols=["2nd Reporting"])
            if results is not None and not results.empty:
                st.dataframe(results)
            else:
                st.warning("No data found for these reporting heads.")

    # ======== Manager-wise ========
    elif mode == "Manager-wise":
        selected = st.multiselect("Select Manager(s):", all_managers)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["Manager"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = cached_filter_and_merge(ecodes, extra_cols=["Manager"])
            if results is not None and not results.empty:
                st.dataframe(results)
            else:
                st.warning("No data found for these managers.")

    # ======== Ageing-wise ========
    elif mode == "Ageing-wise":
        selected = st.multiselect("Select Ageing Bucket(s):", all_ageing)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["Ageing"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = cached_filter_and_merge(ecodes)
            if results is not None and not results.empty:
                st.dataframe(results)
            else:
                st.warning("No data found for these ageing buckets.")




