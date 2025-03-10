# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 13:05:45 2024

@author: inarisetty
"""


import pandas as pd 
import os 
from datetime import datetime

from utils import load_data, is_null_or_empty, missing_month

def check_ce_missing_month(data_path, preproc=lambda df: df, **kwargs):
    ce_file_path = os.path.join(data_path, "ce.sas7bdat")
    datasets = "CE"
    if  os.path.exists(ce_file_path):
        CE = load_data(data_path, 'ce')
        
    else:
        return pd.DataFrame({
            "CHECK": ["Check for CE records with missing month in dates"],
            "Message": [f"Check stopped running due to CE dataset not found at the specified location: {ce_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    required_columns = ["USUBJID", "CETERM", ]
    date_columns = ["CESTDTC", "CEENDTC", "CEDTC"]
    
    # Check if required variables exist in CE
    if not set(required_columns).issubset(CE.columns):
        missing = set(required_columns) - set(CE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for CE records with missing month in dates"],
            "Message": [f"Missing columns in CE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    CE = preproc(CE, **kwargs)
    
    outlist = []
    
    # Process only the date columns that exist in CE
    for col in date_columns:
        if col in CE.columns:
            outlist.append(
                CE.loc[CE[col].apply(missing_month), ["USUBJID", "CETERM"] + [dc for dc in date_columns if dc in CE.columns]]
            )
    
    # Stack and get unique rows
    if outlist:
        mydf = pd.concat(outlist).drop_duplicates().reset_index(drop=True)
    else:
        mydf = pd.DataFrame()
    
    check_description = "Check for CE records with missing month in dates"
    
    # Return message if no records with missing month in dates
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    # Return subset dataframe if there are records with inconsistency
    message = "Fail"
    notes = f"{mydf['USUBJID'].nunique()} patient(s) with a clinical events date that has year and day present but missing month."
    mydf.insert(0, "CHECK", check_description)
    mydf.insert(1, "Message", message)
    mydf.insert(2, "Notes", notes)
    mydf.insert(3, "Datasets", datasets)
    return mydf