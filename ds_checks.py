# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 09:56:31 2024

@author: inarisetty
"""
import pandas as pd 
import os 
from datetime import datetime
import plotly.express as px
from utils import load_data,is_null_or_empty, is_null_or_empty2
from dash import dcc, html
def check_ds_ae_discon(data_path):
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    
    datasets = "DS, AE"
    
    required_ae_columns = ["USUBJID", "AETERM", "AEDECOD", "AESTDTC", "AEACN"]
    required_ds_columns = ["USUBJID", "DSSPID", "DSCAT", "DSSCAT", "DSDECOD", "DSSTDTC"]

    # Check if required variables exist in AE and DS
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency between DS and AE for treatment discontinuation"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for consistency between DS and AE for treatment discontinuation"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    suppae_file_path = os.path.join(data_path, "suppae.sas7bdat")
    if  os.path.exists(suppae_file_path):
        SUPPAE = load_data(data_path, 'suppae')
        transposed_df = SUPPAE.pivot(index=['USUBJID', 'IDVAR', 'IDVARVAL'], columns='QNAM', values='QVAL').reset_index()
        transposed_df['IDVARVAL'] = transposed_df['IDVARVAL'].astype(int)
        AE = pd.merge(AE, transposed_df, left_on=['USUBJID', 'AESEQ'], right_on=['USUBJID', 'IDVARVAL'], how='left')

    # Drop the IDVARVAL column as it is no longer needed
        AE.drop(columns=['IDVARVAL'], inplace=True)
    # Keep variables on which we want to check action taken with treatment
    ae0 = AE[["USUBJID", "AETERM", "AEDECOD", "AESTDTC"] + [col for col in AE.columns if col.startswith("AEACN")]]
    
    # Select if AE dataset has AEACNx variables
    aeacnvars = [col for col in ae0.columns if col.startswith("AEACN")]

    # Create a where condition for AE
    whrcond = (ae0["AEACN"] == 'DRUG WITHDRAWN')
    for var in aeacnvars:
        whrcond |= (ae0[var] == 'DRUG WITHDRAWN')

    # Loop through each AEACNx and keep DRUG WITHDRAWN AEs
    ae1 = ae0[whrcond]

    # Keep unique usubjid
    ae2 = ae1.drop_duplicates(subset="USUBJID")

   # Keep records with discontinuation treatment due to AE
    ds0 = DS[(DS["DSCAT"] == 'DISPOSITION EVENT') & 
             (DS["DSDECOD"] == 'ADVERSE EVENT')][["USUBJID", "DSSPID", "DSCAT", "DSSCAT", "DSDECOD", "DSSTDTC"]]

    finout = pd.merge(ae2, ds0, on="USUBJID", how="right")

    # Check if DS record with AE has corresponding record in AE
    mask = is_null_or_empty2(finout["AETERM"])
    mydf = finout[mask][["USUBJID", "DSCAT", "DSSCAT", "DSDECOD", "DSSTDTC", "AETERM"] + aeacnvars]

    check_description = "Check for consistency between DS and AE for treatment discontinuation"

    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    message = "Fail"
    notes = f"{len(mydf)} patient(s) with Treatment Discon due to AE but no AE record indicating drug withdrawn."
    mydf.insert(0, "CHECK", check_description)
    mydf.insert(1, "Message", message)
    mydf.insert(2, "Notes", notes)
    mydf.insert(3, "Datasets", datasets)
    
    return mydf

def check_ds_dsdecod_death(data_path, preproc=lambda x: x):
    DS = load_data(data_path, 'ds')
    datasets = "DS"
    required_columns = ["USUBJID", "DSDECOD", "DSSCAT"]

    # Check if required variables exist in DS
    if not set(required_columns).issubset(DS.columns):
        missing = set(required_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for DSDECOD 'DEATH' without DSSCAT indicating STUDY DISCONTINUATION"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company-specific preprocessing function
    DS = preproc(DS)

    # Select relevant columns
    DS = DS[["USUBJID", "DSDECOD", "DSCAT", "DSSCAT", "DSSTDTC"]]

    # Subset DS death records and include only records without a STUDY COMPLETION/DISCONTINUATION form
    ref = DS[DS["DSDECOD"].str.contains("DEATH", case=False, na=False)]

    # Find patients that have a STUDY DISCONTINUATION record
    discon = DS[
        DS["DSSCAT"].str.contains("STUDY", case=False, na=False) &
        DS["DSSCAT"].str.contains("PARTICI", case=False, na=False) &
        ~DS["DSSCAT"].str.contains("DRUG", case=False, na=False) &
        ~DS["DSSCAT"].str.contains("TREATMENT", case=False, na=False)
    ].copy()
    discon["DISCFL"] = "Y"
    discon = discon[["USUBJID", "DISCFL"]].drop_duplicates()

    # Merge datasets to output only patients without DISCON records in DS but known to have died
    mydf0 = pd.merge(ref, discon, on="USUBJID", how="left")

    mydf = mydf0[is_null_or_empty2(mydf0["DISCFL"])].copy()
    mydf = mydf.drop(columns=["DISCFL"], errors='ignore')

    # Replace <NA> with blank in DSSCAT
    mydf.fillna("", inplace=True)

    check_description = "Check for DSDECOD 'DEATH' without DSSCAT indicating STUDY PARTICIPATION"

    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    message = "Fail"
    notes = f"{len(mydf)} record(s) for {mydf['USUBJID'].nunique()} unique patient(s) with DSDECOD='DEATH' but no record with DSSCAT indicating STUDY DISCONTINUATION."
    mydf.insert(0, "CHECK", check_description)
    mydf.insert(1, "Message", message)
    mydf.insert(2, "Notes", notes)
    mydf.insert(3, "Datasets", datasets)
    return mydf

def check_ds_dsdecod_dsstdtc(data_path):
    DS = load_data(data_path, 'ds')
    datasets = "DS"
    required_columns = ["USUBJID", "DSDECOD", "DSSCAT", "DSSTDTC"]

    # Check if required variables exist in DS
    if not set(required_columns).issubset(DS.columns):
        missing = set(required_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for DSDECOD 'DEATH' with DSSTDTC"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    no_dsstdtc = DS['DSSTDTC'].apply(is_null_or_empty)
    # Get all patients with a death date
    has_death_date = DS[(DS["DSDECOD"] == "DEATH") & ~no_dsstdtc][["USUBJID", "DSDECOD", "DSSTDTC"]].drop_duplicates()

    # Get all patients with a death record that aren't in the list of patients with a death date
    df = DS[(DS["DSDECOD"] == "DEATH") & ~(DS["USUBJID"].isin(has_death_date["USUBJID"]))][["USUBJID", "DSDECOD", "DSSTDTC"]].drop_duplicates()

    check_description = "Check for DSDECOD 'DEATH' with DSSTDTC"

    if df.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        message = "Fail"
        notes = f"{len(df)} record(s) for {df['USUBJID'].nunique()} unique patient(s) with DSDECOD='DEATH' but no death date records."
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message)
        df.insert(2, "Notes", notes)
        df.insert(3, "Datasets", datasets)
        return df
def check_ds_dsscat(data_path):
    DS = load_data(data_path, 'ds')
    datasets = "DS"
    required_columns = ["USUBJID", "DSSCAT"]

    # Check if required variables exist in DS
    if not set(required_columns).issubset(DS.columns):
        missing = set(required_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for study discontinuation records/Study Participation in DSSCAT"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
        })

    # Select relevant columns and filter records
    myds = DS[
        DS["DSSCAT"].str.contains("STUDY", case=False, na=False) &
        DS["DSSCAT"].str.contains("PARTICI", case=False, na=False) &
        ~DS["DSSCAT"].str.contains("DRUG", case=False, na=False) &
        ~DS["DSSCAT"].str.contains("TREATMENT", case=False, na=False)
    ][["USUBJID", "DSSCAT"]]

    check_description = "Check for study discontinuation/Study Participation records in DSSCAT"

    # If no records match the criteria
    if myds.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["There are no study discontinuation/Study Participation records"],
            "Datasets": [datasets],
        })

    # Count unique IDs and check for duplicates
    n_uniqueID = myds["USUBJID"].nunique()
    n_occur = myds["USUBJID"].value_counts().reset_index()
    n_occur.columns = ["USUBJID", "Freq"]

    # Get USUBJID with more than one occurrence
    IDlist = n_occur[n_occur["Freq"] > 1]
    myrecs = pd.merge(myds, IDlist[["USUBJID"]], on="USUBJID", how="right")

    if n_uniqueID == len(myds):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
        })
    else:
        notes = "Patients with more than one study discontinuation/Study Participation records."
        # Ensure the first columns are the required ones
        myrecs.insert(0, "CHECK", check_description)
        myrecs.insert(1, "Message", "Fail")
        myrecs.insert(2, "Notes", notes)
        myrecs.insert(3, "Datasets", datasets)
        return myrecs

def check_ds_dsterm_death_due_to(data_path):
    DS = load_data(data_path, 'ds')
    datasets = "DS"
    
    required_columns = ["USUBJID", "DSTERM", "DSDECOD", "DSSTDTC"]

    # Check if required variables exist in DS
    if not set(required_columns).issubset(DS.columns):
        missing = set(required_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for DSTERM 'DEATH DUE TO' in DS"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # DS records with cause of death
    mydf = DS[
        (DS["DSTERM"].str.strip() == "DEATH DUE TO")
    ][["USUBJID", "DSTERM", "DSDECOD", "DSSTDTC"]]

    check_description = "Check for DSTERM 'DEATH DUE TO' in DS"

    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    message = "Fail"
    notes = f"DS has {len(mydf)} records with missing death reason."
    mydf.insert(0, "CHECK", check_description)
    mydf.insert(1, "Message", message)
    mydf.insert(2, "Notes", notes)
    mydf.insert(3, "Datasets", datasets)
    return mydf
def check_ds_duplicate_randomization(data_path):
    DS = load_data(data_path, 'ds')
    datasets = "DS"
    required_columns = ["USUBJID", "DSDECOD"]

    # Check if required variables exist in DS
    if not set(required_columns).issubset(DS.columns):
        missing = set(required_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for duplicate randomization records in DS"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Filter records with "RANDOMIZ" in DSDECOD
    myds = DS[DS["DSDECOD"].str.contains("RANDOMIZ", case=False, na=False)]

    check_description = "Check for duplicate randomization records in DS"

    if myds.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    n_uniqueID = myds["USUBJID"].nunique()

    # Get a dataframe with the frequency of USUBJID
    n_occur = myds["USUBJID"].value_counts().reset_index()
    n_occur.columns = ["USUBJID", "Freq"]

    # Get USUBJID with more than one occurrence
    IDlist = n_occur[n_occur["Freq"] > 1]
    IDlist.columns = ["Duplicate USUBJID", "Number of Records"]

    if n_uniqueID == len(myds):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        notes = f"DS has {len(IDlist)} patient(s) with duplicate randomization records."
        IDlist.insert(0, "CHECK", check_description)
        IDlist.insert(1, "Message", "Fail")
        IDlist.insert(2, "Notes", notes)
        IDlist.insert(3, "Datasets", datasets)
    
        return IDlist
def check_ds_ex_after_discon(data_path):
    DS = load_data(data_path, 'ds')
    EX = load_data(data_path, 'ex')
    datasets = "DS, EX"
    required_ds_columns = ["USUBJID", "DSSTDTC", "DSCAT", "DSSCAT"]
    required_ex_columns = ["USUBJID", "EXTRT", "EXSTDTC", "EXENDTC", "EXDOSE"]

    # Check if required variables exist in DS and EX
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for exposure after study discontinuation in DS and EX"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ex_columns).issubset(EX.columns):
        missing = set(required_ex_columns) - set(EX.columns)
        return pd.DataFrame({
            "CHECK": ["Check for exposure after study discontinuation in DS and EX"],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Define a helper function to parse dates with various formats
    def parse_dates(date_str):
        try:
            return pd.to_datetime(date_str, errors='coerce')
        except:
            return pd.NaT

    # Get treatment discontinuation date
    DS["DSSTDTC_imp"] = DS["DSSTDTC"].apply(parse_dates)
    DS = DS[
        (~DS["DSSTDTC_imp"].isna()) &
        (DS["DSSCAT"].str.contains("STUDY PARTICI", case=False, na=False) |
         DS["DSSCAT"].str.upper().isin(['STUDY COMPLETION/EARLY DISCONTINUATION', 'STUDY EARLY DISCONTINUATION/COMPLETION'])) &
        DS["DSCAT"].str.contains("DISPO", case=False, na=False)
    ][["USUBJID", "DSSTDTC", "DSSCAT", "DSSTDTC_imp", "DSCAT"]]

    # Check that they have valid dosage
    if "EXOCCUR" in EX.columns:
        EX = EX[(EX["EXOCCUR"] == "Y") & ((EX["EXDOSE"] > 0) | (EX["EXDOSE"] == 0 & EX["EXTRT"].str.contains('PLACEBO', case=False, na=False)))]
    else:
        EX = EX[(EX["EXDOSE"] > 0) | (EX["EXDOSE"] == 0 & EX["EXTRT"].str.contains('PLACEBO', case=False, na=False))]

    # Get max exposure start date
    EX["EXSTDTC_imp"] = EX["EXSTDTC"].apply(parse_dates)
    EX_start = EX[
        ~EX["EXSTDTC_imp"].isna()
    ].sort_values(by=["USUBJID", "EXSTDTC"]).groupby("USUBJID").last().reset_index()

    # Get max exposure end date
    EX["EXENDTC_imp"] = EX["EXENDTC"].apply(parse_dates)
    EX_end = EX[
        ~EX["EXENDTC_imp"].isna()
    ].sort_values(by=["USUBJID", "EXENDTC"]).groupby("USUBJID").last().reset_index()

    # Get overall max exposure date comparing start and end
    EX_all = pd.concat([
        EX_start[["USUBJID", "EXSTDTC_imp"]].rename(columns={"EXSTDTC_imp": "DATE"}),
        EX_end[["USUBJID", "EXENDTC_imp"]].rename(columns={"EXENDTC_imp": "DATE"})
    ]).sort_values(by=["USUBJID", "DATE"]).groupby("USUBJID").last().reset_index().rename(columns={"DATE": "max_STDEND"})

    # Merge together and do the check for exposure after study discontinuation
    mydf = DS.merge(EX_all, on="USUBJID", how="left")\
             .merge(EX_start[["USUBJID", "EXSTDTC"]], on="USUBJID", how="left")\
             .merge(EX_end[["USUBJID", "EXENDTC"]], on="USUBJID", how="left")
    mydf = mydf[mydf["DSSTDTC_imp"] < mydf["max_STDEND"]][["USUBJID", "EXSTDTC", "EXENDTC", "DSSCAT", "DSSTDTC"]]

    check_description = "Check for exposure after study discontinuation in DS and EX"

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
        notes = f"{len(mydf)} patient(s) with suspicious Start/End date of treatment occurring after study discontinuation."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
def check_ds_multdeath_dsstdtc(data_path, preproc=lambda x: x):
    DS = load_data(data_path, 'ds')
    datasets = "DS"
    required_columns = ["USUBJID", "DSDECOD", "DSSTDTC"]

    if not set(required_columns).issubset(DS.columns):
        missing = set(required_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for multiple non-matching death dates in DS"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    DS = preproc(DS)

    # Get all records with a death date
    death_dates = DS[
        (DS["DSDECOD"] == "DEATH") & (~DS["DSSTDTC"].isna())
    ][["USUBJID", "DSDECOD", "DSSTDTC"]]

    # Get all patients where death dates don't match
    df = death_dates.groupby("USUBJID").filter(lambda x: len(x) >= 2 and len(x["DSSTDTC"].unique()) > 1)

    check_description = "Check for multiple non-matching death dates in DS"

    if df.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    message = "Fail"
    notes = "DS has multiple non-missing death dates in DSSTDTC that do not match."
    df.insert(0, "CHECK", check_description)
    df.insert(1, "Message", message)
    df.insert(2, "Notes", notes)
    df.insert(3, "Datasets", datasets)
    return df
def check_ds_sc_strat(data_path, preproc=lambda x: x):
    datasets = "DS, SC"
    DS = load_data(data_path, 'ds')
    sc_file_path = os.path.join(data_path, "sc.sas7bdat")
    if  os.path.exists(sc_file_path):
        SC = load_data(data_path, 'sc')
        required_sc_columns = ["USUBJID", "SCTEST", "SCTESTCD", "SCCAT", "SCORRES"]
    else:
        return pd.DataFrame({
            "CHECK": ["Check DS and SC for Stratification"],
            "Message": [f"Check stopped running due to SC dataset not found at the specified location: {sc_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    
    required_ds_columns = ["USUBJID", "DSDECOD", "DSSTDTC"]
    

    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check DS and SC for Stratification"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_sc_columns).issubset(SC.columns):
        missing = set(required_sc_columns) - set(SC.columns)
        return pd.DataFrame({
            "CHECK": ["Check DS and SC for Stratification"],
            "Message": [f"Missing columns in SC: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    DS = preproc(DS)
    SC = preproc(SC)

    # Filter DS for randomized records and get the earliest randomization date per USUBJID
    DS_filtered = DS[DS["DSDECOD"].str.upper().isin(["RANDOMIZED", "RANDOMIZATION"])].copy()
    DS_filtered["DS_RANDDT"] = pd.to_datetime(DS_filtered["DSSTDTC"], errors='coerce')
    DS_filtered = DS_filtered.sort_values(by="DS_RANDDT").drop_duplicates(subset="USUBJID", keep="first")
    DS_filtered = DS_filtered[["USUBJID", "DS_RANDDT"]]

    # Filter SC for stratification factors
    SC_filtered = SC[SC["SCCAT"].str.upper() == "STRATIFICATION"][["USUBJID", "SCTESTCD", "SCTEST", "SCCAT", "SCORRES"]]

    if DS_filtered.empty:
        return pd.DataFrame({
            "CHECK": ["Check DS and SC for Stratification"],
            "Message": ["Only applicable for randomized studies. Based on DS, no records were found indicating randomized patients."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if SC_filtered.empty:
        return pd.DataFrame({
            "CHECK": ["Check DS and SC for Stratification"],
            "Message": ["Study is randomized but no records in SC indicating stratification factors."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Merge DS and SC and flag missing stratification factors
    mydf1 = pd.merge(DS_filtered, SC_filtered, on="USUBJID", how="left")
    mydf1["MISFLAG"] = mydf1["SCORRES"].isna().astype(int)
    mydf1 = mydf1[mydf1["MISFLAG"] == 1].drop(columns=["SCCAT", "MISFLAG"])
    mydf1 = mydf1.fillna(" ")

    check_description = "Check DS and SC for Stratification"

    if mydf1.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    message = "Fail"
    notes = f"{len(mydf1['USUBJID'].unique())} patient(s) for randomized study where stratification factors are missing."
    mydf1.insert(0, "CHECK", check_description)
    mydf1.insert(1, "Message", message)
    mydf1.insert(2, "Notes", notes)
    mydf1.insert(3, "Datasets", datasets)
    return mydf1

def  comp_status_dis(data_path):
    df = load_data(data_path, 'ds')
    plots = []
    unique_events_df = df.drop_duplicates(subset=["USUBJID", "DSDECOD"])

    # Aggregate data by DSDECOD
    aggregated_df = unique_events_df.groupby("DSDECOD").size().reset_index(name="Count")

    # Plot the aggregated data
    fig = px.bar(
        aggregated_df,
        x="DSDECOD",
        y="Count",
        title="Completion Status Distribution (Unique per Subject)",
        labels={"DSDECOD": "Disposition Event", "Count": "Count"},
        text_auto=True
    )
    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins as needed
        legend=dict(x=1, y=1, traceorder='normal', font=dict(size=10)),
        height=500,
        width=1200  # Set width to a numeric value
    )
    #fig.show()
    #return [dcc.Graph(figure=fig)]
    plot_html = fig.to_html(full_html=False)
    plots.append(plot_html)

    return plots
def study_status_arm(data_path):
    # Load the datasets
    ds = load_data(data_path, 'ds')
    dm = load_data(data_path, 'dm')

    # Merge DM and DS datasets on USUBJID
    df = pd.merge(dm, ds, on="USUBJID", how="left")
    plots = []
    # Remove duplicates to count each disposition event (DSDECOD) per subject (USUBJID) per ARM only once
    unique_events_df = df.drop_duplicates(subset=["USUBJID", "DSDECOD", "ARM"])

    # Aggregate data by DSDECOD and ARM
    aggregated_df = unique_events_df.groupby(["DSDECOD", "ARM"]).size().reset_index(name="Count")

    # Plot the aggregated data
    fig = px.bar(
        aggregated_df,
        x="ARM",
        y="Count",
        color="DSDECOD",
        title="Subject Status by Study Arm",
        labels={"ARM": "Study Arm", "DSDECOD": "Disposition Event", "Count": "Count"},
        text_auto=True
    )
    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins as needed
        legend=dict(x=1, y=1, traceorder='normal', font=dict(size=10)),
        height=500,
        width=1200  # Set width to a numeric value
    )
    #return [dcc.Graph(figure=fig)]
    plot_html = fig.to_html(full_html=False)
    plots.append(plot_html)

    return plots
def dispo_time(data_path):
    df = load_data(data_path, 'ds')
    plots = []
    # Histogram
    fig = px.histogram(
        df,
        x="DSSTDTC",
        title="Disposition Timing Distribution",
        labels={"DSSTDTC": "Disposition Date"},
    )
    #fig.show()
    plot_html = fig.to_html(full_html=False)
    plots.append(plot_html)
    # Scatter Plot for individual subjects
    fig = px.scatter(
        df,
        x="DSSTDTC",
        y="USUBJID",
        title="Disposition Timing by Subject",
        labels={"DSSTDTC": "Disposition Date", "USUBJID": "Subject ID"}
    )
    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins as needed
        legend=dict(x=1, y=1, traceorder='normal', font=dict(size=10)),
        height=500,
        width=1200  # Set width to a numeric value
    )
    #fig.show()
    #return [dcc.Graph(figure=fig)]
    plot_html = fig.to_html(full_html=False)
    plots.append(plot_html)

    return plots
def sub_stat_epoch(data_path):
    # Load the dataset
    df = load_data(data_path, 'ds')
    plots = []
    # Define required columns
    required_ds_columns = ["USUBJID", "DSDECOD", "EPOCH"]
    
    # Title section
    title_section = html.H3("Subject Status by Epoch")
    
    # Check if all required columns are present
    missing_columns = [col for col in required_ds_columns if col not in df.columns]
    if missing_columns:
        # Return title and missing column message
        return [
            html.Div([
                title_section,
                html.P(f"Missing columns in the data: {', '.join(missing_columns)}", style={"color": "red"})
            ])
        ]
    
    # Remove duplicates to count each disposition event (DSDECOD) per subject (USUBJID) and epoch only once
    unique_events_df = df.drop_duplicates(subset=["USUBJID", "DSDECOD", "EPOCH"])
    
    # Aggregate data by EPOCH and DSDECOD
    aggregated_df = unique_events_df.groupby(["EPOCH", "DSDECOD"]).size().reset_index(name="Count")
    
    # Plot the aggregated data
    fig = px.bar(
        aggregated_df,
        x="EPOCH",
        y="Count",
        color="DSDECOD",
        title=None,  # Title handled separately in the layout
        labels={"EPOCH": "Epoch", "DSDECOD": "Disposition Event", "Count": "Count"},
        text_auto=True,
    )
        # Update layout of the plot
    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins as needed
        legend=dict(x=1, y=1, traceorder='normal', font=dict(size=10)),
        height=500,
        width=2000  # Set width to a numeric value
    )
    
    # Return title and the graph
    # return [
    #     html.Div([
    #         title_section,
    #         dcc.Graph(figure=fig)
    #     ])
    # ]
    plot_html = fig.to_html(full_html=False)
    plots.append(plot_html)

    return plots
def dispo_event(data_path):
    df = load_data(data_path, 'ds')
    plots = []
    # Filter records with non-null DSTERM values
    deviation_df = df[df["DSTERM"].notna()]

    # Ensure each subject is counted only once per deviation
    unique_deviations_df = deviation_df.drop_duplicates(subset=["USUBJID", "DSTERM"])

    # Aggregate the data by DSTERM
    aggregated_deviations = unique_deviations_df.groupby("DSTERM").size().reset_index(name="Count")

    # Generate the pie chart
    fig = px.pie(
        aggregated_deviations,
        names="DSTERM",
        values="Count",
        title="Disposition Event by Subject",
        labels={ "Count": "Count"}
    )
    fig.update_traces(textinfo="value", textfont_size=14)
    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins as needed
        legend=dict(x=1, y=1, traceorder='normal', font=dict(size=10)),
        height=500,
        width=1200  # Set width to a numeric value
    )
    # Return the figure (or plot it directly in Dash)
    plot_html = fig.to_html(full_html=False)
    plots.append(plot_html)

    return plots
    #return [dcc.Graph(figure=fig)]
def dispo_reas(data_path):
    df = load_data(data_path, 'ds')
    plots = []
    reason_trend = df.groupby(["DSSTDTC", "DSTERM"]).size().reset_index(name="Count")

    fig = px.line(
        reason_trend,
        x="DSSTDTC", 
        y="Count",
        color="DSTERM",
        title="Disposition Reasons Trends Over Time",
        labels={"DSSTDTC": "Disposition Date", "DSTERM": "Reason", "Count": "Count"}
    )
    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins as needed
        legend=dict(x=1, y=1, traceorder='normal', font=dict(size=10)),
        height=500,
        width=2000  # Set width to a numeric value
    )
    plot_html = fig.to_html(full_html=False)
    plots.append(plot_html)

    return plots
    #fig.show()
    #return [dcc.Graph(figure=fig)]

