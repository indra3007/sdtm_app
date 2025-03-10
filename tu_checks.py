# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 13:22:40 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os

def check_tu_rs_new_lesions(data_path):
    check_description = "Check for new lesions in TU without overall response indicating progression in RS"
    datasets = "TU, RS"
    rs_file_path = os.path.join(data_path, "rs.sas7bdat")

    if not os.path.exists(rs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to RS dataset not found at the specified location: {rs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    tu_file_path = os.path.join(data_path, "tu.sas7bdat")

    if not os.path.exists(tu_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TU dataset not found at the specified location: {tu_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    TU = load_data(data_path, 'tu')
    RS = load_data(data_path, 'rs')
    required_tu_columns = ["USUBJID", "TUSTRESC", "TUDTC"]
    required_rs_columns = ["USUBJID", "RSSTRESC", "RSTESTCD"]


    # Check if required columns exist in TU
    if not set(required_tu_columns).issubset(TU.columns):
        missing = set(required_tu_columns) - set(TU.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in TU: {', '.join(missing)}"],
            "Notes": [""],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Check if required columns exist in RS
    if not set(required_rs_columns).issubset(RS.columns):
        missing = set(required_rs_columns) - set(RS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in RS: {', '.join(missing)}"],
            "Notes": [""],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Find new lesions in TU
    if "TUEVAL" not in TU.columns:
        mytu = TU[TU["TUSTRESC"] == "NEW"]
    else:
        mytu = TU[(TU["TUSTRESC"] == "NEW") & ((TU["TUEVAL"].str.upper() == "INVESTIGATOR") | (TU["TUEVAL"].str.upper().str.contains("INDEPENDENT")) | (TU["TUEVAL"].isna()))]

    # Find overall PD or PMD responses in RS
    if "RSEVAL" not in RS.columns:
        myrs = RS[(RS["RSTESTCD"] == "OVRLRESP") & (RS["RSSTRESC"].isin(["PD", "PMD"]))][["USUBJID"]].drop_duplicates()
    else:
        myrs = RS[(RS["RSTESTCD"] == "OVRLRESP") & (RS["RSSTRESC"].isin(["PD", "PMD"])) & 
                  ((RS["RSEVAL"].str.upper() == "INVESTIGATOR") | (RS["RSEVAL"].isna()))][["USUBJID"]].drop_duplicates()

    keeper_vars = [col for col in ["USUBJID", "TUSTRESC", "TUDTC", "VISIT"] if col in TU.columns]
    mydf = mytu[~mytu["USUBJID"].isin(myrs["USUBJID"])][keeper_vars].drop_duplicates()
    mydf.reset_index(drop=True, inplace=True)

    # Return message if no inconsistency
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"TU has {mydf['USUBJID'].nunique()} patient(s) with a new lesion but no Overall Response indicating progression."
        return fail_check(check_description, datasets, notes, mydf)
    
def check_tu_tudtc(data_path, preproc=lambda df: df, **kwargs):
    required_columns = ["USUBJID", "TUDTC", "VISIT", "TUORRES"]
    check_description = "Check for missing TUDTC in TU"
    datasets = "TU"
    tu_file_path = os.path.join(data_path, "tu.sas7bdat")

    if not os.path.exists(tu_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TU dataset not found at the specified location: {tu_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TU = load_data(data_path, 'tu')
    # Check if required columns exist in TU
    if not set(required_columns).issubset(TU.columns):
        missing = set(required_columns) - set(TU.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in TU: {', '.join(missing)}"],
            "Notes": [""],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    TU = preproc(TU, **kwargs)
    myvars = ["USUBJID", "VISIT", "TUDTC", "TUORRES"] + [col for col in ["TUEVAL", "TUTESTCD"] if col in TU.columns]

    TU = TU[myvars]

    # Subset TU to only records with missing TUDTC
    if "TUEVAL" not in TU.columns:
        mydf = TU[TU["TUDTC"].isna()]
    else:
        mydf = TU[(TU["TUDTC"].isna()) & ((TU["TUEVAL"].str.upper() == "INVESTIGATOR") | (TU["TUEVAL"].str.upper().str.contains("INDEPENDENT")) | (TU["TUEVAL"].isna()))]

    mydf.reset_index(drop=True, inplace=True)

    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"TU has {mydf['USUBJID'].nunique()} patient(s) with {mydf.shape[0]} record(s) with missing TUDTC."
        return fail_check(check_description, datasets, notes, mydf)
def check_tu_tudtc_across_visit(data_path, preproc=lambda df: df, **kwargs):
    required_columns = ["USUBJID", "TUDTC", "VISIT"]
    check_description = "Check for TUDTC across multiple visits in TU"
    datasets = "TU"
    tu_file_path = os.path.join(data_path, "tu.sas7bdat")

    if not os.path.exists(tu_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TU dataset not found at the specified location: {tu_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TU = load_data(data_path, 'tu')
    # Check if required columns exist in TU
    if not set(required_columns).issubset(TU.columns):
        missing = set(required_columns) - set(TU.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in TU: {', '.join(missing)}"],
            "Notes": [""],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company-specific preprocessing function
    TU = preproc(TU, **kwargs)

    # Find unique pairs of TUDTC and VISIT per USUBJID
    if "TUEVAL" not in TU.columns:
        tusub = TU[["USUBJID", "TUDTC", "VISIT"] + [col for col in ["TUTESTCD", "RAVE"] if col in TU.columns]]
    else:
        tusub = TU[(TU["TUEVAL"].str.upper() == "INVESTIGATOR") | TU["TUEVAL"].str.upper().str.contains("INDEPENDENT") | (TU["TUEVAL"].isna())]
        tusub = tusub[["USUBJID", "TUDTC", "VISIT"] + [col for col in ["TUTESTCD", "RAVE"] if col in TU.columns]]

    tu_orig = tusub.copy()  # Save RAVE for merging in later
    tusub = tusub.drop(columns=[col for col in ["TUTESTCD", "RAVE"] if col in tusub.columns])

    if not tusub.empty:
        # Get unique visit/date pairs per patient
        mypairs = tusub.drop_duplicates()
        mypairs["x"] = 1

        # Get counts of visit values per date for each subject
        mydf0 = mypairs.groupby(["USUBJID", "TUDTC"]).size().reset_index(name='x')

        # Subset where count is >1
        mydf0 = mydf0[mydf0["x"] > 1][["USUBJID", "TUDTC"]]

        mypairs0 = mypairs[["USUBJID", "TUDTC", "VISIT"]]

        # Subset unique pairs to only instances where visit has >1 date
        mydf = pd.merge(mydf0, mypairs0, on=["USUBJID", "TUDTC"], how="left") \
                 .merge(tu_orig, on=["USUBJID", "TUDTC", "VISIT"], how="left") \
                 .drop_duplicates()

        mydf.reset_index(drop=True, inplace=True)
    else:
        mydf = pd.DataFrame()

    # Check for inconsistencies
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"There are {mydf.shape[0]} TU records where the same date occurs across multiple visits."
        return fail_check(check_description, datasets, notes, mydf)
def check_tu_tudtc_visit_ordinal_error(data_path):
    required_columns = ["USUBJID", "TUORRES", "TULOC", "VISITNUM", "VISIT", "TUDTC", "TUEVAL"]
    check_description = "Check for TUDTC visit ordinal error in TU"
    datasets = "TU"
    tu_file_path = os.path.join(data_path, "tu.sas7bdat")

    if not os.path.exists(tu_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TU dataset not found at the specified location: {tu_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TU = load_data(data_path, 'tu')
    # Check if required columns exist in TU
    if not set(required_columns).issubset(TU.columns):
        missing = set(required_columns) - set(TU.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in TU: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Check if VISITNUM has more than one unique value
    if TU["VISITNUM"].nunique() <= 1:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["VISITNUM exists but only a single value."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset TU to relevant records
    subsetdf = TU[((TU["TUEVAL"].str.upper() == "INVESTIGATOR") ) & (~TU["VISIT"].str.upper().str.contains("UNSCHEDU"))]

    if subsetdf.shape[0] > 0:
        # Apply dtc_dupl_early function (you'll need to implement this function as per your requirements)
        mydf2 = dtc_dupl_early(
            subsetdf,
            vars=required_columns,
            groupby=["USUBJID","TULNKID","TUTESTCD", "TUORRES", "TULOC"],
            dtc="TUDTC"
        
        )

        # Subset if Vis_order not equal Dtc_order
        myout = mydf2[~mydf2["check_flag"].isna()]

        # Return message if no records with EXSTDTC per VISITNUM
        if myout.shape[0] == 0:
            return pass_check(check_description, datasets)

        else:
            myout.reset_index(drop=True, inplace=True)
            notes = f"TU has {myout.shape[0]} records with Possible TUDTC data entry error."
            return fail_check(check_description, datasets, notes, myout)
     
    return pd.DataFrame({
        "CHECK": [check_description],
        "Message": ["No records when subset to only INV records."],
        "Notes": [""],
        "Datasets": [datasets],
        "Data": [pd.DataFrame()]  # Return an empty DataFrame
    })
def check_tu_tuloc_missing(data_path, preproc=lambda df: df, **kwargs):
    required_columns = ["USUBJID", "TUDTC", "VISIT", "TUORRES", "TULOC"]
    check_description = "Check for target lesions with missing TULOC in TU"
    datasets = "TU"
    tu_file_path = os.path.join(data_path, "tu.sas7bdat")

    if not os.path.exists(tu_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TU dataset not found at the specified location: {tu_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TU = load_data(data_path, 'tu')
    # Check if required columns exist in TU
    if not set(required_columns).issubset(TU.columns):
        missing = set(required_columns) - set(TU.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in TU: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company-specific preprocessing function
    TU = preproc(TU, **kwargs)

    if "TUEVAL" not in TU.columns:
        # Subset TU to only target lesions with missing TULOC
        mydf = TU[(TU["TULOC"].apply(pd.isna)) & (TU["TUORRES"].str.upper() == "TARGET")][
            ["USUBJID", "TUDTC", "VISIT", "TUORRES", "TULOC"]]
    else:
        mydf = TU[(TU["TULOC"].apply(pd.isna)) & (TU["TUORRES"].str.upper() == "TARGET") & 
                  ((TU["TUEVAL"].str.upper() == "INVESTIGATOR") | (TU["TUEVAL"].apply(pd.isna)))][
            ["USUBJID", "TUDTC", "VISIT", "TUORRES", "TULOC"]]

    mydf.reset_index(drop=True, inplace=True)

    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"There are {mydf.shape[0]} target lesions with missing TULOC."
        return fail_check(check_description, datasets, notes, mydf)
