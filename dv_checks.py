# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 15:35:49 2024

@author: inarisetty
"""
import pandas as pd 
import os 
from datetime import datetime

from utils import load_data,is_null_or_empty, is_null_or_empty2

def check_dv_ae_aedecod_covid(data_path, covid_terms=["COVID-19", "CORONAVIRUS POSITIVE"]):
    datasets = "DV, AE"
    dv_file_path = os.path.join(data_path, "dv.sas7bdat")
    if  os.path.exists(dv_file_path):
        DV = load_data(data_path, 'dv')
        required_dv_columns = ["USUBJID", "DVTERM"]
    else:
        return pd.DataFrame({
            "CHECK": ["Check for COVID-19 related terms in AE and DV"],
            "Message": [f"Check stopped running due to DV dataset not found at the specified location: {dv_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    AE = load_data(data_path, 'ae')
    if (covid_terms is None or 
        not isinstance(covid_terms, list) or 
        len(covid_terms) < 1 or 
        all(map(is_null_or_empty, covid_terms))):
        return pd.DataFrame({
            "CHECK": ["Check for COVID-19 related terms in AE and DV"],
            "Message": ["Check not run, did not detect COVID-19 preferred terms. Character vector of terms expected."],
            "Notes": [""],            
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    required_ae_columns = ["USUBJID", "AEDECOD"]
    

    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for COVID-19 related terms in AE and DV"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_dv_columns).issubset(DV.columns):
        missing = set(required_dv_columns) - set(DV.columns)
        return pd.DataFrame({
            "CHECK": ["Check for COVID-19 related terms in AE and DV"],
            "Message": [f"Missing columns in DV: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if covid_terms == ["COVID-19", "CORONAVIRUS POSITIVE"]:
        outmsg = "Default terms used for identifying COVID AEs: COVID-19, CORONAVIRUS POSITIVE"
    else:
        outmsg = ""

    # Select AE records with COVID-related terms
    ae0 = AE[AE["AEDECOD"].str.upper().isin(map(str.upper, covid_terms))][["USUBJID", "AEDECOD"]]

    # Select DV records with relevant reasons
    dv0 = DV[DV["DVTERM"].str.contains('SUSPECTED EPIDEMIC/PANDEMIC INFECTION', case=False, na=False)][["USUBJID", "DVTERM"]]

    # Merge to find discrepancies
    mydfprep = pd.merge(dv0.drop_duplicates(), ae0.drop_duplicates(), on="USUBJID", how="left")
    mydf = mydfprep[pd.isna(mydfprep["AEDECOD"])]

    check_description = "Check for COVID-19 related terms in AE and DV"

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
        notes = f"Found {len(mydf['USUBJID'].unique())} patient(s) with COVID-related Protocol Deviation, but no AE record with COVID terms. {outmsg}"
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
    
        return mydf
def check_dv_covid(data_path):
    datasets = "DV"
    dv_file_path = os.path.join(data_path, "dv.sas7bdat")
    if  os.path.exists(dv_file_path):
        DV = load_data(data_path, 'dv')
        required_columns = ["USUBJID", "DVTERM", "DVEPRELI"]
    else:
        return pd.DataFrame({
            "CHECK": ["Check for COVID-19 related inconsistencies in DV"],
            "Message": [f"Check stopped running due to DV dataset not found at the specified location: {dv_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    if not set(required_columns).issubset(DV.columns):
        missing = set(required_columns) - set(DV.columns)
        return pd.DataFrame({
            "CHECK": ["Check for COVID-19 related inconsistencies in DV"],
            "Message": [f"Missing columns in DV: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Select DV records where there are inconsistencies between DVREAS and DVEPRELI
    mydf = DV[(DV["DVEPRELI"] != "Y") & (~DV["DVREAS"].apply(is_null_or_empty2)) |
              (DV["DVEPRELI"] == "Y") & (DV["DVREAS"].apply(is_null_or_empty2))][["USUBJID", "DVTERM", "DVEPRELI"]]

    check_description = "Check for COVID-19 related inconsistencies in DV"

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
        notes = f"Found {len(mydf['USUBJID'].unique())} patient(s) with COVID-related Protocol Deviation inconsistencies."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf