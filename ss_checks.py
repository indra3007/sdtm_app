# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 10:28:16 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os
import plotly.express as px
from dash import dcc
from datetime import datetime
def check_ss_ssdtc_alive_dm(data_path):
    check_description = "Check for ALIVE status date in SS domain later than death date in DM domain"
    datasets = "SS, DM"
    ss_file_path = os.path.join(data_path, "ss.sas7bdat")

    if not os.path.exists(ss_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to SS dataset not found at the specified location: {ss_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    dm_file_path = os.path.join(data_path, "dm.sas7bdat")

    if not os.path.exists(dm_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to DM dataset not found at the specified location: {dm_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    SS = load_data(data_path, 'ss')
    required_ss_columns = ["USUBJID", "SSDTC", "SSORRES", "SSTESTCD", "VISIT"]

    # Check if required variables exist in QS
    if not set(required_ss_columns).issubset(SS.columns):
        missing = set(required_ss_columns) - set(SS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in SS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    DM = load_data(data_path, 'dm')
    required_dm_columns = ["USUBJID", "DTHDTC"]
    
    if not set(required_dm_columns).issubset(DM.columns):
        missing = set(required_dm_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Filter SS and DM dataframes
    myss = SS.loc[(~SS["SSDTC"].apply(is_null_or_empty)) & (SS["SSTESTCD"] == "SURVSTAT") & (SS["SSORRES"].str.contains("ALIVE", na=False)), ["USUBJID", "SSDTC", "SSORRES", "SSTESTCD", "VISIT"]]
    mydm = DM.loc[(~DM["DTHDTC"].apply(is_null_or_empty)), ["USUBJID", "DTHDTC"]]

    # Merge and filter dataframes
    mydf = pd.merge(myss, mydm, on="USUBJID", how="left")
    mydf["SSDTC"] = pd.to_datetime(mydf["SSDTC"], errors="coerce")
    mydf["DTHDTC"] = pd.to_datetime(mydf["DTHDTC"], errors="coerce")
    mydf = mydf.loc[mydf["SSDTC"] > mydf["DTHDTC"]]

    # Check if there are any records where SS.SSDTC > DM.DTHDTC
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"{len(mydf['USUBJID'].unique())} patient(s) with ALIVE status date in SS domain later than death date in DM domain.", mydf.reset_index(drop=True))
def check_ss_ssdtc_dead_ds(data_path, preproc=lambda df: df, **kwargs):
    ss_file_path = os.path.join(data_path, "ss.sas7bdat")
    ds_file_path = os.path.join(data_path, "ds.sas7bdat")
    datasets = "SS, DS"
    
    if os.path.exists(ss_file_path):
        SS = load_data(data_path, 'ss')
    else:
        return pd.DataFrame({
            "CHECK": ["Check SS SSDTC and DS consistency"],
            "Message": [f"Check stopped running due to SS dataset not found at the specified location: {ss_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    if os.path.exists(ds_file_path):
        DS = load_data(data_path, 'ds')
    else:
        return pd.DataFrame({
            "CHECK": ["Check SS SSDTC and DS consistency"],
            "Message": [f"Check stopped running due to DS dataset not found at the specified location: {ds_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    required_ss_columns = ["USUBJID", "SSDTC", "SSSTRESC", "VISIT"]
    required_ds_columns = ["USUBJID", "DSSTDTC", "DSDECOD", "DSCAT"]

    # Check if required variables exist in SS
    if not set(required_ss_columns).issubset(SS.columns):
        missing = set(required_ss_columns) - set(SS.columns)
        return pd.DataFrame({
            "CHECK": ["Check SS SSDTC and DS consistency"],
            "Message": [f"Missing columns in SS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Check if required variables exist in DS
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check SS SSDTC and DS consistency"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    DS = preproc(DS, **kwargs)
    SS = preproc(SS, **kwargs)

   
    myss = SS.loc[(~SS["SSDTC"].isna()) & (SS["SSSTRESC"].str.upper() == 'DEAD'), ["USUBJID", "SSDTC", "SSSTRESC", "VISIT"]]
    myds = DS.loc[(~DS["DSSTDTC"].isna()) & (DS["DSDECOD"].str.upper() == 'DEATH') & (DS["DSCAT"].str.upper() == "DISPOSITION EVENT"), ["USUBJID", "DSSTDTC", "DSDECOD", "DSCAT"]]

    mydf = pd.merge(myss, myds, on="USUBJID", how="left")
    mydf = mydf.loc[(mydf["DSSTDTC"].isna()) | (mydf["SSDTC"] < mydf["DSSTDTC"])]

    check_description = "Check SS SSDTC and DS consistency"

    # Return message if no records
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        notes = f"{mydf['USUBJID'].nunique()} patient(s) with death information in SS domain but no death information in DS domain or date with DEAD status in SS dataset is less than death date in DS dataset."
        return fail_check(check_description, datasets, notes, mydf)
def check_ss_ssdtc_dead_dthdtc(data_path):
    check_description = "Check for SS records with DEAD status and SS date before death date in DM"
    datasets = "SS, DM"
    ss_file_path = os.path.join(data_path, "ss.sas7bdat")

    if not os.path.exists(ss_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to SS dataset not found at the specified location: {ss_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    dm_file_path = os.path.join(data_path, "dm.sas7bdat")

    if not os.path.exists(dm_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to DM dataset not found at the specified location: {dm_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    SS = load_data(data_path, 'ss')
    required_ss_columns = ["USUBJID", "SSDTC", "SSSTRESC", "VISIT"]

    # Check if required variables exist in QS
    if not set(required_ss_columns).issubset(SS.columns):
        missing = set(required_ss_columns) - set(SS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in SS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    DM = load_data(data_path, 'dm')
    required_dm_columns = ["USUBJID", "DTHDTC"]
    
    if not set(required_dm_columns).issubset(DM.columns):
        missing = set(required_dm_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    myss = SS.loc[(~SS["SSDTC"].isna()) & (SS["SSSTRESC"].str.upper() == 'DEAD'), ["USUBJID", "SSDTC", "SSSTRESC", "VISIT"]]
    mydm = DM.loc[(~DM["DTHDTC"].isna()), ["USUBJID", "DTHDTC"]]
    mydf = pd.merge(myss, mydm, on="USUBJID", how="left")
    mydf = mydf.loc[(~mydf["DTHDTC"].isna()) & (mydf["SSDTC"] < mydf["DTHDTC"])]

    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        message = f"{mydf['USUBJID'].nunique()} patient(s) with DEAD status in SS domain where SS date is less than death date in DM domain."
        return fail_check(check_description, datasets, message, mydf)
def check_ss_ssstat_ssorres(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for SS records with SSSTAT='NOT DONE' but non-missing SSORRES"
    datasets = "SS"
    ss_file_path = os.path.join(data_path, "ss.sas7bdat")

    if not os.path.exists(ss_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to SS dataset not found at the specified location: {ss_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    SS = load_data(data_path, 'ss')
    # First check that required variables exist and return a message if they don't
    required_columns = ["USUBJID", "SSORRES", "VISIT", "SSSTAT", "SSDTC"]
    if not set(required_columns).issubset(SS.columns):
        missing = set(required_columns) - set(SS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in SS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    SS = preproc(SS, **kwargs)

    mydf = SS.loc[(SS["SSSTAT"] == "NOT DONE") & (~SS["SSORRES"].apply(is_null_or_empty)),
                  ["USUBJID", "VISIT", "SSDTC", "SSORRES", "SSSTAT"]]

    mydf = mydf.drop_duplicates().sort_values(by=["USUBJID", "SSDTC", "VISIT"]).reset_index(drop=True)

    # Print to report
    # Return message if no records with issue in SS
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        message = f"SS (LTFU) has {len(mydf)} record(s) for {mydf['USUBJID'].nunique()} unique patient(s) with non-missing SSORRES when SSSTAT=NOT DONE (no contact)."
        return fail_check(check_description, datasets, message, mydf)
def surv_dist(data_path):
    ss_file_path = os.path.join(data_path, "ss.sas7bdat")
    dm_file_path = os.path.join(data_path, "dm.sas7bdat")

    # Check if both SS and DM datasets exist
    if not os.path.exists(ss_file_path) or not os.path.exists(dm_file_path):
        return pd.DataFrame({
            "CHECK": ["Survival Status Distribution"],
            "Message": [f"SS or DM dataset not found at the specified location: {ss_file_path} or {dm_file_path}"],
            "Notes": [""],
            "Datasets": [["SS", "DM"]],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    # Load data
    ss_data = load_data(data_path, 'ss')
    dm_data = load_data(data_path, 'dm')

    # Filter SS data for survival status
    ss_data = ss_data.loc[(ss_data["SSTESTCD"] == "SURVSTAT")]
    ss_data['SSORRES'] = ss_data['SSORRES'].fillna('MISSING')
    # Merge with DM to include all subjects
    merged_data = pd.merge(dm_data[['USUBJID']], ss_data, on='USUBJID', how='left')

    # Count subjects by survival status
    survival_counts = merged_data['SSORRES'].value_counts(dropna=False).reset_index()
    survival_counts.columns = ['SSORRES', 'Count']  # Rename columns for clarity

    # Calculate total subjects for pie chart
    survival_counts['Percentage'] = (survival_counts['Count'] / len(dm_data)) * 100

    # Pie Chart
    fig = px.pie(
        survival_counts,
        names='SSORRES',
        values='Count',
        title='Survival Status Distribution',
        hole=0.4
    )
    fig.update_traces(textinfo='percent+label', pull=[0.1 if ss == "DEAD" else 0 for ss in survival_counts['SSORRES']])

    # Return the figure as a Dash Graph component
    return [dcc.Graph(figure=fig)]