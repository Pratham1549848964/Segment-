import streamlit as st
import pandas as pd

# ================== File Upload ==================
st.title("Agent Performance Dashboard")

uploaded_files = st.file_uploader("Upload Excel Files (June, July, August)", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    months = ["June", "July", "August"]
    dfs = {}

    for month, file in zip(months, uploaded_files):
        df = pd.read_excel(file, sheet_name="Agent Wise", header=1)
        df.columns = df.columns.str.strip()
        dfs[month] = df

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

                # ✅ Always sort by Ecode ascending
                subset = subset.sort_values(by="Ecode", ascending=True)

                results[month] = subset[["Ecode", "Employee Name", "Status", "Ageing"] + extra_cols +
                                        ["Process_Final", "Leads", "Bkgs", "APE", "ATS", "Con.%", "APE/Leads"]]
        return results

    # ================== Mode Selection ==================
    mode = st.selectbox("Select Mode:", [
        "Agent-wise", "Process-wise", "1st Reporting-wise",
        "2nd Reporting-wise", "Manager-wise", "Ageing-wise"
    ])

    # ======== Agent-wise ========
    if mode == "Agent-wise":
        ecode = st.text_input("Enter Ecode:")
        if st.button("Show Results"):
            results = {}
            for sheet, df in dfs.items():
                agent_data = df[df["Ecode"].astype(str) == ecode]
                if not agent_data.empty:
                    agent_data = agent_data[["Ecode", "Employee Name", "Status", "Ageing",
                                             "Process_Final", "Leads", "Bkgs", "APE", "ATS", "Con.%", "APE/Leads"]]
                    agent_data = format_columns(agent_data)
                    agent_data = agent_data.sort_values(by="Ecode", ascending=True)
                    results[sheet] = agent_data
            if results:
                for m, r in results.items():
                    st.subheader(f"{m}")
                    st.dataframe(r)
            else:
                st.warning("No data found for this Ecode.")

    # ======== Process-wise ========
    elif mode == "Process-wise":
        selected = st.multiselect("Select Process(es):", all_processes)
        if st.button("Show Results"):
            if not selected:
                st.warning("Please select at least one process.")
            else:
                august_data = dfs["August"][dfs["August"]["Process_Final"].isin(selected)]
                ecodes = august_data["Ecode"].astype(str).unique().tolist()
                results = filter_and_show(ecodes)
                if results:
                    for m, r in results.items():
                        st.subheader(f"{m}")
                        st.dataframe(r)
                else:
                    st.warning("No data found for these processes.")

    # ======== 1st Reporting-wise ========
    elif mode == "1st Reporting-wise":
        selected = st.multiselect("Select 1st Reporting Head(s):", all_reporting_1)
        if st.button("Show Results"):
            if not selected:
                st.warning("Please select at least one reporting head.")
            else:
                august_data = dfs["August"][dfs["August"]["1st Reporting"].isin(selected)]
                ecodes = august_data["Ecode"].astype(str).unique().tolist()
                results = filter_and_show(ecodes, extra_cols=["1st Reporting"])
                if results:
                    for m, r in results.items():
                        st.subheader(f"{m}")
                        st.dataframe(r)
                else:
                    st.warning("No data found for these reporting heads.")

    # ======== 2nd Reporting-wise ========
    elif mode == "2nd Reporting-wise":
        selected = st.multiselect("Select 2nd Reporting Head(s):", all_reporting_2)
        if st.button("Show Results"):
            if not selected:
                st.warning("Please select at least one reporting head.")
            else:
                august_data = dfs["August"][dfs["August"]["2nd Reporting"].isin(selected)]
                ecodes = august_data["Ecode"].astype(str).unique().tolist()
                results = filter_and_show(ecodes, extra_cols=["2nd Reporting"])
                if results:
                    for m, r in results.items():
                        st.subheader(f"{m}")
                        st.dataframe(r)
                else:
                    st.warning("No data found for these reporting heads.")

    # ======== Manager-wise ========
    elif mode == "Manager-wise":
        selected = st.multiselect("Select Manager(s):", all_managers)
        if st.button("Show Results"):
            if not selected:
                st.warning("Please select at least one manager.")
            else:
                august_data = dfs["August"][dfs["August"]["Manager"].isin(selected)]
                ecodes = august_data["Ecode"].astype(str).unique().tolist()
                results = filter_and_show(ecodes, extra_cols=["Manager"])
                if results:
                    for m, r in results.items():
                        st.subheader(f"{m}")
                        st.dataframe(r)
                else:
                    st.warning("No data found for these managers.")

    # ======== Ageing-wise ========
    elif mode == "Ageing-wise":
        selected = st.multiselect("Select Ageing Bucket(s):", all_ageing)
        if st.button("Show Results"):
            if not selected:
                st.warning("Please select at least one ageing bucket.")
            else:
                august_data = dfs["August"][dfs["August"]["Ageing"].isin(selected)]
                ecodes = august_data["Ecode"].astype(str).unique().tolist()
                results = filter_and_show(ecodes)
                if results:
                    for m, r in results.items():
                        st.subheader(f"{m}")
                        st.dataframe(r)
                else:
                    st.warning("No data found for these ageing buckets.")
