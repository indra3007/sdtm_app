# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 15:27:35 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os


def check_pr_missing_month(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for PR records with missing month in dates"
    datasets = "PR"
    pr_file_path = os.path.join(data_path, "pr.sas7bdat")

    if not os.path.exists(pr_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to PR dataset not found at the specified location: {pr_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    PR = load_data(data_path, 'pr')
    required_columns = ["USUBJID", "PRTRT", "PRSTDTC"]
    
    # Check if required variables exist in PR
    if not set(required_columns).issubset(PR.columns):
        missing = set(required_columns) - set(PR.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in PR: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    # Apply company specific preprocessing function
    PR = preproc(PR, **kwargs)

    # PRENDTC is an optional variable
    if "PRENDTC" not in PR.columns:
        mydf = PR.loc[PR["PRSTDTC"].apply(missing_month), ["USUBJID", "PRTRT", "PRSTDTC"]]
    else:
        mydf = PR.loc[PR["PRSTDTC"].apply(missing_month) | PR["PRENDTC"].apply(missing_month), ["USUBJID", "PRTRT", "PRSTDTC", "PRENDTC"]]

    # Return message if no records with missing month in dates
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"{len(mydf['USUBJID'].unique())} patient(s) with a PR procedure date with known year and day but unknown month."
        return fail_check(check_description, datasets, notes, mydf)
def check_pr_prlat(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for PRLAT in records with PRCAT containing 'OCULAR'"
    datasets = "PR"
    pr_file_path = os.path.join(data_path, "pr.sas7bdat")

    if not os.path.exists(pr_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to PR dataset not found at the specified location: {pr_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    PR = load_data(data_path, 'pr')
    required_columns = ["USUBJID", "PRCAT", "PRLAT", "PRTRT", "PROCCUR", "PRPRESP"]

    # Check if required variables exist in PR
    if not set(required_columns).issubset(PR.columns):
        missing = set(required_columns) - set(PR.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in PR: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    
    # Filter for relevant PRCAT
    if PR.loc[PR["PRCAT"].str.upper().str.contains("OCULAR") & ~PR["PRCAT"].str.upper().str.contains("NON-OCULAR")].empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["No data with PRCAT containing the word OCULAR"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Apply company-specific preprocessing function
    PR = preproc(PR, **kwargs)

    perm_var = ["PRSTDTC", "PRINDC"]
    int_var = [col for col in perm_var if col in PR.columns]
    my_select_var = ["USUBJID", "PRCAT"] + int_var + ["PRLAT", "PRTRT"]

    mydf = PR.loc[
        PR["PRCAT"].str.upper().str.contains("OCULAR") & 
        ~PR["PRCAT"].str.upper().str.contains("NON-OCULAR") &
        ((PR["PRPRESP"] == "Y") & (PR["PROCCUR"] == "Y") | (PR["PRPRESP"].apply(is_null_or_empty) & PR["PROCCUR"].apply(is_null_or_empty))),
        my_select_var
    ].copy()

    mydf["MISFLAG"] = ~mydf["PRLAT"].str.upper().isin(["LEFT", "RIGHT", "BILATERAL"]).astype(int)

    mydf = mydf.loc[mydf["MISFLAG"] == 1].drop(columns=["MISFLAG"])

    # Return message if no records with PRLAT Missing from records with PRCAT containing the word OCULAR
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"{mydf.shape[0]} record(s) with PRLAT Missing from records with PRCAT containing the word OCULAR when expected to be populated."
        return fail_check(check_description, datasets, notes, mydf)
