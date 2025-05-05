# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 13:52:58 2024

@author: inarisetty
"""

import pandas as pd 
import os 
from datetime import datetime

from utils import load_data, is_null_or_empty, missing_month

def check_dd_ae_aedthdtc_ds_dsstdtc(data_path, preproc=lambda df: df, **kwargs):
    dd_file_path = os.path.join(data_path, "dd.sas7bdat")
    
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    datasets = "DD, AE, DS"
    if os.path.exists(dd_file_path):
        DD = load_data(data_path, 'dd')
        required_dd_columns = ["USUBJID", "DDTEST", "DDORRES"]
        if DD.empty:
            return pd.DataFrame({
                "CHECK": ["Check for AE, DS and DD records with different death dates"],
                "Message": ["No records in DD dataset."],
                "Datasets": [datasets]
            })
    
    required_ae_columns = ["USUBJID", "AESTDTC","AESDTH", "AEOUT"]
    required_ds_columns = ["USUBJID", "DSDECOD", "DSSTDTC"]
    
    if AE.empty:
        return pd.DataFrame({
            "CHECK": ["Check for AE, DS and DD records with different death dates"],
            "Message": ["No records in AE dataset."],
            "Datasets": [datasets]
        })
    if DS.empty:
        return pd.DataFrame({
            "CHECK": ["Check for AE, DS and DD records with different death dates"],
            "Message": ["No records in DS dataset."],
            "Datasets": [datasets]
        })

    # Check if required variables exist in AE and DS
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE, DS and DD records with different death dates"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE, DS and DD records with different death dates"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    if os.path.exists(dd_file_path):
        if not set(required_dd_columns).issubset(DD.columns):
            missing = set(required_dd_columns) - set(DD.columns)
            return pd.DataFrame({
                "CHECK": ["Check for AE, DS and DD records with different death dates"],
                "Message": [f"Missing columns in DD: {', '.join(missing)}"],
                "Notes": [""],
                "Datasets": [datasets],
                "Data": [pd.DataFrame()]  # Return an empty DataFrame
            })    

    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    DS = preproc(DS, **kwargs)
    
    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)

    ae0 = AE[~AE["AEDTHDTC"].apply(is_null_or_empty)][["USUBJID", "AEDTHDTC"]]

    # From DS take DEATH records where DEATH date is populated
    ds0 = DS[(~DS["DSSTDTC"].apply(is_null_or_empty)) & (DS["DSDECOD"].str.contains("DEATH", case=False))][["USUBJID", "DSSTDTC"]]
    if os.path.exists(dd_file_path):
        ddtest_contains_cause = DD[
            (DD["DDTEST"].str.contains("cause", case=False, na=False)) & 
            (DD["DDORRES"] != "DISEASE PROGRESSION")
        ][["USUBJID", "DDTEST", "DDORRES"]]

    # Merge DS and AE and if death dates in both are different then output in mydf
    mydf0 = pd.merge(ds0, ae0, on="USUBJID", how="outer", suffixes=(".DS", ".AE"))
    mydf = mydf0[mydf0["AEDTHDTC"] != mydf0["DSSTDTC"]].drop_duplicates()[["USUBJID", "DSSTDTC", "AEDTHDTC"]]
    if os.path.exists(dd_file_path):
        mydf = pd.merge(mydf, ddtest_contains_cause, on="USUBJID", how="inner", suffixes=(".DS", ".AE"))
    mydf = mydf.reset_index(drop=True)

    check_description = "Check for AE, DS and DD records with different death dates"

    # Declare number of patients
    num_patients = mydf["USUBJID"].nunique()
    message = f"There are {num_patients} patients with a death date different in DS and AE."

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
         notes = f"There are {num_patients} patients with a death date different in AE, DS and DD."
         mydf.insert(0, "CHECK", check_description)
         mydf.insert(1, "Message", message)
         mydf.insert(2, "Notes", notes)
         mydf.insert(4, "Datasets", datasets)
         return mydf

    
def check_dd_ae_aeout_aedthdtc(data_path, preproc=lambda df: df, **kwargs):
    AE = load_data(data_path, 'ae')
    datasets = "AE"
    required_columns = ["USUBJID", "AEOUT", "AEDECOD", "AESTDTC"]
    if AE.empty:
        return pd.DataFrame({
            "CHECK": ["Check for AE records with discrepant AE outcome and AE death date"],
            "Message": ["No records in AE dataset."],
            "Datasets": [datasets]
        })
    # Check if required variables exist in AE
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE records with discrepant AE outcome and AE death date"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
    # Check if AEOUT=='FATAL' that there is a corresponding AEDTHDTC, death date
    # Check non-missing AEDTHDTC with AEOUT=='FATAL'
    mydf = AE[((AE["AEOUT"] == 'FATAL') & AE["AEDTHDTC"].apply(is_null_or_empty)) |
              ((~AE["AEDTHDTC"].apply(is_null_or_empty)) & ((AE["AEOUT"] != 'FATAL') | AE["AEOUT"].apply(is_null_or_empty)))]
    
    mydf = mydf[["USUBJID", "AEDECOD", "AESTDTC", "AEDTHDTC", "AEOUT"]].drop_duplicates().reset_index(drop=True)

    check_description = "Check for AE records with discrepant AE outcome and AE death date"

    if not mydf.empty:
        message = "Fail"
        notes = f"{len(mydf)} record(s) with a discrepant AE outcome and AE death date."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(4, "Datasets", datasets)
        return mydf
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
def check_dd_death_date(data_path, preproc=lambda df: df, **kwargs):
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    datasets = "AE, DS"
    required_ae_columns = ["USUBJID", "AESTDTC","AESDTH", "AEOUT"]
    required_ds_columns = ["USUBJID", "DSDECOD", "DSTERM"]
    if AE.empty:
        return pd.DataFrame({
            "CHECK": ["Check for AE death dates not reflected in DS"],
            "Message": ["No records in AE dataset."],
            "Datasets": [datasets]
        })
    if DS.empty:
        return pd.DataFrame({
            "CHECK": ["Check for AE death dates not reflected in DS"],
            "Message": ["No records in DS dataset."],
            "Datasets": [datasets]
        })
    # Check if required variables exist in AE and DS
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE death dates not reflected in DS"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE death dates not reflected in DS"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    DS = preproc(DS, **kwargs)
    
    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
    # Subset AE for recs with non-missing AE.AEDTHDTC
    ae0 = AE[~AE["AEDTHDTC"].apply(is_null_or_empty)][["USUBJID", "AETERM", "AESTDTC"]]

    # Select DEATH recs in DS, include DSDECOD contains DEATH and DSTERM containing DEATH
    # exclude DSTERM in (DEATH DUE TO PROGRESSIVE DISEASE, DEATH DUE TO DISEASE RELAPSE)
    ds0 = DS[(DS["DSDECOD"].str.contains("DEATH", case=False)) &
             (DS["DSTERM"].str.contains("DEATH", case=False)) &
             (~DS["DSTERM"].str.contains("PROGRESSIVE DISEASE", case=False)) &
             (~DS["DSTERM"].str.contains("DISEASE RELAPSE", case=False))][["USUBJID", "DSTERM", "DSDECOD"]]

    # Keep patients with AE DEATH who lack DS DEATH record
    mydfprep = pd.merge(ae0, ds0.drop_duplicates(), on="USUBJID", how="left")
    mydf = mydfprep[mydfprep["DSDECOD"].apply(is_null_or_empty)]

    check_description = "Check for AE death dates not reflected in DS"

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
        notes = f"{mydf['USUBJID'].nunique()} patient(s) with a death date in AE but death not reflected properly in DS."
        mydf = mydf.drop_duplicates().reset_index(drop=True)
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(4, "Datasets", datasets)
        return mydf
