# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 12:56:22 2024

@author: inarisetty
"""
import pandas as pd 
import os 
from datetime import datetime
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from dash import html
#from utils import load_data,is_null_or_empty, is_null_or_empty2
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month, convert_date, format_dates
def check_dm_actarm_arm(data_path):
    datasets = "DM"
    DM = load_data(data_path, 'dm')
    required_columns = ["USUBJID", "ARM", "ACTARM", "ARMNRS"]
    check_description = "This check looks for DM entries where ARM is not equal to ACTARM"
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist
    missing = set(required_columns) - set(DM.columns)
    if missing:
        print(f"Warning: Missing columns in DM: {missing}")
        # Use only available columns for the check
        available_columns = list(set(required_columns) - missing)
    else:
        available_columns = required_columns

    # Filter rows where ARM != ACTARM (if both columns exist)
    if "ARM" in DM.columns and "ACTARM" in DM.columns:
        df = DM.loc[DM["ARM"] != DM["ACTARM"], available_columns]
    else:
        # If either "ARM" or "ACTARM" is missing, the check cannot proceed
        return pass_check(
            "This check cannot be performed due to missing ARM or ACTARM columns.",
            datasets
        )

    # Add check description column
    check_description = "This check looks for DM entries where ARM is not equal to ACTARM"

    if df.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"{len(df['USUBJID'].unique())} patient(s) where ARM is not equal to ACTARM"
        return fail_check(check_description, datasets, notes, df)


    
def check_dm_ae_ds_death(data_path):
    datasets = "AE, DS, DM"
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    DM = load_data(data_path, 'dm')
    
    required_ae_columns = ["USUBJID", "AETERM", "AESTDTC", "AEOUT", "AESDTH"]
    required_ds_columns = ["USUBJID", "DSDECOD", "DSSTDTC"]
    required_dm_columns = ["USUBJID", "DTHFL", "DTHDTC"]

    # Check if required variables exist in AE, DS, and DM
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for death information consistency across DM, DS, and AE"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for death information consistency across DM, DS, and AE"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_dm_columns).issubset(DM.columns):
        missing = set(required_dm_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for death information consistency across DM, DS, and AE"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
    # Get death information from AE, DS, DM
    if "AETOXGR" in AE.columns:
        aedth = AE[(~AE["AESTDTC"].apply(is_null_or_empty)) | 
                   (AE["AESDTH"] == "Y") | 
                   (AE["AEOUT"] == "FATAL") | 
                   (AE["AETOXGR"] == "5")][["USUBJID", "AETERM", "AESTDTC", "AETOXGR", "AESDTH", "AEOUT"]]
    else:
        aedth = AE[(~AE["AESTDTC"].apply(is_null_or_empty)) | 
                   (AE["AESDTH"] == "Y") | 
                   (AE["AEOUT"] == "FATAL")][["USUBJID", "AETERM", "AESTDTC", "AESDTH", "AEOUT"]]

    dsdth = DS[DS["DSDECOD"] == "DEATH"][["USUBJID", "DSSTDTC"]]
    dmdth = DM[(~DM["DTHDTC"].apply(is_null_or_empty)) | (DM["DTHFL"] == "Y")][["USUBJID", "DTHDTC", "DTHFL"]]

    # Get earliest AE death record
    if not aedth.empty:
        aedths = aedth.sort_values(by=["USUBJID", "AESTDTC"]).drop_duplicates()
    else:
        aedths = aedth

    # Get earliest DS death record
    if not dsdth.empty:
        dsdths = dsdth.sort_values(by=["USUBJID", "DSSTDTC"]).drop_duplicates()
    else:
        dsdths = dsdth

    # JOIN AE and DS deaths
    aeds = pd.merge(aedths, dsdths, on="USUBJID", how="outer")

    # Get only DM deaths not reported in AE or DS
    mydf = dmdth[~dmdth["USUBJID"].isin(aeds["USUBJID"])]
    mydf = mydf.reset_index(drop=True)

    check_description = "Check for death information consistency across DM, DS, and AE"

    # Return message
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"{len(mydf['USUBJID'].unique())} patient(s) where DM data indicates death but no record indicating death in DS or AE."
        mydf = mydf.merge(aeds, on="USUBJID", how="left", suffixes=(".DM", ".AE_DS"))
        return fail_check(check_description, datasets, notes,mydf)

def check_dm_age_missing(data_path):
    datasets = "DM"
    DM = load_data(data_path, 'dm')
    required_columns = ["USUBJID", "AGE","ARM","ACTARM"]
    check_description = "Check for missing or suspicious age values in DM, Checking age <18 and >=90, if study allow, ignore this check"
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM
    if not set(required_columns).issubset(DM.columns):
        missing = set(required_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for missing or suspicious age values in DM, Checking age <18 and >=90, if study allow, ignore this check"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset DM to only records with missing AGE
    if "ARMNRS"  in DM.columns:
        mydf_0 = DM[DM["AGE"].apply(is_null_or_empty)][["USUBJID", "AGE", "ARM","ACTARM","ARMNRS"]]
    else:
        mydf_0 = DM[DM["AGE"].apply(is_null_or_empty)][["USUBJID", "AGE", "ARM","ACTARM"]]
        
    # Subset DM to only records with AGE < 18
    mydf_1 = DM[(~DM["AGE"].apply(is_null_or_empty)) & (DM["AGE"] < 18)][["USUBJID", "AGE"]]

    # Subset DM to only records with AGE >= 90
    mydf_2 = DM[(~DM["AGE"].apply(is_null_or_empty)) & (DM["AGE"] >= 90)][["USUBJID", "AGE"]]

    # Combine records with abnormal AGE
    mydf = pd.concat([mydf_0, mydf_1, mydf_2]).sort_values(by="USUBJID").reset_index(drop=True)

    check_description = "Check for missing or suspicious age values in DM, Checking age <18 and >=90, if study allow, ignore this check"

    # Return message if no records with missing AGE, AGE < 18, or AGE >= 90
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:  
        # Return subset dataframe if there are records with missing AGE, AGE < 18, or AGE >= 90
        notes = f"DM has {len(mydf['USUBJID'].unique())} patient(s) with suspicious age value(s). ***Checks for Age <18 and Age >=90***"
        return fail_check(check_description, datasets, notes,mydf_1)

def check_dm_armnrs_missing(data_path):
    datasets = "DM"
    check_description = "Check for ARMNRS Variable if ARMCD = SCRNFAIL"
    DM = load_data(data_path, 'dm')
    required_columns = ["USUBJID","ARM","ARMCD"]
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM
    if not set(required_columns).issubset(DM.columns):
        missing = set(required_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for ARMNRS Variable if ARMCD = SCRNFAIL"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    if "ARMNRS" in DM.columns:
        mydf_1 = DM[((DM["ARMCD"] == "SCRNFAIL") | (DM["ARMCD"] == "")) & is_null_or_empty2(DM["ARMNRS"])][["USUBJID", "ARMCD", "ARM", "ARMNRS"]]
        check_description = "Check for ARMNRS Variable if ARMCD = SCRNFAIL"
        if not mydf_1.empty:
            notes = "ARMNRS is missing where ARMCD = SCRNFAIL or empty"
            return fail_check(check_description, datasets, notes,mydf_1)

    else:
        mydf_1 = DM[(DM["ARMCD"] == "SCRNFAIL") | (DM["ARMCD"] == "")][["USUBJID", "ARMCD", "ARM"]]
        required_columns = ["USUBJID", "AGE", "ARM", "ACTARM"]
        
        if not set(required_columns).issubset(DM.columns):
            missing = set(required_columns) - set(DM.columns)
            check_description = "Check for ARMNRS Variable if ARMCD = SCRNFAIL"
            #message = "Fail"
            notes = f"SCRNFAIL value found in ARMCD, Missing columns in DM: {', '.join(missing)}"
            return fail_check(check_description, datasets, notes,mydf_1)

        else:
            check_description = "ARMCD Should not be SCRNFAIL. It should populate in ARMNRS and ARMCD set to NULL"
            #message = "Fail"
            notes = f"DM has {len(mydf_1['USUBJID'].unique())} patient(s) with ARMCD = SCRNFAIL"
            return fail_check(check_description, datasets, notes,mydf_1)

    return pd.DataFrame({
        "CHECK": ["Check for ARMNRS Variable if ARMCD = SCRNFAIL"],
        "Message": ["Pass"],
        "Notes": [""],
        "Datasets": [datasets],
        "Data": [pd.DataFrame()]  # Return an empty DataFrame
    })
def check_dm_armcd(data_path):
    datasets = "DM"
    check_description = "Check for missing ARM or ARMCD values in DM"
    DM = load_data(data_path, 'dm')  # Ensure load_data function is defined
    required_columns = ["USUBJID", "ARM", "ARMCD", "ARMNRS"]
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM 
    if not set(required_columns).issubset(DM.columns):
        missing = set(required_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for missing ARM or ARMCD values in DM"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset DM to only records with missing ARM and ARMCD
    missing_arm_or_armcd = DM[
        DM["ARM"].apply(is_null_or_empty) & DM["ARMCD"].apply(is_null_or_empty)
    ]

    # Check if there are records where ARM and ARMCD are missing
    if not missing_arm_or_armcd.empty:
        if "ARMNRS" not in DM.columns:
            return pd.DataFrame({
                "CHECK": ["Check for missing ARM or ARMCD values in DM"],
                "Message": ["Fail"],
                "Notes": ["'ARMNRS' column is missing."],
                "Datasets": [datasets],
                "Data": [missing_arm_or_armcd[["USUBJID", "ARM", "ARMCD"]].reset_index(drop=True)]
            })
        
        # Further check if ARMNRS is also missing or equals "SCREEN FAILURE"
        fail_condition = missing_arm_or_armcd[
            ~missing_arm_or_armcd["ARMNRS"].apply(is_null_or_empty) & (missing_arm_or_armcd["ARMNRS"] != "SCREEN FAILURE")
        ]

        # If any records do not pass the check, return a failure message
        if not fail_condition.empty:
            notes = f"Total number of patients with missing ARM/ARMCD but unexpected ARMNRS values is {len(fail_condition)}."
            return fail_check("Check for missing ARM or ARMCD values in DM", datasets, notes, fail_condition[["USUBJID", "ARM", "ARMCD", "ARMNRS"]].reset_index(drop=True))
    
    # Pass if no invalid records are found
    return pass_check("Check for missing ARM or ARMCD values in DM", datasets)

def check_dm_arm_scrnfl(data_path):
    datasets = "DM"
    check_description = "Check for missing ARM or ARMCD values in DM"
    DM = load_data(data_path, 'dm')
    required_columns = ["USUBJID", "ARM", "ARMCD"]
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM
    if not set(required_columns).issubset(DM.columns):
        missing = set(required_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for missing ARM or ARMCD values in DM"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset DM to only records with missing ARM or ARMCD
    scrnfl_arm_or_armcd = DM[DM["ARM"] == "SCRNFAIL"]

    # Check if there are any records with missing ARM or ARMCD
    if not scrnfl_arm_or_armcd.empty:
        if "ARMNRS" not in DM.columns:
            return pd.DataFrame({
                "CHECK": ["Check for SCRNFAIL in ARM or ARMCD values in DM"],
                "Message": ["Fail"],
                "Notes": ["'ARMNRS' column is missing."],
                "Datasets": [datasets],
                "Data": [scrnfl_arm_or_armcd[["USUBJID", "ARM", "ARMCD"]].reset_index(drop=True)]
            })

        # Update ARMNRS to "SCRNFAIL" for records with missing ARM or ARMCD
        #DM.loc[DM["ARM"].apply(is_null_or_empty) | DM["ARMCD"].apply(is_null_or_empty), "ARMNRS"] = "SCRNFAIL"
        armnrs_arm_or_armcd = DM[DM["ARMCD"].apply(is_null_or_empty) & DM["ARMNRS"] == "SCRNFAIL"]
        check_description = "Check for SCRNFAIL in ARMNRS in DM"
    
        # Return message if no records with missing ARM or ARMCD
        if not armnrs_arm_or_armcd.empty:
            return pass_check(check_description, datasets)
        else:
            # Return subset dataframe if there are records with missing ARM or ARMCD
            notes = "Total number of patients with missing ARMNRS when ARM/ARMCD present"
            mydf = armnrs_arm_or_armcd[["USUBJID", "ARM", "ARMCD", "ARMNRS"]].reset_index(drop=True)
            return fail_check(check_description, datasets, notes,mydf)
    else:
        check_description = "Check for SCRNFAIL in ARMNRS in DM"
        notes = "SCRNFAIL value present in ARM, check if the IG version, it should follow below 3.3"
        return fail_check(check_description, datasets, notes)
        

def check_dm_dthfl_dthdtc(data_path):

    DM = load_data(data_path, 'dm')
    datasets = "DM"
    required_columns = ["USUBJID", "DTHFL", "DTHDTC"]
    check_description = "Check for consistency between DTHFL and DTHDTC in DM"
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM
    if not set(required_columns).issubset(DM.columns):
        missing = set(required_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency between DTHFL and DTHDTC in DM"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets" : [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset DM to only records with inconsistency between DTHFL and DTHDTC
    mydf = DM[(DM["DTHFL"] == "Y") & DM["DTHDTC"].apply(is_null_or_empty) |
              (DM["DTHFL"] != "Y") & ~DM["DTHDTC"].apply(is_null_or_empty)][["USUBJID", "DTHFL", "DTHDTC"]]

    check_description = "Check for consistency between DTHFL and DTHDTC in DM"

    # Return message if no records with potential data issue
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        # Return subset dataframe if there are records with potential data issue
        notes = f"DM has {len(mydf)} records with inconsistent values of DTHFL and DTHDTC."
        return fail_check(check_description, datasets, notes,mydf)
   

def check_dm_usubjid_ae_usubjid(data_path):
    DM = load_data(data_path, 'dm')
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    EX = load_data(data_path, 'ex')
    
    
    datasets = "DM, AE, DS, EX"
    required_dm_columns = ["USUBJID", "ARM"]
    required_ae_columns = ["USUBJID","AETERM","AESTDTC"]
    required_ds_columns = ["USUBJID", "DSSTDTC", "DSDECOD"]
    required_ex_columns = ["USUBJID", "EXSTDTC", "EXDOSE", "EXTRT"]
    check_description = "Check for consistency of USUBJID across DM, AE, DS, and EX"
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM, AE, DS, and EX
    if not set(required_dm_columns).issubset(DM.columns):
        missing = set(required_dm_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency of USUBJID across DM, AE, DS, and EX"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets" : [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency of USUBJID across DM, AE, DS, and EX"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets" : [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency of USUBJID across DM, AE, DS, and EX"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets" : [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ex_columns).issubset(EX.columns):
        missing = set(required_ex_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency of USUBJID across DM, AE, DS, and EX"],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets" : [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    DM["ARM"] = DM["ARM"].str.upper()
    if "ARMNRS" in DM.columns:
        DM = DM[
            ~DM["ARM"].isin(["SCREEN FAILURE", " ", "NOT ASSIGNED"]) &
            ~DM["ARMNRS"].isin(["SCREEN FAILURE", " ", "NOT ASSIGNED"])
        ]
        dm_no_ae = DM[~DM["USUBJID"].isin(AE["USUBJID"])][["USUBJID",'ARM', "ARMNRS"]].reset_index(drop=True)
    else:
        DM = DM[
            ~DM["ARM"].isin(["SCREEN FAILURE", " ", "NOT ASSIGNED"])]
        dm_no_ae = DM[~DM["USUBJID"].isin(AE["USUBJID"])][["USUBJID",'ARM']].reset_index(drop=True)
    

    # Return message if all USUBJIDs in DM also exist in AE
    if dm_no_ae.empty:
        check_description = "Check for consistency of USUBJID across DM, AE, DS, and EX"
        return pass_check(check_description, datasets)
    else:
    
        # Obtain first treatment start date for these patients
        if "EXOCCUR" in EX.columns:
            EX = EX[EX["EXOCCUR"] == "Y"]
    
        myex = EX[(~EX["EXSTDTC"].apply(is_null_or_empty)) &
                  ((EX["EXDOSE"] > 0) | ((EX["EXDOSE"] == 0) & EX["EXTRT"].str.contains("PLACEBO", case=False))) &
                  (EX["USUBJID"].isin(dm_no_ae["USUBJID"]))][["USUBJID", "EXSTDTC"]]
    
        myex["rank"] = myex.groupby("USUBJID")["EXSTDTC"].rank(method="first")
        ex_first = myex[myex["rank"] == 1].drop(columns=["rank"])
    
        # Obtain earliest death date for these patients
        myds = DS[(~DS["DSSTDTC"].apply(is_null_or_empty)) &
                  (DS["DSDECOD"] == "DEATH") &
                  (DS["USUBJID"].isin(dm_no_ae["USUBJID"]))][["USUBJID", "DSDECOD", "DSSTDTC"]]
    
        myds["rank"] = myds.groupby("USUBJID")["DSSTDTC"].rank(method="first")
        myds_first = myds[myds["rank"] == 1].drop(columns=["rank"])
    
        dm_ex_ds = pd.merge(dm_no_ae, ex_first, on="USUBJID", how="left")
        dm_ex_ds = pd.merge(dm_ex_ds, myds_first, on="USUBJID", how="left")
    
        # Replace NaN with blank
        dm_ex_ds = dm_ex_ds.fillna("")
    
        check_description = "Check for consistency of USUBJID across DM, AE, DS, and EX"
    

        notes = f"There is/are {len(dm_ex_ds)} patient(s) in DM without Adverse Events reported."
        return fail_check(check_description, datasets, notes,dm_ex_ds)

def check_dm_usubjid_dup(data_path):
    DM = load_data(data_path, 'dm')
    datasets = "DM"
    required_columns = ["USUBJID"]
    check_description = "Check for consistency of USUBJID across DM, AE, DS, and EX"
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM
    if not set(required_columns).issubset(DM.columns):
        missing = set(required_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for duplicate USUBJID in DM"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets" : [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Select USUBJID column
    DM2 = DM[["USUBJID"]].copy()

    # Identify duplicate USUBJID
    DM2["FLAG"] = ["Duplicate USUBJID" if DM2["USUBJID"].duplicated().iloc[i] else "" for i in range(len(DM2))]

    # Derive patient number for USUBJID not identified as duplicates
    DM2["subject_id"] = DM2.apply(lambda row: "" if row["FLAG"] else row["USUBJID"], axis=1)

    # Identify duplicate patient numbers across different USUBJIDs
    DM3 = DM2.groupby("subject_id").apply(lambda x: x.assign(n=len(x))).reset_index(drop=True)

    DM3["FLAG"] = DM3.apply(lambda row: "Same Patient Number Across Different USUBJID" if row["FLAG"] == "" and row["n"] > 1 else row["FLAG"], axis=1)

    DM4 = DM3[DM3["FLAG"] != ""].drop(columns=["subject_id", "n"])

    check_description = "Check for duplicate USUBJID in DM"

    if not DM4.empty:
        # Return subset dataframe if there are records with potential data issue
        notes = ["Duplicate USUBJID and/or same Patient number across different USUBJIDs"] * len(DM4)
        return fail_check(check_description, datasets, notes,DM4)
    else:
        return pass_check(check_description, datasets)
    
def check_dm_ds_icdtc(data_path):

    DM = load_data(data_path, 'dm')
    DS = load_data(data_path, 'ds')
    datasets = "DM, DS"
    required_columns = ["USUBJID", "RFICDTC"]
    required_columns_ds = ["USUBJID", "DSTERM", 'DSSTDTC']
    check_description = "Check for consistency Informed consent dates between RFICDTC and DSSTDTC"
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM
    if not set(required_columns).issubset(DM.columns):
        missing = set(required_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency Informed consent dates between RFICDTC and DSSTDTC"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets" : [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    if not set(required_columns_ds).issubset(DS.columns):
        missing = set(required_columns_ds) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency Informed consent dates between RFICDTC and DSSTDTC"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets" : [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Subset DM to only records with inconsistency between DTHFL and DTHDTC
    mydm = DM[["USUBJID", "RFICDTC"]]
    myds = DS[(~DS["DSSTDTC"].apply(is_null_or_empty)) & (DS["DSDECOD"] == "INFORMED CONSENT")][["USUBJID", "DSSTDTC"]]

    # Merge DM and DS on USUBJID
    mydf = pd.merge(mydm, myds, on="USUBJID", how="inner")

    # Calculate the difference between RFICDTC and DSSTDTC
    mydf["Date_Difference"] = pd.to_datetime(mydf["RFICDTC"]) - pd.to_datetime(mydf["DSSTDTC"])

    # Description for the check
    check_description = "Check for consistency in informed consent dates between RFICDTC and DSSTDTC"

    # Return message if no records with potential data issue
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        # Return subset DataFrame if there are records with potential data issues
        inconsistent_records = mydf[mydf["Date_Difference"].dt.days != 0]  # filter only non-zero differences
        notes = f"DM has {len(inconsistent_records)} records with inconsistent values of RFICDTC and DSSTDTC."
        return fail_check(check_description, datasets, notes, inconsistent_records)
def check_dm_rficdtc(data_path):
    datasets = "DM"
    DM = load_data(data_path, 'dm')  # Ensure load_data function is defined
    required_columns = ["USUBJID", "RFICDTC", "ARMCD", "ARM"]
    check_description = "Check for missing RFICDTC values in DM"
    if DM.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["DM dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Check if required variables exist in DM 
    if not set(required_columns).issubset(DM.columns):
        missing = set(required_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": ["Check for missing RFICDTC values in DM"],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset DM to only records with missing ARM and ARMCD
    missing_rficdtc = DM[DM["RFICDTC"].apply(lambda x: pd.isna(x) or x == "")]
    

        # If any records do not pass the check, return a failure message
    if not missing_rficdtc.empty:
        notes = f"Total number of patients with missing RFICDTC values is {len(missing_rficdtc)}."
        return fail_check("Check for missing RFICDTC values in DM", datasets, notes, missing_rficdtc[["USUBJID", "RFICDTC", "ARM", "ARMCD"]].reset_index(drop=True))
    else:
        # Pass if no invalid records are found
        return pass_check("Check for missing RFICDTC values in DM", datasets)
    # dm_plots.py

def generate_dm_plots(data_path):
    df = load_data(data_path, 'dm')
    df = df.fillna("Missing")  # Replace missing values
    plots = []
    variables_to_check = ['RACE', 'ETHNIC', 'DTHFL', 'ARM', 'ACTARM', 'ARMNRS', 'SEX']
    
    # Replace empty strings with 'Missing' for specified variables
    for var in variables_to_check:
        if var in df.columns:
            df[var] = df[var].replace('', 'Missing').fillna('Missing')

    # Unique subject count
    unique_subject_count = df['USUBJID'].nunique()

    # Bar plots
    bar_variables = ['RACE', 'ETHNIC']
    for var in bar_variables:
        if var in df.columns:
            df[var] = df[var].str.upper()
            group_counts = df.groupby(var)['SUBJID'].nunique().reset_index()
            group_percentages = group_counts['SUBJID'] / df['SUBJID'].nunique() * 100
            group_counts['percentage'] = group_percentages
            labels = [f"{count} ({percentage:.2f}%)" for name, count, percentage in zip(group_counts[var], group_counts['SUBJID'], group_counts['percentage'])]
            
            fig_bar = px.bar(group_counts, x=var, y='SUBJID', color=var, text=labels, color_discrete_sequence=px.colors.qualitative.Set1)
            fig_bar.update_layout(
                title=f'Bar Chart of {var}', 
                xaxis_title=var, 
                yaxis_title='Subject Count',
                legend_title_text=var,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.3,
                    xanchor="center",
                    x=0.5,
                    title_font_size=12,
                    font_size=10,
                    font_family="Arial",
                    itemwidth=60,
                    tracegroupgap=5
                )
            )
            plots.append(dcc.Graph(id=f'{var}-distribution', figure=fig_bar))

    # Donut plots
    donut_variables = ['ARM', 'ACTARM', 'ARMNRS', 'SEX', 'ETHNIC', 'DTHFL']
    for var in donut_variables:
        if var not in df.columns:
            continue

        # Handle DTHFL to only create plot if there are 'Y' values
        if var == 'DTHFL' and 'Y' not in df['DTHFL'].values:
            continue  

        # Get value counts and ignore case for "Screen Failure"
        value_counts = df[var].str.upper().value_counts()
        labels = value_counts.index
        values = value_counts.values
        
        # Emphasize "Screen Failure" in the legend
        pull = [0.2 if label.upper() == "SCREEN FAILURE" else 0 for label in labels]
        
        fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, pull=pull)])
        fig_donut.update_layout(
            title=f'Donut Chart of {var}', 
            annotations=[dict(text=var, x=0.5, y=0.5, font_size=20, showarrow=False)],
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.3,
                xanchor="center",
                x=0.5,
                title_font_size=12,
                font_size=10,
                font_family="Arial",
                itemwidth=60,
                tracegroupgap=5
            )
        )
        plots.append(dcc.Graph(id=f'{var}-donut', figure=fig_donut))

    # Arrange plots in rows of three
    plot_rows = []
    for i in range(0, len(plots), 2):
        row = html.Div(plots[i:i+2], style={'display': 'flex', 'justify-content': 'space-around', 'margin-bottom': '20px'})
        plot_rows.append(row)

    return plot_rows


def generate_dm_plots_html(data_path):
    df = load_data(data_path, 'dm')
    df = df.fillna("Missing")  # Replace missing values
    plots = []
    variables_to_check = ['RACE', 'ETHNIC', 'DTHFL', 'ARM', 'ACTARM', 'ARMNRS', 'SEX']
    
    # Replace empty strings with 'Missing' for specified variables
    for var in variables_to_check:
        if var in df.columns:
            df[var] = df[var].replace('', 'Missing').fillna('Missing')

    # Unique subject count
    unique_subject_count = df['USUBJID'].nunique()

    # Bar plots
    bar_variables = ['RACE', 'ETHNIC']
    for var in bar_variables:
        if var in df.columns:
            df[var] = df[var].str.upper()
            group_counts = df.groupby(var)['SUBJID'].nunique().reset_index()
            group_percentages = group_counts['SUBJID'] / df['SUBJID'].nunique() * 100
            group_counts['percentage'] = group_percentages
            labels = [f"{count} ({percentage:.2f}%)" for name, count, percentage in zip(group_counts[var], group_counts['SUBJID'], group_counts['percentage'])]

            fig_bar = px.bar(group_counts, x=var, y='SUBJID', color=var, text=labels, color_discrete_sequence=px.colors.qualitative.Set1)
            fig_bar.update_layout(
                title=f'Bar Chart of {var}', 
                xaxis_title=var, 
                yaxis_title='Subject Count',
                legend_title_text=var,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.3,
                    xanchor="center",
                    x=0.5,
                    title_font_size=12,
                    font_size=10,
                    font_family="Arial",
                    itemwidth=60,
                    tracegroupgap=5
                )
            )

            # Convert the plot to HTML using Plotly's to_html method
            plot_html = fig_bar.to_html(full_html=False)
            plots.append(plot_html)

    # Donut plots
    donut_variables = ['ARM', 'ACTARM', 'ARMNRS', 'SEX', 'ETHNIC', 'DTHFL']
    for var in donut_variables:
        if var not in df.columns:
            continue

        # Handle DTHFL to only create plot if there are 'Y' values
        if var == 'DTHFL' and 'Y' not in df['DTHFL'].values:
            continue  

        # Get value counts and ignore case for "Screen Failure"
        value_counts = df[var].str.upper().value_counts()
        labels = value_counts.index
        values = value_counts.values
        
        # Emphasize "Screen Failure" in the legend
        pull = [0.2 if label.upper() == "SCREEN FAILURE" else 0 for label in labels]
        
        fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, pull=pull)])
        fig_donut.update_layout(
            title=f'Donut Chart of {var}', 
            annotations=[dict(text=var, x=0.5, y=0.5, font_size=20, showarrow=False)],
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.3,
                xanchor="center",
                x=0.5,
                title_font_size=12,
                font_size=10,
                font_family="Arial",
                itemwidth=60,
                tracegroupgap=5
            )
        )

        # Convert the plot to HTML using Plotly's to_html method
        plot_html = fig_donut.to_html(full_html=False)
        plots.append(plot_html)

    return plots
