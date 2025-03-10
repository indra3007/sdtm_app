# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 15:15:26 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os

def check_mh_missing_month(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for MH records with missing month in dates"
    datasets = "MH"

    mh_file_path = os.path.join(data_path, "mh.sas7bdat")

    if not os.path.exists(mh_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to MH dataset not found at the specified location: {mh_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    MH = load_data(data_path, 'mh')
    required_columns = ["USUBJID", "MHTERM", "MHSTDTC"]
    # Check if required variables exist in MH
    if not set(required_columns).issubset(MH.columns):
        missing = set(required_columns) - set(MH.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in MH: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Apply company-specific preprocessing function
    MH = preproc(MH, **kwargs)
    
    # Check for missing month in MHSTDTC and MHENDTC if it exists
    if 'MHENDTC' in MH.columns:
        df = MH.loc[MH["MHSTDTC"].apply(missing_month) | MH["MHENDTC"].apply(missing_month), ["USUBJID", "MHTERM", "MHSTDTC", "MHENDTC"]]
    else:
        df = MH.loc[MH["MHSTDTC"].apply(missing_month), ["USUBJID", "MHTERM", "MHSTDTC"]]

    # Return message if no records with missing month in dates
    if df.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"{df['USUBJID'].nunique()} patient(s) with medical history date that has year and day present but missing month."
        return fail_check(check_description, datasets, notes, df)
