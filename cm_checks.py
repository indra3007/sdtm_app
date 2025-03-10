# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 13:26:54 2024

@author: inarisetty
"""
import pandas as pd 
import os 
from datetime import datetime

from utils import load_data, is_null_or_empty, missing_month

def check_cm_cmdecod(data_path, preproc=lambda df: df, **kwargs):
    cm_file_path = os.path.join(data_path, "cm.sas7bdat")
    datasets = "CM"
    if  os.path.exists(cm_file_path):
        CM = load_data(data_path, 'cm')
        
    else:
        return pd.DataFrame({
            "CHECK": ["Check for CM records with missing CMDECOD"],
            "Message": [f"Check stopped running due to CM dataset not found at the specified location: {check_cm_cmdecod}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "CMTRT", "CMDECOD", "CMCAT"]

    # Check if required variables exist in CM
    if not set(required_columns).issubset(CM.columns):
        missing = set(required_columns) - set(CM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for CM records with missing CMDECOD"],
            "Message": [f"Missing columns in CM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    CM = preproc(CM, **kwargs)

    # Subset domain to only records with missing coded term (CMDECOD)
    mydf = CM[CM["CMCAT"].str.contains("CONCOMITANT", na=False) & CM["CMDECOD"].isna()]
    mydf = mydf[["USUBJID", "CMSTDTC", "CMTRT", "CMDECOD"]]
    mydf = mydf.reset_index(drop=True)

    check_description = "Check for CM records with missing CMDECOD"

    # Return message if no records with missing CMDECOD
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        message = "Fail"
        # Return subset dataframe if there are records with missing CMDECOD
        notes = f"CM has {len(mydf)} record(s) with missing CMDECOD."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
def check_cm_cmindc(data_path, preproc=lambda df: df, **kwargs):
    cm_file_path = os.path.join(data_path, "cm.sas7bdat")
    datasets = "CM"
    if  os.path.exists(cm_file_path):
        CM = load_data(data_path, 'cm')
        
    else:
        return pd.DataFrame({
            "CHECK": ["Check for CM records with missing CMDECOD"],
            "Message": [f"Check stopped running due to CM dataset not found at the specified location: {check_cm_cmdecod}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "CMTRT", "CMSTDTC", "CMINDC", "CMPROPH"]

    # Check if required variables exist in CM
    if not set(required_columns).issubset(CM.columns):
        missing = set(required_columns) - set(CM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for CM records with prophylactic indication"],
            "Message": [f"Missing columns in CM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    CM = preproc(CM, **kwargs)


    # Keep records not indicated as prophylactic via CMPROPH
    cmNP = CM[CM["CMPROPH"].isna()]
    cmNP = cmNP[["USUBJID"]  + ["CMTRT", "CMSTDTC", "CMINDC", "CMPROPH"]]

    mydf = cmNP[cmNP["CMINDC"].str.upper().str.contains("PROPHYL", na=False)]
    mydf = mydf.reset_index(drop=True)

    check_description = "Check for CM records with prophylactic indication"

    # Check
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        message = "Fail"
        # Return subset dataframe if there are records with inconsistency
        notes = f"There are {mydf['USUBJID'].nunique()} patients with CM indication containing 'PROPHYL' when given for prophylaxis variable is not checked as 'Y'."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
def check_cm_cmlat(data_path, preproc=lambda df: df, **kwargs):
    cm_file_path = os.path.join(data_path, "cm.sas7bdat")
    datasets = "CM"
    if  os.path.exists(cm_file_path):
        CM = load_data(data_path, 'cm')
        
    else:
        return pd.DataFrame({
            "CHECK": ["Check for CM records with missing or inconsistent CMLAT"],
            "Message": [f"Check stopped running due to CM dataset not found at the specified location: {check_cm_cmdecod}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "CMCAT", "CMLAT", "CMTRT", "CMDECOD", "CMROUTE"]

    # Check if required variables exist in CM
    if not set(required_columns).issubset(CM.columns):
        missing = set(required_columns) - set(CM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for CM records with missing or inconsistent CMLAT"],
            "Message": [f"Missing columns in CM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    CM = preproc(CM, **kwargs)

    perm_var = ["CMSTDTC"]
    int_var = list(set(CM.columns).intersection(perm_var))

    eye_related_routes = ["OPHTHALMIC", "INTRAVITREAL", "INTRAOCULAR",
                          "CONJUNCTIVAL", "INTRACAMERAL", "INTRACORNEAL",
                          "RETROBULBAR", "SUBTENON", "SUBRETINAL", "SUBCONJUNCTIVAL"]
    
    cmlat_values = ["LEFT", "RIGHT", "BILATERAL"]

    CM['MISFLAG'] = CM.apply(
        lambda row: 1 if (
            (row['CMROUTE'].upper() in eye_related_routes and row['CMLAT'].upper() not in cmlat_values) or
            (row['CMROUTE'].upper() not in eye_related_routes and row['CMLAT'].upper() in cmlat_values)
        ) else 0, axis=1
    )

    my_select_var = ["USUBJID"] + int_var + ["CMLAT", "CMTRT", "CMDECOD", "CMROUTE", "MISFLAG"]
    mydf = CM.loc[CM['CMCAT'] == "CONCOMITANT MEDICATIONS", my_select_var]

    mydf = mydf[mydf['MISFLAG'] == 1].drop(columns=["MISFLAG"]).reset_index(drop=True)

    check_description = "Check for CM records with missing or inconsistent CMLAT"

    # Check
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        message = "Fail"
        # Return subset dataframe if there are records with inconsistency
        notes = f"{len(mydf)} record(s) with CMLAT Missing when CM is Eye related, or CMLAT is LEFT/RIGHT/BILATERAL and CMROUTE is not Eye related."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf

def check_cm_missing_month(data_path, preproc=lambda df: df, **kwargs):
    cm_file_path = os.path.join(data_path, "cm.sas7bdat")
    datasets = "CM"
    if  os.path.exists(cm_file_path):
        CM = load_data(data_path, 'cm')
        
    else:
        return pd.DataFrame({
            "CHECK": ["Check for CM records with missing month in dates"],
            "Message": [f"Check stopped running due to CM dataset not found at the specified location: {check_cm_cmdecod}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "CMTRT", "CMSTDTC", "CMENDTC"]

    # Check if required variables exist in CM
    if not set(required_columns).issubset(CM.columns):
        missing = set(required_columns) - set(CM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for CM records with missing month in dates"],
            "Message": [f"Missing columns in CM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    CM = preproc(CM, **kwargs)

    # Check if CMSTDTC or CMENDTC has missing month and is in format 'yyyy---dd'
    mydf = CM.loc[CM["CMSTDTC"].apply(missing_month) | CM["CMSTDTC"].apply(missing_month)]
   

    mydf = mydf[["USUBJID", "CMTRT", "CMSTDTC", "CMENDTC"]]
    mydf = mydf.reset_index(drop=True)

    check_description = "Check for CM records with missing month in dates"

    # Return message if no records with missing month in dates
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        message = "Fail"
        # Return subset dataframe if there are records with inconsistency
        notes = f"There are {mydf['USUBJID'].nunique()} patient(s) with a conmed date that has year and day present but missing month."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf