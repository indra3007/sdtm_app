# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 10:18:29 2024

@author: inarisetty
"""

import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os

def check_sc_dm_eligcrit(data_path):
    check_description = "Check for eligibility criteria in SC"
    datasets = "DM, SC"
    sc_file_path = os.path.join(data_path, "sc.sas7bdat")

    if not os.path.exists(sc_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to SC dataset not found at the specified location: {sc_file_path}"],
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
    SC = load_data(data_path, 'sc')
    required_sc_columns = ["USUBJID", "SCTEST", "SCTESTCD", "SCCAT", "SCORRES", "SCDTC"]

    # Check if required variables exist in QS
    if not set(required_sc_columns).issubset(SC.columns):
        missing = set(required_sc_columns) - set(SC.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in SC: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    DM = load_data(data_path, 'dm')
    required_dm_columns = ["USUBJID"]
    
    if not set(required_dm_columns).issubset(DM.columns):
        missing = set(required_dm_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Select relevant columns from DM
    DM = DM[["USUBJID"]]

    # Filter and mutate SC dataframe
    SC = SC[["USUBJID", "SCTESTCD", "SCTEST", "SCCAT", "SCORRES", "SCDTC"]]
    SC["MISFLAG"] = SC.apply(lambda row: 1 if (pd.notna(row["SCTESTCD"]) and "ELIGEYE" in row["SCTESTCD"].upper() and row["SCORRES"] not in ["OD", "OS", "OU"]) else 0, axis=1)

    # Merge DM and SC dataframes
    mydf = pd.merge(DM, SC, on="USUBJID", how="left")

    # Filter dataframe
    mydf = mydf[(mydf["MISFLAG"] == 1) | (mydf["SCORRES"].isna())].drop(columns=["MISFLAG"])

    # Check if there are any records with missing eligibility criteria
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"{len(mydf)} record(s) missing eye(s) that met study criteria in SC.", mydf.reset_index(drop=True))
