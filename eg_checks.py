# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 10:26:51 2024

@author: inarisetty
"""

import pandas as pd 
import os 
from datetime import datetime

from utils import load_data,is_null_or_empty, is_null_or_empty2

def check_eg_egdtc_visit_ordinal_error(data_path):
    datasets = "EG"
    check_description = "Check for EGDTC and VISITNUM Ordinal Error"
    eg_file_path = os.path.join(data_path, "eg.sas7bdat")
    if  os.path.exists(eg_file_path):
        EG = load_data(data_path, 'eg')
        vars = ["USUBJID", "VISITNUM", "VISIT", "EGDTC", "EGSTAT"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to EG dataset not found at the specified location: {eg_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    

    # Helper function for duplicated and early date check
    def dtc_dupl_early(df, vars, groupby, dtc):
        df = df.sort_values(by=[vars[0], vars[1], vars[2], vars[3]])
        df['visit_order'] = df.groupby(groupby).cumcount() + 1
        df['dtc_order'] = df.groupby(groupby)[dtc].rank(method='dense')
        df['check_flag'] = df.apply(lambda x: 'Duplicated' if x['visit_order'] != x['dtc_order'] else None, axis=1)
        return df

    # Check if required variables exist
    if not set(vars).issubset(EG.columns):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns: {', '.join(set(vars) - set(EG.columns))}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Check if VISITNUM is all missing
    if len(EG["VISITNUM"].unique()) <= 1:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["VISITNUM exists but only a single value."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Filter EG data and run the check
    EG_filtered = EG[(EG["EGSTAT"] != "NOT DONE") & (~EG["VISIT"].str.contains("UNSCHEDU", case=False))]
    myout = dtc_dupl_early(EG_filtered, vars=vars, groupby=[vars[0]], dtc=vars[3])

    if not myout.empty:
        myout = myout.dropna(subset=["check_flag"])
        myout = myout[myout["check_flag"] != "Duplicated"]
    
    if myout.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        myout = myout.reset_index(drop=True)
        message = "Fail"
        notes = f"EG has {len(myout)} records with Possible EGDTC data entry error."
        myout.insert(0, "CHECK", check_description)
        myout.insert(1, "Message", message)
        myout.insert(2, "Notes", notes)
        myout.insert(3, "Datasets", datasets)
        return myout
       