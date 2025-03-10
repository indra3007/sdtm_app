# -*- coding: utf-8 -*-
"""
Created on Thu Aug  1 10:11:48 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month, convert_date, format_dates
import os
import plotly.express as px
from dash import dcc

def check_sv_svstdtc_visit_ordinal_error(data_path):
    check_description = "Check for SV entries with SVSTDTC Visit Ordinal Error"
    datasets = "SV"
    qs_file_path = os.path.join(data_path, "sv.sas7bdat")
    if  os.path.exists(qs_file_path):
        SV = load_data(data_path, 'sv')
        required_sv_columns = ["USUBJID", "VISITNUM", "VISIT", "SVSTDTC"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to SV dataset not found at the specified location: {qs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    # First check that required variables exist and return a message if they don't
    if not set(required_sv_columns).issubset(SV.columns):
        missing = set(required_sv_columns) - set(SV.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in SV: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Don't run if VISITNUM is all missing
    if SV["VISITNUM"].nunique() <= 1:
        return fail_check(check_description, datasets, "VISITNUM exists but only a single value.")

    # Only keep records not indicated as NOT DONE and drop Unscheduled and Tx Discon visits
    #subset_df = QS[(QS["QSSTAT"] != "NOT DONE") & (~QS["VISIT"].str.contains("UNSCHEDU|TREATMENT OR OBSERVATION FU COMP EARLY DISC", case=False))]
    subset_df = SV.copy()
    if subset_df.empty:
        return fail_check(check_description, datasets, "No SV records when subset to exclude NOT DONE.")
    
    # Remove duplicates and sort by USUBJID, VISITNUM, and QSDTC
    subset_df = subset_df.drop_duplicates(subset=["USUBJID", "VISITNUM", "SVSTDTC"])
    subset_df = subset_df.sort_values(by=["USUBJID", "VISITNUM", "SVSTDTC"]).reset_index(drop=True)

    # Check for QSDTC order within VISITNUM
    #subset_df = convert_date(subset_df, "SVSTDTC")
    subset_df["SVSTDTC"] = subset_df["SVSTDTC"].apply(format_dates)
    #subset_df["SVSTDTC"] = pd.to_datetime(subset_df["SVSTDTC"], errors='coerce')
    #subset_df['SVSTDTC'] = subset_df['SVSTDTC'].apply(lambda x: pd.to_datetime(x, errors='coerce') if isinstance(x, str) and len(x) == 10 else x)

    # Ensure all dates are in the correct format
    #subset_df['SVSTDTC'] = subset_df['SVSTDTC'].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, pd.Timestamp) else x)
    subset_df["DTC_order"] = subset_df.groupby("USUBJID")["SVSTDTC"].rank(method="first", ascending=True)
    subset_df["Vis_order"] = subset_df.groupby("USUBJID")["VISITNUM"].rank(method="first", ascending=True)

    # Subset if Vis_order not equal to DTC_order
    myout = subset_df[subset_df["DTC_order"] != subset_df["Vis_order"]]
    
    # Add sorting
    myout = myout.sort_values(by=["USUBJID", "VISITNUM", "SVSTDTC"]).reset_index(drop=True)
    

        # Return message if no records with QSDTC per VISITNUM
    if myout.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"SV has {len(myout)} record(s) with Possible SVSTDTC data entry error.", myout)
def check_sv_dupc_visit(data_path):
    check_description = "Check for duplicate records in SV"
    datasets = "SV"
    qs_file_path = os.path.join(data_path, "sv.sas7bdat")
    if  os.path.exists(qs_file_path):
        SV = load_data(data_path, 'sv')
        required_sv_columns = ["USUBJID", "VISITNUM", "VISIT", "SVSTDTC"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to SV dataset not found at the specified location: {qs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    # First check that required variables exist and return a message if they don't
    if not set(required_sv_columns).issubset(SV.columns):
        missing = set(required_sv_columns) - set(SV.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in SV: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Don't run if VISITNUM is all missing
    if SV["VISITNUM"].nunique() <= 1:
        return fail_check(check_description, datasets, "VISITNUM exists but only a single value.")

    # Only keep records not indicated as NOT DONE and drop Unscheduled and Tx Discon visits
    #subset_df = QS[(QS["QSSTAT"] != "NOT DONE") & (~QS["VISIT"].str.contains("UNSCHEDU|TREATMENT OR OBSERVATION FU COMP EARLY DISC", case=False))]

    subset_df = SV[["USUBJID", "VISITNUM", "VISIT", "SVSTDTC"]]
    subset_df = subset_df[subset_df.duplicated(keep=False)]
    

        # Return message if no records with QSDTC per VISITNUM
    if subset_df.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"SV has {len(subset_df)} record(s) with Possible SVSTDTC data entry error.", subset_df)




# 1. Subject Compliance by Visit (Bar Chart)
def subject_compliance_plot(data_path):
    data = load_data(data_path, 'sv')
    compliance = data.groupby(["VISIT","VISITNUM"])["USUBJID"].nunique().reset_index()
    compliance.columns = ["Visit", "VISITNUM" ,"Number of Subjects"]
    compliance = compliance.sort_values("VISITNUM")
    fig = px.bar(
        compliance,
        x="Visit",
        y="Number of Subjects",
        title="Subject Compliance by Visit",
        labels={"Visit": "Visit", "Number of Subjects": "Number of Subjects"},
        text="Number of Subjects",
        category_orders={"Visit": compliance["Visit"].tolist()} 
    )
    return [dcc.Graph(figure=fig)]

# 2. Visit Timing Distribution (Box Plot)
def visit_timing_distribution_plot(data_path):
    data = load_data(data_path, 'sv')
    fig = px.box(
        data,
        x="VISIT",
        y="SVSTDTC",
        title="Visit Timing Distribution",
        labels={"VISIT": "Visit", "SVSTDTC": "Visit Date"},
    )
    return [dcc.Graph(figure=fig)]

# 3. Visit Sequence for Each Subject (Line Plot)
def visit_sequence_plot(data_path):
    data = load_data(data_path, 'sv')
    data = data.sort_values("VISITNUM")
    fig = px.line(
        data,
        x="SVSTDTC",
        y="VISIT",
        color="USUBJID",
        title="Visit Sequence for Each Subject",
        labels={"SVSTDTC": "Visit Date", "VISIT": "Visit", "USUBJID": "Subject ID"},
        markers=True,
        category_orders={"VISIT": data["VISIT"].unique()}
    )
    return [dcc.Graph(figure=fig)]

# 4. Cumulative Visit Completion Over Time (Line Plot)
def cumulative_visit_completion_plot(data_path):
    data = load_data(data_path, 'sv')
    data['Cumulative_Visits'] = data.groupby("SVSTDTC")["USUBJID"].transform('count').cumsum()

    fig = px.line(
        data,
        x="SVSTDTC",
        y="Cumulative_Visits",
        title="Cumulative Visit Completion Over Time",
        labels={"SVSTDTC": "Visit Date", "Cumulative_Visits": "Cumulative Visits"}
    )
    return [dcc.Graph(figure=fig)]

def subject_dropout_analysis_plot(data_path):
    # Load SV data
    data = load_data(data_path, 'sv')

    # Ensure necessary columns exist
    if "USUBJID" not in data.columns or "VISITNUM" not in data.columns:
        return html.Div("Required columns 'USUBJID' or 'VISITNUM' not found in the dataset.")

    # Create DROPOUT_FLAG based on missing visits
    data = data.sort_values(by=["USUBJID", "VISITNUM"])  # Ensure sorted by subject and visit number
    data["DROPOUT_FLAG"] = data.groupby("USUBJID")["VISITNUM"].transform(
        lambda x: x.shift(-1).isna().replace({True: "Yes", False: "No"})
    )

    # Count dropouts per visit
    dropout = data.groupby(["VISIT", "DROPOUT_FLAG"])["USUBJID"].count().reset_index()
    dropout.columns = ["Visit", "Dropout Status", "Number of Subjects"]

    # Plot dropout analysis
    fig = px.bar(
        dropout,
        x="Visit",
        y="Number of Subjects",
        color="Dropout Status",
        title="Dropout Analysis by Visit",
        labels={"Visit": "Visit", "Number of Subjects": "Number of Subjects", "Dropout Status": "Status"},
        category_orders={"Visit": data["VISIT"].unique()}  # Preserve visit order
    )
    return [dcc.Graph(figure=fig)]

    