# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 11:15:46 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os


def check_tr_dup(data_path):
    check_description = "Check for duplicate TR records"
    datasets = "TR"
    tr_file_path = os.path.join(data_path, "tr.sas7bdat")

    if not os.path.exists(tr_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TR dataset not found at the specified location: {tr_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TR = load_data(data_path, 'tr')
    # First check that required variables exist and return a message if they don't
    required_columns = ["USUBJID", "TRCAT", "TRTESTCD", "TRDTC", "TRSTRESC"]


    if not set(required_columns).issubset(TR.columns):
        missing = set(required_columns) - set(TR.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in TR: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not { "TRLNKID"}.intersection(TR.columns):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["TR is missing TRLNKID variable."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    myvars = ["USUBJID", "TRCAT", "TRTESTCD", "VISIT"] + \
             [col for col in ["TRLINKID", "TRLNKID"] if col in TR.columns] + \
             ["TRSPID" if "TRSPID" in TR.columns else None, "TRDTC", "TRSTRESC"]

    myvars = [var for var in myvars if var]  # Remove None values from the list

    if "TREVAL" not in TR.columns:
        # for TR domains without TREVAL
        tr1 = TR[myvars].groupby(myvars).filter(lambda x: len(x) > 1)
    else:
        # for TR domains with TREVAL
        tr1 = TR[(TR["TREVAL"].str.upper() == "INVESTIGATOR") | (TR["TREVAL"].str.upper().str.contains("INDEPENDENT"))  | (TR["TREVAL"].apply(is_null_or_empty))][myvars]
        tr1 = tr1.groupby(myvars).filter(lambda x: len(x) > 1)

    # duplicate TR records
    dups = tr1[tr1.duplicated(subset=myvars, keep=False)].reset_index(drop=True)

    # declare number of duplicated TR records and print them
    n0 = f'There are {len(dups)} duplicated TR records.'

    if dups.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, n0, dups)
def check_tr_trdtc_across_visit(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check TR TRDTC across visit"
    datasets = "TR"
    tr_file_path = os.path.join(data_path, "tr.sas7bdat")

    if not os.path.exists(tr_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TR dataset not found at the specified location: {tr_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TR = load_data(data_path, 'tr')
    required_columns = ["USUBJID", "TRDTC", "VISIT", "TRTESTCD"]

    # Check if required variables exist and return a message if they don't
    if not set(required_columns).issubset(TR.columns):
        missing = set(required_columns) - set(TR.columns)
        return pd.DataFrame({
            "CHECK": ["Check TR TRDTC across visit"],
            "Message": [f"Missing columns: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company-specific preprocessing function
    TR = preproc(TR, **kwargs)

    # Find unique pairs of TRDTC and VISIT per USUBJID
    if "TREVAL" not in TR.columns:
        trsub = TR[(TR["TRTESTCD"] == "LDIAM") & ~TR["TRDTC"].apply(is_null_or_empty)][["USUBJID", "TRDTC", "VISIT", "TRTESTCD"]]
    else:
        trsub = TR[(TR["TRTESTCD"] == "LDIAM") & ((TR["TREVAL"].str.upper() == "INVESTIGATOR") | (TR["TREVAL"].str.upper().str.contains("INDEPENDENT")) | 
                (TR["TREVAL"].isna())) & ~TR["TRDTC"].apply(is_null_or_empty)][["USUBJID", "TRDTC", "VISIT", "TRTESTCD"]]

    tr_orig = trsub.copy()  # Save RAVE for merging in later


    if len(trsub) > 0:
        mypairs = trsub.drop_duplicates()
        mypairs["x"] = 1

        # Get counts of visit values per date for each subject
        mydf0 = mypairs.groupby(["USUBJID", "TRDTC"]).size().reset_index(name='x')

        # Subset where count is >1 and output
        mydf0 = mydf0[mydf0['x'] > 1][["USUBJID", "TRDTC"]]

        mypairs0 = mypairs[["USUBJID", "TRDTC", "VISIT", "TRTESTCD"]]

        mydf = mydf0.merge(mypairs0, on=["USUBJID", "TRDTC"], how='left').merge(tr_orig, on=["USUBJID", "TRDTC", "VISIT", "TRTESTCD"], how='left').drop_duplicates()

        if mydf.empty:
            return pass_check(check_description, datasets)
        else:
            notes = f"There are {len(mydf)} TR Longest Diameter records where the same date occurs across multiple visits."
            return fail_check(check_description, datasets, notes, mydf)
    else:
        
        return pass_check(check_description, datasets)
def check_tr_trdtc_visit_ordinal_error(data_path, preproc=lambda df: df, **kwargs):
    
    check_description = "Check TR TRDTC visit ordinal error"
    datasets = "TR"
    tr_file_path = os.path.join(data_path, "tr.sas7bdat")

    if not os.path.exists(tr_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TR dataset not found at the specified location: {tr_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TR = load_data(data_path, 'tr')
    required_columns = ["USUBJID", "VISITNUM", "VISIT", "TRDTC", "TREVAL", "TRSTAT"]
    
    # Check that required variables exist and return a message if they don't
    if not set(required_columns).issubset(TR.columns):
        missing = set(required_columns) - set(TR.columns)
        return pd.DataFrame({
            "CHECK": ["Check TR TRDTC visit ordinal error"],
            "Message": [f"Missing columns: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    # Don't run if VISITNUM is all missing
    if len(TR["VISITNUM"].unique()) <= 1:
        return pd.DataFrame({
            "CHECK": ["Check TR TRDTC visit ordinal error"],
            "Message": ["VISITNUM exists but only a single value."],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    # Apply company specific preprocessing function
    TR = preproc(TR, **kwargs)
    
    subsetdf = TR[(TR["TREVAL"] == "INVESTIGATOR") & 
                  (TR["TRSTAT"] != "NOT DONE") & 
                  (~TR["VISIT"].str.upper().str.contains("UNSCHEDU"))]
    
    if subsetdf.shape[0] > 0:
        mydf2 = dtc_dupl_early(
            subsetdf,
            vars=required_columns,
            groupby=["USUBJID"],
            dtc="TRDTC"
           
        )
        
        myout = mydf2[~mydf2["check_flag"].isna()]
        myout = myout[myout["check_flag"] != "Duplicated"]
        
        if myout.shape[0] == 0:
            return pass_check(check_description, datasets)
        else:
            notes = f"TR has {myout.shape[0]} records with Possible TRDTC data entry error."
            return fail_check(check_description, datasets, notes, myout)
           
    else:
        
        return pd.DataFrame({
            "CHECK": ["Check TR TRDTC visit ordinal error"],
            "Message": ["No records when subset to only INV records."],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
def check_tr_trstresn_ldiam(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check TRSTRESN LDIAM"
    datasets = "TR"
    tr_file_path = os.path.join(data_path, "tr.sas7bdat")

    if not os.path.exists(tr_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TR dataset not found at the specified location: {tr_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TR = load_data(data_path, 'tr')
    required_columns = ["USUBJID", "TRTESTCD", "TRDTC", "VISIT", "TRORRES", "TRSTRESN"]
    linkid_columns = [ "TRLNKID"]
    # Check that required variables exist and return a message if they don't
    if not set(required_columns).issubset(TR.columns) or not any(col in TR.columns for col in linkid_columns):
        missing = set(required_columns) - set(TR.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    if "LDIAM" not in TR["TRTESTCD"].values:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["No records with TR.TRTESTCD = 'LDIAM' found"],
            "Notes": [""],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    TR = preproc(TR, **kwargs)

    myvars = ["USUBJID", "TRTESTCD", "TRDTC", "VISIT", "TRORRES", "TRSTRESN"] + \
             [col for col in TR.columns if col in ["TRLNKID", "TRSTAT"]]
    
    if "TREVAL" not in TR.columns:
        df = TR[(TR["TRTESTCD"] == "LDIAM") & is_null_or_empty_numeric(TR["TRSTRESN"])][myvars]
    else:
        df = TR[(TR["TRTESTCD"] == "LDIAM") & is_null_or_empty_numeric(TR["TRSTRESN"]) & 
                ((TR["TREVAL"].str.upper() == "INVESTIGATOR") | is_null_or_empty2(TR["TREVAL"]))][myvars]

    if df.shape[0] == 0:
        return pass_check(check_description, datasets)
    else:
        # x not done
        x = df[df["TRORRES"].isin(["NOT DONE", "ND"])].shape[0]
        if "TRSTAT" in df.columns:
            x += df[df["TRSTAT"] == "NOT DONE"].shape[0]
        # y not evaluable
        y = df[df["TRORRES"].isin(["NOT EVALUABLE", "NE"])].shape[0]
        # z done but missing
        z = df.shape[0] - x - y
        notes = (f"TR has {df.shape[0]} record(s) with missing TRSTRESN values for LDIAM assessment. "
                 f"{x} record(s) indicate 'NOT DONE'. "
                 f"{y} record(s) indicate 'NOT EVALUABLE'. "
                 f"{z} record(s) indicate done and evaluable but otherwise missing.")
        return fail_check(check_description, datasets, notes, df)
     