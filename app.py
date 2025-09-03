import streamlit as st
import pandas as pd

# ================== Streamlit Setup ==================
st.set_page_config(page_title="Agent Performance Dashboard", layout="wide")
st.title("📊 Agent Performance Dashboard")

# ================== File Upload ==================
june_file = st.file_uploader("Upload June Excel File", type=["xlsx"])
july_file = st.file_uploader("Upload July Excel File", type=["xlsx"])
august_file = st.file_uploader("Upload August Excel File", type=["xlsx"])

if june_file and july_file and august_file:
    months = ["June", "July", "August"]
    file_paths = [june_file, july_file, august_file]

    dfs = {}
    for month, file in zip(months, file_paths):
        df = pd.read_excel(file, sheet_name="Agent Wise", header=1)
        df.columns = df.columns.str.strip()
        dfs[month] = df

    # ================== Unique Dropdown Options ==================
    all_processes = dfs["August"]["Process_Final"].dropna().unique().tolist()
    all_reporting_1 = dfs["August"]["1st Reporting"].dropna().unique().tolist()
    all_reporting_2 = dfs["August"]["2nd Reporting"].dropna().unique().tolist()
    all_managers = dfs["August"]["Manager"].dropna().unique().tolist()
    all_ageing = dfs["August"]["Ageing"].dropna().unique().tolist()

    # ================== Helper Functions ==================
    def format_columns(df):
        df = df.copy()
        for col in ["APE", "ATS", "APE/Leads"]:
            if col in df.columns:
                df[col] = df[col].round(0).astype(int)
        if "Con.%" in df.columns:
            df["Con.%"] = (df["Con.%"] * 100).round(1)
        return df

    # ================== Caching ==================
    @st.cache_data
    def create_ecode_lookup(dfs):
        lookup = {}
        for month, df in dfs.items():
            lookup[month] = df.set_index("Ecode")
        return lookup

    ecode_lookup = create_ecode_lookup(dfs)

    # ================== Optimized Filter & Merge ==================
    def fast_filter_and_merge(ecodes, extra_cols=[]):
        merged = None
        ageing_map = dfs["August"].set_index("Ecode")["Ageing"].to_dict()

        for month in months:
            df = ecode_lookup[month]
            subset = df.loc[df.index.intersection(ecodes)].copy()
            if not subset.empty:
                base_cols = ["Employee Name", "Status", "Process_Final", "Leads", "Bkgs", "APE", "ATS", "Con.%", "APE/Leads"]
                subset = subset[base_cols]
                for col in extra_cols:
                    if col in df.columns:
                        subset[col] = df.loc[subset.index, col]
                subset["Ageing"] = subset.index.map(ageing_map)
                subset = format_columns(subset)

                rename_map = {col: f"{month}_{col}" for col in subset.columns if col not in ["Ageing", "Employee Name", "Status"]}
                subset = subset.rename(columns=rename_map)
                subset = subset.reset_index().rename(columns={"Ecode": "Ecode"})

                if merged is None:
                    merged = subset
                else:
                    merged = pd.merge(merged, subset, on=["Ecode", "Employee Name", "Status", "Ageing"], how="outer")

        if merged is not None:
            merged = merged.sort_values(by="Ecode").reset_index(drop=True)
        return merged

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
            results = fast_filter_and_merge(ecodes)
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
            results = fast_filter_and_merge(ecodes)
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
            results = fast_filter_and_merge(ecodes, extra_cols=["1st Reporting"])
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
            results = fast_filter_and_merge(ecodes, extra_cols=["2nd Reporting"])
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
            results = fast_filter_and_merge(ecodes, extra_cols=["Manager"])
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
            results = fast_filter_and_merge(ecodes)
            if results is not None and not results.empty:
                st.dataframe(results)
            else:
                st.warning("No data found for these ageing buckets.")



