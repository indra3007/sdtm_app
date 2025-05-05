# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 10:36:21 2024

@author: inarisetty
"""
import pandas as pd 
import os 
from datetime import datetime
import re
import numpy as np
import plotly.express as px
from dash import dcc
from utils import load_data,is_null_or_empty, is_null_or_empty2,fail_check, pass_check, lacks_any, lacks_all, impute_day01, miss_col, dtc_dupl_early

def check_ex_dup(data_path):
    datasets = "EX"
    check_description = "Check for Duplicate Dosing in EX"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")
    if  os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
        required_columns = ["USUBJID", "EXTRT", "EXDOSE", "EXSTDTC"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Helper function for checking required columns
    def lacks_any(df, required_columns):
        return [col for col in required_columns if col not in df.columns]

    # Helper function for generating fail message

    # First bifurcate EX into a df based on occurrence of EXOCCUR
    if "EXOCCUR" in EX.columns:
        EX = EX[EX["EXOCCUR"] == "Y"]

    # Check that required variables exist
    
    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Leave only variables on which we want to check duplicate dosing
    ex0 = EX[["USUBJID", "EXTRT", "EXDOSE", "EXSTDTC"]]

    # Sort
    ex1 = ex0.sort_values(by=["USUBJID", "EXTRT", "EXDOSE", "EXSTDTC"])

    # Check if there are duplicate dosing
    dups = ex1[ex1.duplicated()].reset_index(drop=True)
    n0 = f"There are {len(dups)} duplicated exposure records."

    if len(dups) > 0:
        # Check that the visit variable is in the dataset
        if "VISIT" not in EX.columns:
            # Print this list without visit information appended if there is no visit variable
            return fail_check(check_description,datasets,n0, dups)
        
            # Merge this back to get the visit to print in the duplicate list
        ex2 = EX[["USUBJID", "EXTRT", "EXDOSE", "EXSTDTC", "VISIT"]]
        ex2s = ex2.sort_values(by=["USUBJID", "EXTRT", "EXDOSE", "EXSTDTC", "VISIT"])

            # Left join to merge on VISIT
        dups_with_visit = pd.merge(dups, ex2s, on=["USUBJID", "EXTRT", "EXDOSE", "EXSTDTC"], how="left").drop_duplicates()
        return fail_check(check_description,datasets,n0, dups_with_visit)
   
    else:
        return pass_check(check_description,datasets)
def check_ex_exdose_exoccur(data_path, drug=None):
    datasets = "EX"
    check_description = "Check for Missing EXDOSE"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")
    if  os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
        required_columns = ["USUBJID", "EXTRT", "EXSTDTC", "EXDOSE"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if drug is not None and drug not in EX["EXTRT"].values:
        return fail_check(check_description,datasets,"Drug name not found in dataset")

    if lacks_all(EX, ["EXOCCUR", "VISIT"]):
        df = EX[["USUBJID", "EXTRT", "EXSTDTC", "EXDOSE"]][EX["EXDOSE"].apply(is_null_or_empty)]
    elif lacks_any(EX, ["EXOCCUR"]):
        df = EX[["USUBJID", "EXTRT", "VISIT", "EXSTDTC", "EXDOSE"]][EX["EXDOSE"].apply(is_null_or_empty)]
    elif lacks_any(EX, ["VISIT"]):
        df = EX[["USUBJID", "EXTRT", "EXSTDTC", "EXOCCUR", "EXDOSE"]][EX["EXDOSE"].apply(is_null_or_empty)]
    else:
        df = EX[["USUBJID", "EXTRT", "VISIT", "EXSTDTC", "EXOCCUR", "EXDOSE"]][(EX["EXOCCUR"] == "Y") & EX["EXDOSE"].apply(is_null_or_empty)]

    if drug is not None:
        df = df[df["EXTRT"] == drug]

    if len(df) != 0 and drug is not None:
        return fail_check(check_description,datasets,f"EX has {len(df)} record(s) with missing EXDOSE when EXOCCUR = 'Y' (or EXOCCUR does not exist) for {drug}.", df)
    elif len(df) != 0:
        return fail_check(check_description,datasets,f"EX has {len(df)} record(s) with missing EXDOSE when EXOCCUR = 'Y' (or EXOCCUR does not exist).", df)
    else:
        return pass_check(check_description,datasets)
def check_ex_exdose_pos_exoccur_no(data_path):
    datasets = "EX"
    check_description = "Check for Positive EXDOSE with EXOCCUR not 'Y'"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    required_columns = ["USUBJID", "EXTRT",  "EXOCCUR", "EXSTDTC","EXDOSE", "VISIT"]
    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    unique_drugs = EX["EXTRT"].unique()
    results = []

    for drug in unique_drugs:
        #df = EX[["USUBJID", "EXTRT", "EXSTDTC", "EXOCCUR", "EXDOSE", "VISIT"]][(EX["EXOCCUR"] != "Y") & (EX["EXDOSE"] > 0) & (EX["EXTRT"] == drug)]
        df = EX[["USUBJID", "EXTRT", "EXSTDTC",  "EXOCCUR", "EXDOSE", "VISIT"]][(EX["EXDOSE"] > 0) & (EX["EXTRT"] == drug)]
        if not df.empty:
            results.append(fail_check(check_description, datasets, f"There are {len(df['USUBJID'].unique())} patients with positive dose amount (EXDOSE>0) when occurrence (EXOCCUR) for {drug} is not 'Y'.", df))

    if not results:
        return pass_check(check_description, datasets)
    else:
        return pd.concat(results, ignore_index=True)
def check_ex_exdosu(data_path):
    datasets = "EX"
    check_description = "Check for Missing EXDOSU"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    required_columns = ["USUBJID", "EXTRT", "EXSTDTC", "EXDOSE", "EXDOSU"]
    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    if "EXOCCUR" in EX.columns:
        df = EX[EX["EXOCCUR"] == "Y"]
    else:
        df = EX

    df = df[required_columns]
    df = df[df["EXDOSU"].isna()]

    if df.empty:
        return pass_check(check_description, datasets)
    else:
        df = df.reset_index(drop=True)
        return fail_check(check_description, datasets, f"There are {len(df)} records with missing dose units.", df)
def check_ex_exoccur_exdose_exstdtc(data_path):
    check_description = "Check for EX records with invalid dosing amount or missing full treatment administration date"
    datasets = "EX"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "VISIT", "VISITNUM", "EXTRT", "EXDOSE", "EXSTDTC", "EXENDTC"]
    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # First bifurcate EX into a df based on occurrence of EXOCCUR
    if "EXOCCUR" in EX.columns:
        df = EX[EX["EXOCCUR"] == "Y"]
    else:
        df = EX

    # Convert EXSTDTC to datetime
    df['startdate'] = pd.to_datetime(df['EXSTDTC'], errors='coerce')

    # Get unique values from EXTRT
    unique_extrt_values = EX["EXTRT"].unique()

    # Create regex pattern from unique EXTRT values
    extrt_pattern = "|".join([re.escape(str(val)) for val in unique_extrt_values])
    
    # Filter by NA date, NA EXDOSE value, or invalid EXDOSE value
    df = df[df['startdate'].apply(is_null_or_empty) | 
            df['EXDOSE'].apply(is_null_or_empty) |
            (df['EXTRT'].str.contains(extrt_pattern, regex=True) & df['EXDOSE'] <= 0)]


    # Select based on regex matching
    df = df.filter(regex="USUBJID$|VISIT$|VISITNUM$|EXOCCUR$|EXTRT$|EXDOSE$|EXSTDTC$|EXENDTC$")

    if not df.empty:
        return fail_check(check_description, datasets, f"There are {len(df)} EX records with invalid dosing amount or missing full treatment administration date.", df)
    else:
        return pass_check(check_description, datasets)
def check_ex_exoccur_mis_exdose_nonmis(data_path):
    check_description = "Check for missing EXOCCUR with non-missing EXDOSE"
    datasets = "EX"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "EXTRT", "EXOCCUR", "EXDOSE", "EXSTDTC"]
    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    
    if EX["EXOCCUR"].notna().all():
        return pass_check(check_description, datasets)
    else:
        ex2 = EX[["USUBJID", "EXTRT", "EXOCCUR", "EXDOSE", "EXSTDTC"]][EX["EXOCCUR"].apply(is_null_or_empty) & EX["EXDOSE"].notna()]
        
        if not ex2.empty:
            n0= f"There are {len(ex2)} EX records with EXOCCUR missing but EXDOSE not missing."
            #return fail_check(check_description, datasets, f"There are {len(ex2)} EX records with EXOCCUR missing but EXDOSE not missing.", ex2)
            return fail_check(check_description, datasets, n0, ex2)
        else:
            return pass_check(check_description, datasets)



def check_ex_exstdtc_after_dd(data_path):
    check_description = "Check for EXSTDTC after death dates in AE and DS"
    datasets = "EX, DS, AE"
    
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    ds_file_path = os.path.join(data_path, "ds.sas7bdat")

    if os.path.exists(ds_file_path):
        DS = load_data(data_path, 'ds')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to DS dataset not found at the specified location: {ds_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    ae_file_path = os.path.join(data_path, "ae.sas7bdat")

    if os.path.exists(ae_file_path):
        AE = load_data(data_path, 'ae')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to AE dataset not found at the specified location: {ae_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_ae_columns = ["USUBJID", "AESTDTC", "AEDECOD", "AETERM","AESDTH", "AEOUT"]
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

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
    required_ex_columns = ["USUBJID", "EXSTDTC", "EXTRT", "EXDOSE"]
    if not set(required_ex_columns).issubset(EX.columns):
        missing = set(required_ex_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
    AE['AEDTHDTC'] = impute_day01(AE['AEDTHDTC'])
    AE['AESTDTC'] = impute_day01(AE['AESTDTC'])
    DS['DSSTDTC'] = impute_day01(DS['DSSTDTC'])
    EX['EXSTDTC'] = impute_day01(EX['EXSTDTC'])

    # Get earliest death date by USUBJID
    ae_dd = AE[['USUBJID', 'AEDTHDTC']].dropna().drop_duplicates()
    ds_dd = DS[DS.apply(lambda row: 'DEATH' in row['DSDECOD'].upper() or 'DEATH' in row['DSTERM'].upper(), axis=1)][['USUBJID', 'DSSTDTC']].dropna().drop_duplicates()

    death_dates = pd.merge(ae_dd, ds_dd, on='USUBJID', how='outer')
    death_dates['EARLIEST_DTHDTC'] = death_dates[['AEDTHDTC', 'DSSTDTC']].min(axis=1)

    if death_dates.empty:
        return pass_check(check_description, datasets)

    df = EX[(EX['USUBJID'].isin(death_dates['USUBJID'])) & (EX['EXSTDTC'].notna()) & (EX['EXTRT'].notna()) & (EX['EXDOSE'].notna())]

    if 'EXOCCUR' in EX.columns:
        df = df[df['EXOCCUR'] == 'Y']

    df = df[['USUBJID', 'EXSTDTC']].merge(death_dates, on='USUBJID')
    df = df[df['EARLIEST_DTHDTC'] < df['EXSTDTC']]

    if df.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"Patient(s) with EX occurring after death date.", df)
def check_ex_exstdtc_visit_ordinal_error(data_path):
    check_description = "Check for EXSTDTC Visit Ordinal Error"
    datasets = "EX"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "EXTRT", "VISITNUM", "VISIT", "EXSTDTC"]
    
    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    
    # Don't run if VISITNUM is all missing
    if len(EX["VISITNUM"].unique()) <= 1:
        return fail_check(check_description, datasets, "VISITNUM exists but only a single value")

    # Filter for EXOCCUR if it exists
    if "EXOCCUR" in EX.columns:
        EX = EX[EX["EXOCCUR"] == "Y"]

    # Filter out unscheduled visits
    EX = EX[~EX["VISIT"].str.upper().str.contains("UNSCHEDU", na=False)]
    
    # Apply dtc_dupl_early function
    mydf2 = dtc_dupl_early(
        EX,
        vars=required_columns,
        groupby=["USUBJID", "EXTRT"],
        dtc="EXSTDTC"
    )
    
    # Subset if Vis_order not equal Dtc_order
    myout = mydf2[~mydf2["check_flag"].isna()]
    
    # Different check already doing dups
    myout = myout[myout["check_flag"] != "Duplicated"]
    
    # Return message if no records with EXSTDTC per VISITNUM
    if myout.empty:
        return pass_check(check_description, datasets)
    else:
        message = "Fail"
        notes = f"{len(myout)} records with Possible EXSTDTC data entry error."
        myout.insert(0, "CHECK", check_description)
        myout.insert(1, "Message", message)
        myout.insert(2, "Notes", notes)
        myout.insert(3, "Datasets", datasets)
        return myout
def check_ex_extrt_exoccur(data_path):
    check_description = "Check for Missing EXTRT where EXOCCUR is Y"
    datasets = "EX"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "EXSTDTC", "EXTRT", "EXDOSE"]
    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    if "EXOCCUR" in EX.columns:
        # Subset EX to only records with missing EXTRT but EXOCCUR=Y
        mydf = EX[["USUBJID", "EXSTDTC", "EXTRT", "EXOCCUR", "EXDOSE"]][
            EX["EXTRT"].apply(is_null_or_empty) & (EX["EXOCCUR"] == "Y")
        ]
        mymsg = "Patients with Missing EXTRT where EXOCCUR=Y"
    else:
        # Subset EX to only records with missing EXTRT where EXOCCUR doesn't exist
        mydf = EX[["USUBJID", "EXSTDTC", "EXTRT", "EXDOSE"]][
            EX["EXTRT"].apply(is_null_or_empty)
        ]
        mymsg = "Patients with Missing EXTRT."
    
    # Return message if no records with missing EXTRT but EXOCCUR=Y
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        message = "Fail"
        notes = mymsg
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
def check_ex_infusion_exstdtc_exendtc(data_path):
    check_description = "Check for EXSTDTC and EXENDTC errors in intravenous infusions"
    datasets = "EX"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "EXTRT", "EXSTDTC", "EXENDTC", "EXROUTE"]

    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Filter for EXOCCUR if it exists
    if "EXOCCUR" in EX.columns:
        df = EX[EX["EXOCCUR"] == "Y"]
    else:
        df = EX
    no_exstdtc = EX['EXSTDTC'].apply(is_null_or_empty)
    no_exendtc = EX['EXSTDTC'].apply(is_null_or_empty)
    # Get minimum length for when EXSTDTC and EXENDTC are different lengths
    df["startdtc"] = df["EXSTDTC"].where(~no_exstdtc, None)
    df["enddtc"] = df["EXENDTC"].where(~no_exendtc, None)

    df["startdate"] = df["startdtc"].str[:10]
    df["enddate"] = df["enddtc"].str[:10]
    df["starttime"] = df["startdtc"].str[11:19]
    df["endtime"] = df["enddtc"].str[11:19]

    # Convert string to date/time
    df["DT1"] = pd.to_datetime(df["startdate"], errors='coerce')
    df["DT2"] = pd.to_datetime(df["enddate"], errors='coerce')
    df["TM1"] = pd.to_datetime(df["starttime"], format='%H:%M:%S', errors='coerce')
    df["TM2"] = pd.to_datetime(df["endtime"], format='%H:%M:%S', errors='coerce')

    # Include VISIT and EXOCCUR in display if they exist in the data set
    myvars = ["USUBJID", "EXTRT", "EXSTDTC", "EXENDTC"]
    if "VISIT" in EX.columns:
        myvars.append("VISIT")

    # Filter records where route is intravenous
    df_iv = df[df["EXROUTE"].str.upper().str.contains("INTRAVENOUS", na=False)]
    if df_iv.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Check stopped. This check will only for EXTRT = INTRAVENOUS"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        # Create check flags for date checks
        df_iv["check_stat"] = np.where(
            (df_iv["DT1"] != df_iv["DT2"]) & df_iv["TM1"].isna() & df_iv["TM2"].isna(), "Different Start/End date for Infusion",
            np.where(
                ~df_iv["DT1"].isna() & df_iv["TM1"].isna() & df_iv["EXENDTC"].isna(), "Missing End date",
                np.where(
                    ~df_iv["DT2"].isna() & df_iv["TM2"].isna() & df_iv["EXSTDTC"].isna(), "Missing Start date", ""
                )
            )
        )
    
        # Filter empty check flags
        mydf1 = df_iv[df_iv["check_stat"] != ""][myvars + ["check_stat"]]
    
        # Create check flags for date and time checks
        df_iv["check_stat"] = np.where(
            (df_iv["DT1"] == df_iv["DT2"]) & (df_iv["TM1"] > df_iv["TM2"]), "Same Start/End date but Start time after End time",
            np.where(
                (df_iv["DT1"] != df_iv["DT2"]) & (~df_iv["TM1"].isna()) & (~df_iv["TM2"].isna()), "Different Start/End date for Infusion",
                np.where(
                    ~df_iv["DT1"].isna() & ~df_iv["TM1"].isna() & df_iv["EXENDTC"].isna(), "Missing End date/time",
                    np.where(
                        ~df_iv["DT2"].isna() & ~df_iv["TM2"].isna() & df_iv["EXSTDTC"].isna(), "Missing Start date/time", ""
                    )
                )
            )
        )

    # Filter empty check flags
    mydf2 = df_iv[df_iv["check_stat"] != ""][myvars + ["check_stat"]]

    if mydf1.empty and mydf2.empty:
        return pass_check(check_description, datasets)
    else:
        stackeddf = pd.concat([mydf1, mydf2])
        stackeddf["check_flag"] = stackeddf["check_stat"].map({
            "Different Start/End date for Infusion": "A",
            "Missing End date": "B",
            "Missing Start date": "C",
            "Same Start/End date but Start time after End time": "D",
            "Different Start/End date for Infusion": "E",
            "Missing End date/time": "F",
            "Missing Start date/time": "G"
        })

        msg1 = f"{len(mydf1)} record(s) with issues on date checks" if not mydf1.empty else ""
        msg2 = f"{len(mydf2)} record(s) with issues on date/time checks" if not mydf2.empty else ""
        fmsg = f"EX has {msg1} and {msg2}." if msg1 and msg2 else (f"EX has {msg1}." if msg1 else f"EX has {msg2}.")

        return fail_check(check_description, datasets, fmsg, stackeddf)
def check_ex_visit(data_path):
    check_description = "Check for missing VISIT in EX"
    datasets = "EX"
    ex_file_path = os.path.join(data_path, "ex.sas7bdat")

    if os.path.exists(ex_file_path):
        EX = load_data(data_path, 'ex')
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EX dataset not found at the specified location: {ex_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "EXTRT", "EXSTDTC", "VISIT"]
    if not set(required_columns).issubset(EX.columns):
        missing = set(required_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    if "EXOCCUR" in EX.columns:
        mydf = EX[(EX["EXOCCUR"] == "Y") & (EX["VISIT"].apply(is_null_or_empty))][["USUBJID", "EXTRT", "EXSTDTC", "EXOCCUR", "VISIT"]].reset_index(drop=True)
    else:
        mydf = EX[EX["VISIT"].apply(is_null_or_empty)][["USUBJID", "EXTRT", "EXSTDTC", "VISIT"]].reset_index(drop=True)

    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"Total number of records is {len(mydf)}.", mydf)

def dose_overtime(data_path):
    data = load_data(data_path, 'ex')
    #data['StartDate'] = pd.to_datetime(data['EXSTDTC'])
    #data['EndDate'] = pd.to_datetime(data['EXENDTC'])
    #fig = px.timeline(data, x_start='EXSTDTC', x_end='EXENDTC', y='USUBJID', title='Treatment Administration Timeline')
    #fig.update_yaxes(title='Subjects')
    #fig.update_xaxes(title='Date')
    treatment_units = data.groupby('EXTRT')['EXDOSU'].unique().apply(lambda x: ', '.join(x))

    # Plot
    fig = px.line(
        data,
        x='EXSTDY',
        y='EXDOSE',
        color='USUBJID',
        facet_col='EXTRT',  # Create separate plots for each treatment
        title='Dose Over Time by Treatment'
    )

    # Update subplot titles dynamically for each treatment
    for annotation in fig.layout.annotations:
        treatment = annotation.text  # Extract treatment name from annotation
        if treatment in treatment_units.index:
            units = treatment_units[treatment]
            annotation.text = f"{treatment} (Dose in {units})"  # Add units to treatment name

    fig.update_xaxes(title='Study Day')
    fig.update_yaxes(title='Dose')
    #fig.show()
    return [dcc.Graph(figure=fig)]
def dose_cumdose(data_path):
    data = load_data(data_path, 'ex')
    data['CumulativeDose'] = data.groupby(['USUBJID', 'EXTRT'])['EXDOSE'].cumsum()

    # Plot cumulative dose histogram
    fig = px.histogram(
        data, 
        x='CumulativeDose', 
        color='EXTRT', 
        nbins=10, 
        title='Histogram of Cumulative Dose by Treatment'
    )

    fig.update_xaxes(title='Cumulative Dose (mg)')
    fig.update_yaxes(title='Frequency')
    return [dcc.Graph(figure=fig)]