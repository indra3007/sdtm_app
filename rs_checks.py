# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 09:09:16 2024

@author: inarisetty
"""

import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os

def check_rs_rscat_rsscat(data_path):
    check_description = "Check for missing RSCAT when RSSCAT is not missing"
    datasets = "RS"
    rs_file_path = os.path.join(data_path, "rs.sas7bdat")

    if not os.path.exists(rs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to RS dataset not found at the specified location: {rs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    RS = load_data(data_path, 'rs')
    required_columns = ["USUBJID", "RSCAT", "RSSCAT"]

    # Check if required variables exist in QS
    if not set(required_columns).issubset(RS.columns):
        missing = set(required_columns) - set(RS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in RS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    


    # Subset RS to only patient(s) with non-missing RSSCAT and missing RSCAT
    mydf = RS[is_null_or_empty2(RS["RSCAT"]) & ~is_null_or_empty2(RS["RSSCAT"])][["USUBJID", "RSCAT", "RSSCAT"]]

    # Return message if no patient(s) with missing RSCAT
    if mydf.empty:
        return pass_check(check_description, "RS")

    # Return subset dataframe if there are patient(s) with missing RSCAT
    return fail_check(
        check_description,
        datasets,
        f"There are {mydf['USUBJID'].nunique()} patients with unpopulated RSCAT values.",
        mydf
    )
def check_rs_rsdtc_across_visit(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for RSDTC across visits"
    datasets = "RS"
    rs_file_path = os.path.join(data_path, "rs.sas7bdat")

    if not os.path.exists(rs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to RS dataset not found at the specified location: {rs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    RS = load_data(data_path, 'rs')
    required_columns = ["USUBJID", "RSDTC", "VISIT"]

    # Check if required variables exist in QS
    if not set(required_columns).issubset(RS.columns):
        missing = set(required_columns) - set(RS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in RS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    

    # Apply company specific preprocessing function
    RS = preproc(RS, **kwargs)

    # Find unique pairs of RSDTC and VISIT per USUBJID
    if "RSEVAL" not in RS.columns:
        rssub = RS[["USUBJID", "RSDTC", "VISIT"] + [col for col in ["RSTESTCD"] if col in RS.columns]]
    else:
        rssub = RS[(RS["RSEVAL"].str.upper() == "INVESTIGATOR") | RS["RSEVAL"].isna()]
        rssub = rssub[["USUBJID", "RSDTC", "VISIT"] + [col for col in ["RSTESTCD"] if col in RS.columns]]

    rs_orig = rssub.copy()  
    rssub = rssub.drop(columns=[col for col in ["RSTESTCD"] if col in rssub.columns])

    if not rssub.empty:
        mypairs = rssub.drop_duplicates()
        mypairs["x"] = 1

        # Get counts of visit values per date for each subject
        mydf0 = mypairs.groupby(["USUBJID", "RSDTC"]).size().reset_index(name='x')

        # Subset where count is >1 and output
        mydf0 = mydf0[mydf0["x"] > 1].drop(columns="x")

        mypairs0 = mypairs[["USUBJID", "RSDTC", "VISIT"]]

        mydf = pd.merge(mydf0, mypairs0, on=["USUBJID", "RSDTC"], how="left")
        mydf = pd.merge(mydf, rs_orig, on=["USUBJID", "RSDTC", "VISIT"], how="left").drop_duplicates()

        mydf.reset_index(drop=True, inplace=True)
    else:
        mydf = pd.DataFrame()

    # If no inconsistency
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        # Return subset dataframe if there are records with inconsistency
        return fail_check(check_description, datasets, f"{len(mydf)} records with same date at >1 visit.", mydf)
def check_rs_rsdtc_visit(data_path):
    check_description = "Check for missing RSDTC or VISIT in RS"
    datasets = "RS"
    rs_file_path = os.path.join(data_path, "rs.sas7bdat")

    if not os.path.exists(rs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to RS dataset not found at the specified location: {rs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    RS = load_data(data_path, 'rs')
    required_columns = ["USUBJID", "RSDTC", "RSTEST", "RSORRES", "VISIT"]

    # Check if required variables exist in QS
    if not set(required_columns).issubset(RS.columns):
        missing = set(required_columns) - set(RS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in RS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    #missingunit = df[is_null_or_empty2(df["LBSTRESU"]) & ~is_null_or_empty_numeric(df["LBORRES"])]
    # Filter RS records based on the presence of the RSEVAL column
    if "RSEVAL" not in RS.columns:
        mydf = RS[
            (RS["RSDTC"].apply(is_null_or_empty) | is_null_or_empty2(RS["VISIT"])) &
            ~is_null_or_empty2(RS["RSORRES"]) &
            ~RS["RSORRES"].str.upper().isin(["NA", "NOT APPLICABLE", "N/A", "UNKNOWN"]) 
            
        ]
    else:
        mydf = RS[
            (RS["RSDTC"].apply(is_null_or_empty) | is_null_or_empty2(RS["VISIT"])) &
            ~is_null_or_empty2(RS["RSORRES"]) &
            ~RS["RSORRES"].str.upper().isin(["NA", "NOT APPLICABLE", "N/A", "UNKNOWN"]) &
           
            ((RS["RSEVAL"].str.upper() == "INVESTIGATOR") | is_null_or_empty2(RS["RSEVAL"])) 
        ]
    # Select relevant columns
    mydf = mydf[["USUBJID", "RSTEST", "RSDTC", "RSORRES", "VISIT", "RSEVAL"] if "RSEVAL" in RS.columns else ["USUBJID","RSTEST", "RSDTC", "RSORRES", "VISIT"]]

    mydf = mydf.reset_index(drop=True)

    # Check if there are any records with missing RSDTC or VISIT
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"There are {len(mydf)} records with missing RSDTC or VISIT.", mydf)
