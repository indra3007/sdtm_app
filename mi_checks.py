# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 15:23:13 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os

def check_mi_mispec(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for MI records with missing MISPEC"
    datasets = "MI"
    mi_file_path = os.path.join(data_path, "mi.sas7bdat")
    
    if not os.path.exists(mi_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to MI dataset not found at the specified location: {mi_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    MI = load_data(data_path, 'mi')
    required_columns = ["USUBJID", "MITESTCD", "MISPEC", "MIDTC"]
    
    # Check if required variables exist in MI
    if not set(required_columns).issubset(MI.columns):
        missing = set(required_columns) - set(MI.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in MI: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    
    # Apply company-specific preprocessing function
    MI = preproc(MI, **kwargs)
    
    # Filter records where MISPEC is not populated
    df = MI.loc[MI["MISPEC"].apply(is_null_or_empty), ["USUBJID", "MITESTCD", "MISPEC", "MIDTC"]]

    # Return message if no records with missing MISPEC
    if df.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"{len(df)} record(s) with required variable MISPEC not populated."
        return fail_check(check_description, datasets, notes, df)
