import pandas as pd
import streamlit as st

# ========== App Title ==========
st.set_page_config(page_title="Performance Dashboard", layout="wide")
st.title("📊 Performance Dashboard")
st.write("Upload June, July, and August Excel files to analyze performance.")

# ========== File Upload ==========
june_file = st.file_uploader("Upload June.xlsx", type="xlsx")
july_file = st.file_uploader("Upload July.xlsx", type="xlsx")
august_file = st.file_uploader("Upload August.xlsx", type="xlsx")

if june_file and july_file and august_file:
    months = ["June", "July", "August"]
    files = [june_file, july_file, august_file]

    dfs = {}
    for month, f in zip(months, files):
        df = pd.read_excel(f, sheet_name="Agent Wise", header=1)
        df.columns = df.columns.str.strip()
        dfs[month] = df

    # Unique dropdown values
    all_processes = dfs["August"]["Process_Final"].dropna().unique().tolist()
    all_reporting = dfs["August"]["1st Reporting"].dropna().unique().tolist()
    all_reporting2 = dfs["August"]["2nd Reporting"].dropna().unique().tolist()
    all_manager = dfs["August"]["Manager"].dropna().unique().tolist()
    all_ageing = [
        val for val in dfs["August"]["Ageing"].dropna().unique().tolist()
        if isinstance(val, str) and ("M" in val or "Above" in val)
    ]

    # ========== Helper ==========
    def format_columns(df):
        df = df.copy()
        for col in ["APE", "ATS", "APE/Leads"]:
            if col in df.columns:
                df[col] = df[col].round(0).astype(int)
        if "Con.%" in df.columns:
            df["Con.%"] = (df["Con.%"] * 100).round(1)
        return df

    def filter_and_show(ecodes, extra_cols=[]):
        results = {}
        august_data = dfs["August"][dfs["August"]["Ecode"].astype(str).isin(ecodes)]
        ageing_map = august_data.set_index("Ecode")["Ageing"].to_dict()

        for month in months:
            df = dfs[month]
            subset = df[df["Ecode"].astype(str).isin(ecodes)].copy()
            if not subset.empty:
                base_cols = ["Ecode", "Employee Name", "Status", "Process_Final",
                             "Leads", "Bkgs", "APE", "ATS", "Con.%", "APE/Leads"]
                subset = subset[base_cols]
                for col in extra_cols:
                    if col in df.columns:
                        subset[col] = df.loc[subset.index, col]
                subset["Ageing"] = subset["Ecode"].map(ageing_map)
                subset = format_columns(subset)
                results[month] = subset[["Ecode", "Employee Name", "Status", "Ageing"] + extra_cols +
                                        ["Process_Final", "Leads", "Bkgs", "APE", "ATS", "Con.%", "APE/Leads"]]
        return results

    # ========== Mode Selection ==========
    mode = st.selectbox("Select Mode", [
        "Agent-wise", "Process-wise", "1st Reporting-wise",
        "2nd Reporting-wise", "Manager-wise", "Ageing-wise"
    ])

    # Agent-wise
    if mode == "Agent-wise":
        ecode = st.text_input("Enter Ecode")
        if st.button("Show Results") and ecode:
            ecodes = [ecode]
            results = filter_and_show(ecodes)
            if results:
                for m in results:
                    st.subheader(m)
                    st.dataframe(results[m])
            else:
                st.warning("No data found for this Ecode.")

    # Process-wise
    elif mode == "Process-wise":
        selected = st.multiselect("Select Processes", all_processes)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["Process_Final"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = filter_and_show(ecodes)
            if results:
                for m in results:
                    st.subheader(m)
                    st.dataframe(results[m])
            else:
                st.warning("No data found for selected processes.")

    # 1st Reporting-wise
    elif mode == "1st Reporting-wise":
        selected = st.multiselect("Select 1st Reporting", all_reporting)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["1st Reporting"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = filter_and_show(ecodes, extra_cols=["1st Reporting"])
            if results:
                for m in results:
                    st.subheader(m)
                    st.dataframe(results[m])
            else:
                st.warning("No data found for selected reporting.")

    # 2nd Reporting-wise
    elif mode == "2nd Reporting-wise":
        selected = st.multiselect("Select 2nd Reporting", all_reporting2)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["2nd Reporting"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = filter_and_show(ecodes, extra_cols=["2nd Reporting"])
            if results:
                for m in results:
                    st.subheader(m)
                    st.dataframe(results[m])
            else:
                st.warning("No data found for selected reporting.")

    # Manager-wise
    elif mode == "Manager-wise":
        selected = st.multiselect("Select Manager", all_manager)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["Manager"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = filter_and_show(ecodes, extra_cols=["Manager"])
            if results:
                for m in results:
                    st.subheader(m)
                    st.dataframe(results[m])
            else:
                st.warning("No data found for selected managers.")

    # Ageing-wise
    elif mode == "Ageing-wise":
        selected = st.multiselect("Select Ageing Buckets", all_ageing)
        if st.button("Show Results") and selected:
            august_data = dfs["August"][dfs["August"]["Ageing"].isin(selected)]
            ecodes = august_data["Ecode"].astype(str).unique().tolist()
            results = filter_and_show(ecodes)
            if results:
                for m in results:
                    st.subheader(m)
                    st.dataframe(results[m])
            else:
                st.warning("No data found for selected ageing buckets.")
