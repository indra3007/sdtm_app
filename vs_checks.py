# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 14:42:19 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os

def check_vs_height(data_path):
    check_description = "Check for patients in DM with no recorded height at any visit"
    datasets = "VS, DM"
    vs_file_path = os.path.join(data_path, "vs.sas7bdat")

    if not os.path.exists(vs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to VS dataset not found at the specified location: {vs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    VS = load_data(data_path, 'vs')
    dm_file_path = os.path.join(data_path, "dm.sas7bdat")

    if not os.path.exists(dm_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to DM dataset not found at the specified location: {dm_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    DM = load_data(data_path, 'dm')
    # Check if required columns exist in VS
    if not set(["USUBJID", "VSTEST", "VSSTRESN"]).issubset(VS.columns):
        missing = set(["USUBJID", "VSTEST", "VSSTRESN"]) - set(VS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in VS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Check if required columns exist in DM
    if not set(["USUBJID"]).issubset(DM.columns):
        missing = set(["USUBJID"]) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Obtain dataset containing all patients in VS with a valid height
    vs_pats = VS[(VS["VSTEST"].str.upper() == "HEIGHT") & (~VS["VSSTRESN"].isna())][["USUBJID"]]

    # Obtain list of patients in DM
    dm_pats = DM[["USUBJID","ARM","ACTARM"]]

    # Obtain patients in dm_pats who don't appear in vs_pats
    mydf = dm_pats[~dm_pats["USUBJID"].isin(vs_pats["USUBJID"])]
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"{mydf.shape[0]} patient(s) in DM with no recorded height at any visit."
        return fail_check(check_description, datasets, notes, mydf)
    
def check_vs_sbp_lt_dbp(data_path):
    check_description = "Check for records with Systolic BP < Diastolic BP"
    datasets = "VS"
    vs_file_path = os.path.join(data_path, "vs.sas7bdat")

    if not os.path.exists(vs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to VS dataset not found at the specified location: {vs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    VS = load_data(data_path, 'vs')
    # Check if required columns exist in VS
    if "VSSPID" not in VS.columns:
        required_columns = ["USUBJID", "VISIT", "VSDTC", "VSTESTCD", "VSSTRESN", "VSSPID"]
    else:
        required_columns = ["USUBJID", "VISIT", "VSDTC", "VSTESTCD", "VSSTRESN"]
    if not set(required_columns).issubset(VS.columns):
        missing = set(required_columns) - set(VS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in VS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Select records for blood pressure
    vs0 = VS[required_columns]

    sbp = vs0[vs0["VSTESTCD"] == "SYSBP"].rename(columns={"VSDTC": "VSDTC.SYSBP", "VSSTRESN": "SYSBP"})
    dbp = vs0[vs0["VSTESTCD"] == "DIABP"].rename(columns={"VSDTC": "VSDTC.DIABP", "VSSTRESN": "DIABP"})
    if "VSSPID" not in VS.columns:
        mydf0 = pd.merge(sbp, dbp, on=["USUBJID", "VISIT", "VSSPID"])
    else:
        mydf0 = pd.merge(sbp, dbp, on=["USUBJID", "VISIT"])
    mydf = mydf0[(mydf0["DIABP"] > mydf0["SYSBP"]) & (mydf0["SYSBP"] > 0) & (mydf0["DIABP"] > 0)][["USUBJID", "VISIT", "VSDTC.SYSBP", "SYSBP", "DIABP"]]
    mydf = mydf.rename(columns={"VSDTC.SYSBP": "VSDTC"})
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"VS has {mydf.shape[0]} records with Systolic BP < Diastolic BP."
        return fail_check(check_description, datasets, notes, mydf)
    
def check_vs_vsdtc_after_dd(data_path):
    check_description = "Check for VS records occurring after death date"
    datasets = "VS, AE, DS"
    vs_file_path = os.path.join(data_path, "vs.sas7bdat")

    if not os.path.exists(vs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to VS dataset not found at the specified location: {vs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    VS= load_data(data_path, 'vs')
    
    ae_file_path = os.path.join(data_path, "ae.sas7bdat")

    if not os.path.exists(ae_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to AE dataset not found at the specified location: {ae_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    AE= load_data(data_path, 'ae')
    
    ds_file_path = os.path.join(data_path, "ds.sas7bdat")
    if not os.path.exists(ds_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to DS dataset not found at the specified location: {ds_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    DS= load_data(data_path, 'ds')


    # Check if required columns exist in AE
    required_ae_columns = ["USUBJID",  "AESTDTC", "AEDECOD", "AETERM", "AESDTH", "AEOUT"]
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Check if required columns exist in DS
    required_ds_columns = ["USUBJID", "DSSTDTC", "DSDECOD", "DSTERM"]
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Check if required columns exist in VS
    required_vs_columns = ["USUBJID", "VSDTC", "VSTESTCD", "VSORRES"]
    if not set(required_vs_columns).issubset(VS.columns):
        missing = set(required_vs_columns) - set(VS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in VS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    
    #AE["AEDTHDTC"] = AE["AEDTHDTC"].apply(impute_day01)
    AE["AESTDTC"] = impute_day01(AE["AESTDTC"]) 
    DS["DSSTDTC"] = impute_day01(DS["DSSTDTC"]) 
    VS["VSDTC"] = impute_day01(VS["VSDTC"])  
    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
    # Get earliest death date by USUBJID
    ae_dd = AE[["USUBJID", "AEDTHDTC"]].dropna().drop_duplicates().sort_values(by=["USUBJID", "AEDTHDTC"])
    ds_dd = DS[(DS["DSDECOD"].str.contains("DEATH", case=False, na=False) | DS["DSTERM"].str.contains("DEATH", case=False, na=False)) & DS["DSSTDTC"].notna()][["USUBJID", "DSSTDTC"]].drop_duplicates().sort_values(by=["USUBJID", "DSSTDTC"])

    death_dates = pd.merge(ae_dd, ds_dd, on="USUBJID", how="outer")

    if death_dates.empty:
        return pass_check(check_description, datasets)
    death_dates["EARLIEST_DTHDTC"] = death_dates[["AEDTHDTC", "DSSTDTC"]].min(axis=1)

    df = VS[VS["USUBJID"].isin(death_dates["USUBJID"]) & VS["VSDTC"].notna() & VS["VSORRES"].notna()][["USUBJID", "VSDTC", "VSTESTCD"]]
    df = pd.merge(df, death_dates, on="USUBJID")

    df = df[df["EARLIEST_DTHDTC"] < df["VSDTC"]]

    if df.empty:
        return pass_check(check_description, datasets)
    else:
        notes = "Patient(s) with VS occurring after death date."
        return fail_check(check_description, datasets, notes, df)
