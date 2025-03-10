
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd 
import os 
from datetime import datetime

#from utils import load_data,is_null_or_empty
from utils import load_data,is_null_or_empty, is_null_or_empty2,fail_check, pass_check, lacks_any, lacks_all, impute_day01, miss_col, check_empty_dataset

def check_ae_aeacn_ds_disctx_covid(data_path, covid_terms=None):
    ae = load_data(data_path, 'ae')
    ds = load_data(data_path, 'ds')
    datasets = "AE,DS"
    check_description = "Check for patients with COVID-19 AE indicating drug withdrawn but no Treatment Discon form indicating AE."
    if covid_terms is None:
        covid_terms = ["COVID-19", "CORONAVIRUS POSITIVE"]
    
    # Check covid_terms
    if not covid_terms or not all(isinstance(term, str) for term in covid_terms):
        raise ValueError("covid_terms should be a non-empty list of strings.")
    
    required_ae_columns = {"USUBJID", "AETERM", "AEDECOD", "AESTDTC", "AEACN"}
    required_ds_columns = {"USUBJID", "DSCAT", "DSDECOD"}
    empty_check = check_empty_dataset(ae,"AE", datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check required columns in AE and DS
    if not required_ae_columns.issubset(ae.columns):
        missing = required_ae_columns - set(ae.columns)
        return pd.DataFrame({
            "CHECK": ["Check for patients with COVID-19 AE indicating drug withdrawn but no Treatment Discon form indicating AE."],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    if not required_ds_columns.issubset(ds.columns):
        missing = required_ds_columns - set(ds.columns)
        return pd.DataFrame({
            "CHECK": ["Check for patients with COVID-19 AE indicating drug withdrawn but no Treatment Discon form indicating AE."],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    outmsg = ""
    if covid_terms == ["COVID-19", "CORONAVIRUS POSITIVE"]:
        outmsg = f"Default terms used for identifying Covid AEs: {', '.join(covid_terms)}"
    
    # Remove duplicate columns
    ae = ae.loc[:, ~ae.columns.duplicated()]
    
    # Filter AE for covid terms and specific AEACN conditions
    ae_covid = ae[ae["AEDECOD"].str.upper().isin([term.upper() for term in covid_terms])]
    if ae_covid.empty:
        return pd.DataFrame({
            "CHECK": ["Check for patients with COVID-19 AE indicating drug withdrawn but no Treatment Discon form indicating AE."],
            "Message": ["Check not run, did not detect COVID-19 preferred terms in AEDECOD."],
            "Notes" :[""],
            "Datasets":[datasets]
        })

    ae_cols = ["USUBJID", "AEDECOD", "AESTDTC"] + [col for col in ae.columns if col.startswith("AEACN")]
    ae0 = ae_covid[ae_cols]
    
    aeacnvars = [col for col in ae0.columns if col.startswith("AEACN")]
    
    # Boolean indexing instead of query() for filtering ae0
    condition = ae0["AEACN"] == "DRUG WITHDRAWN"
    ae1 = ae0[condition]
    
    # Filter DS for specific conditions
    ds0 = ds[(ds["DSCAT"] == "DISPOSITION EVENT") & (ds["DSDECOD"] == "ADVERSE EVENT")]
    ds0 = ds0[["USUBJID", "DSDECOD"]]
    
    # Merge AE and DS data
    finout = pd.merge(ae1, ds0, on="USUBJID", how="left")
    
    # Filter for specific conditions in final DataFrame
    mydf = finout[finout["DSDECOD"].isna()].drop(columns=["DSDECOD"])
    
    if "AEACN" in ae.columns and any(ae["AEACN"] == "MULTIPLE"):
        mydf = mydf.drop(columns=["AEACN"])
    
    # Construct final DataFrame with message
 
    if mydf.empty:
        result_df = pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    else:
        message = "Fail"
        unique_patients = len(mydf["USUBJID"].unique())
        notes = f"{unique_patients} patient(s) with COVID-19 AE indicating drug withdrawn but no Treatment Discon form indicating AE. {outmsg}"
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        result_df = mydf

    return result_df
def check_ae_aeacnoth(data_path, preproc=lambda df: df, **kwargs):
    AE = load_data(data_path, 'ae')
    datasets = "AE"
    check_description = "AE entries where AEACNOTH = 'MULTIPLE' and AEACNOT1 or AEACNOT2 is NA"
    required_columns = ["USUBJID", "AETERM", "AESTDTC", "AEACNOTH", "AEACNOT1", "AEACNOT2"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["AE entries where AEACNOTH = 'MULTIPLE' and AEACNOT1 or AEACNOT2 is NA"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })    
    # First check if there are any records with AEACNOTH == "MULTIPLE"
    if not any(AE["AEACNOTH"] == "MULTIPLE"):
        return pd.DataFrame({
            "CHECK": ["AE entries where AEACNOTH = 'MULTIPLE' and AEACNOT1 or AEACNOT2 is NA"],
            "Message": ["Check not run, No records with AEACNOTH = 'MULTIPLE'"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    
    
    
    # Check if required variables exist

    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    
    # Subset AE to only records with null AEACNOT[1/2] when AEACNOTH = 'MULTIPLE'
    mydf = AE.loc[
        (AE["AEACNOTH"] == "MULTIPLE") & (AE["AEACNOT1"].isna() | AE["AEACNOT2"].isna()),
        ["USUBJID", "AETERM", "AESTDTC", "AEACNOTH", "AEACNOT1", "AEACNOT2"]
    ]
    
    # Return message if no records with null AEACNOT[1/2] when AEACNOTH = 'MULTIPLE'
 
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    else:
        message = 'Fail'
        unique_patients = len(mydf["USUBJID"].unique())
        notes = f"{unique_patients} record(s) with null AEACNOT[1/2] when AEACNOTH = 'MULTIPLE'."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
def check_ae_aeacnoth_ds_disctx(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE, DS"
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    check_description = "Check for AEs leading to Study Discontinuation but no corresponding record in DS"
    required_ae_columns = ["USUBJID", "AEDECOD", "AEACNOTH"]
    required_ds_columns = ["USUBJID", "DSCAT", "DSSCAT", "DSDECOD"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AEs leading to Study Discontinuation but no corresponding record in DS"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AEs leading to Study Discontinuation but no corresponding record in DS"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    
    # Get all AEACNOTx (x = "H", "1", "2", etc) columns
    aeacnotx_cols = ["AEACNOTH"] + [col for col in AE.columns if col.startswith("AEACNOT") and col != "AEACNOTH"]
    
    # Keep only AE columns that are needed
    ae1 = AE[["USUBJID", "AEDECOD", "AESTDTC"] + aeacnotx_cols ]
    
    # Filter for AE records where any of AEACNOTHx (x = "", "1", "2", etc) contains "STUDY DISCONTINUED"
    ae1["subj_discont_fl"] = ae1[aeacnotx_cols].apply(lambda x: x.str.contains("STUDY DISCONT", case=False, na=False).any(), axis=1)
    
    # Check if any records qualify
    if not ae1["subj_discont_fl"].any():
        return pd.DataFrame({
            "CHECK": ["Check for AEs leading to Study Discontinuation but no corresponding record in DS"],
            "Message": ["Check not run, No records qualified for study discontinuation"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    
    ae2 = ae1[ae1["subj_discont_fl"]].drop(columns=["subj_discont_fl"])
    
    # Keep only DS columns that are needed
    ds1 = DS[["USUBJID", "DSCAT", "DSSCAT", "DSDECOD"]]
    
    # Filter for DS records indicating subject didn't complete the study
    ds2 = ds1[ds1["DSSCAT"].str.contains("STUDY", case=False, na=False) &
              ds1["DSSCAT"].str.contains("PARTICI", case=False, na=False) &
              (ds1["DSDECOD"] != "COMPLETED")]
    
    # Merge AE and DS to cross-check records
    ae_ds = ae2.merge(ds2, on="USUBJID", how="left")
    
    # Keep only AE records where there is no corresponding DS record
    mydf = ae_ds[ae_ds["DSDECOD"].isna()]
    
    # Return pass message if no there is no inconsistency between AE and DS

    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    else:
        message = "Fail"
        unique_patients = len(mydf["USUBJID"].unique())
        notes = f"{unique_patients} patient(s) with AEs leading to Study Discontinuation but no corresponding record in DS."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets",datasets)
        
        return mydf

def check_ae_aeacnoth_ds_stddisc_covid(data_path, covid_terms=["COVID-19", "CORONAVIRUS POSITIVE"]):
    datasets="AE, DS"
    check_description = "Check for COVID-related AEs leading to Study Discontinuation but no corresponding record in DS"
    AE = load_data(data_path, 'ae')
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    DS = load_data(data_path, 'ds')
    if (covid_terms is None or
        (covid_terms is not None and not isinstance(covid_terms, list)) or
        (covid_terms is not None and isinstance(covid_terms, list) and len(covid_terms) < 1) or
        (covid_terms is not None and isinstance(covid_terms, list) and len(covid_terms) >= 1 and all(pd.isna(covid_terms)))):
        
        return pd.DataFrame({
            "CHECK": ["Check for COVID-related AEs leading to Study Discontinuation but no corresponding record in DS"],
            "Message": ["Check not run, did not detect COVID-19 preferred terms. Character vector of terms expected."],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    
    if not set(["USUBJID", "AEDECOD", "AEACNOTH"]).issubset(AE.columns):
        missing = set(["USUBJID", "AEDECOD", "AEACNOTH"]) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for COVID-related AEs leading to Study Discontinuation but no corresponding record in DS"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })

    if not set(["USUBJID", "DSSCAT", "DSDECOD"]).issubset(DS.columns):
        missing = set(["USUBJID", "DSSCAT", "DSDECOD"]) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for COVID-related AEs leading to Study Discontinuation but no corresponding record in DS"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })

    # Select AE recs where uppercased AE.AEDECOD matches COVID-related terms
    ae0 = AE[AE["AEDECOD"].str.upper().isin([term.upper() for term in covid_terms])]
    
    # Check if any COVID terms are detected in AEDECOD
    if ae0.empty:
        return pd.DataFrame({
            "CHECK": ["Check for COVID-related AEs leading to Study Discontinuation but no corresponding record in DS"],
            "Message": ["Check not run, did not detect COVID-19 preferred terms in AEDECOD."],
            "Notes" :[""],
            "Datasets":[datasets]
        })

    # Let user know terms used
    if covid_terms == ["COVID-19", "CORONAVIRUS POSITIVE"]:
        outmsg = f"Default terms used for identifying Covid AEs: {', '.join(covid_terms)}"
    else:
        outmsg = ""

    # Select column variables matching AEACNOT* (i.e. AEACNOTH, AEACNOT1, AEACNOT2, etc.)
    aeacnoth_colnm = [col for col in ae0.columns if col.startswith("AEACNOT")]

    # Select AE recs leading to STUDY DISCON use variables AEACNOT*
    ae1 = ae0[
        ae0[aeacnoth_colnm].apply(lambda x: x.str.contains("STUDY", case=False, na=False).any(), axis=1) &
        ae0[aeacnoth_colnm].apply(lambda x: x.str.contains("DISCON", case=False, na=False).any(), axis=1)
    ]

    # Select DS recs with STUDY DISCON
    ds0 = DS[
        DS["DSSCAT"].str.contains("STUDY", case=False, na=False) &
        DS["DSSCAT"].str.contains("DISCON", case=False, na=False) &
        ~DS["DSSCAT"].str.contains("DRUG", case=False, na=False) &
        ~DS["DSSCAT"].str.contains("TREATMENT", case=False, na=False)
    ][["USUBJID", "DSDECOD", "DSSCAT"]]

    # Keep patients in AE who lack DS record
    mydfprep = pd.merge(ae1, ds0, on="USUBJID", how="left")
    mydf = mydfprep[mydfprep["DSSCAT"].isna()][["USUBJID", "AEDECOD", "DSDECOD", "DSSCAT"] + aeacnoth_colnm]

    # Return pass if all COVID-related AE recs leading to STUDY discon had corresponding DISCON rec
    
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    else:
        unique_patients = len(mydf["USUBJID"].unique())
        message = "Fail"
        notes = f"Found {unique_patients} patient(s) with COVID-related AE(s) leading to Study Discon, but no corresponding Study Discon in DS. {outmsg}"
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets",datasets)
        return mydf
def check_ae_aedecod(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    AE = load_data(data_path, 'ae')
    check_description = "Check for missing AEDECOD"
    required_columns = ["USUBJID", "AETERM", "AEDECOD"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for missing AEDECOD"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })

    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    
    # Subset AE to only records with missing AEDECOD
    mydf = AE.loc[AE["AEDECOD"].isna(), ["USUBJID", "AESTDTC", "AETERM", "AEDECOD"]]

    # Return message if no records with missing AEDECOD

    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Datasets":[datasets]
        })
    else:
        message = "Fail"
        notes = f"AE has {len(mydf)} record(s) with missing AEDECOD."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.inster(3,"Datasets", datasets)
        
        return mydf
def check_ae_aedthdtc_aesdth(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    AE = load_data(data_path, 'ae')
    check_description = "Check for AE entries with AESTDTC and AESDTH  equal to 'Y'"
    required_columns = ["USUBJID", "AETERM", "AESDTH", "AEDECOD", "AESTDTC"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AESTDTC but AESDTH not equal to 'Y'"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    has_deaths = AE["AESDTH"] == "Y"
    if not has_deaths.any():
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AE Death Date but AESDTH not equal to 'Y'"],
            "Message": ["Check not run, No deaths found"],
            "Notes" :[""],
            "Datasets":[datasets]
        })

    # Rows where AEDTHDTC is not NA
    aestdtc_null = AE['AESTDTC'].apply(is_null_or_empty)
    has_aedthdtc = aestdtc_null
    
    # Rows where AESDTH != "Y", with expanded logic for NA values
    no_aesdth = (AE["AESDTH"] == "Y") 
    
    # Subsets AE to select variables and rows where AESDTH != "Y" and AEDTHDTC has a value
    df = AE.loc[has_aedthdtc & no_aesdth, ["USUBJID", "AETERM", "AEDECOD", "AESTDTC", "AESDTH"]]
    
    # Return message depending on whether there are instances where AESDTH != "Y" and AEDTHDTC has a value

    if df.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    else:
        message = "Fail"
        notes = f"{len(df)} AE(s) with AESDTH = 'Y' but AESTDTC and AEENDTC inconsistent."
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message),
        df.insert(2, "Notes", notes)
        df.insert(3,"Datasets", datasets)
        return df
def check_ae_aedthdtc_ds_death(data_path):
    datasets = "AE, DS"
    check_description = "Check for AE entries with AESTDTC and DS entries with DEATH DUE TO ADVERSE EVENT"
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    required_ae_columns = ["USUBJID", "AESTDTC"]
    required_ds_columns = ["USUBJID", "DSDECOD", "DSTERM", "DSSTDTC"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AESTDTC and DS entries with DEATH DUE TO ADVERSE EVENT"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AESTDTC and DS entries with DEATH DUE TO ADVERSE EVENT"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
    
    # Check if study has older mapping where "DEATH DUE TO ADVERSE EVENT" is used
    if 'DEATH DUE TO ADVERSE EVENT' in DS['DSTERM'].values:
        
        # Only consider DS records from patients who have a record with DEATH and ADVERSE EVENT
        ds0a = DS[(DS['DSDECOD'].str.contains("DEATH", case=False, na=False)) & 
                  (DS['DSTERM'].str.contains("ADVERSE EVENT", case=False, na=False))]
        
        # If there are no DS records that qualify for the check
        if ds0a.empty:
            return pd.DataFrame({
                "CHECK": ["Check for AE entries with AESTDTC and DS entries with DEATH DUE TO ADVERSE EVENT"],
                "Message": ["Pass"],
                "Notes" :[""],
                "Datasets":[datasets]
            })
        aestdtc_null = AE['AESTDTC'].apply(is_null_or_empty)
        # Look for all records in AE where the death date is populated
        ae0a = AE[~aestdtc_null]
        
        # Check for subjects in ds0a that do not have a matching record in ae0a
        ds11 = ds0a[~ds0a['USUBJID'].isin(ae0a['USUBJID'])][['USUBJID', 'DSTERM', 'DSSTDTC']]
        
        # If all subjects in ds0a have a matching record in ae0a
        if ds11.empty:
            return pd.DataFrame({
                "CHECK": ["Check for AE entries with AESTDTC and DS entries with DEATH DUE TO ADVERSE EVENT"],
                "Message": ["Pass"],
                "Notes" :[""],
                "Datasets":[datasets]
            })
        
        # Return subset dataframe if there are records with inconsistency
        else:
            message = "Fail"
            notes= f"{len(ds11['USUBJID'].unique())} patient(s) where DS.DSDECOD contains 'DEATH' and DS.DSTERM contains 'ADVERSE EVENT' but with no death date in AE.AESTDTC (DSTERM mapping only applicable to older studies)."
            ds11.insert(0, "CHECK", "Check for AE entries with AESTDTC and DS entries with DEATH DUE TO ADVERSE EVENT")
            ds11.insert(1, "Message", message)
            ds11.insert(2, "Message", notes)
            ds11.insert(3,"Datasets", datasets)
            return ds11

    # If study has newer mapping where DSDECOD = DEATH
    else:
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AESTDTC and DS entries with DEATH DUE TO ADVERSE EVENT"],
            "Message": ["Pass"],
            "Notes" :[""],
            "Datasets":[datasets]
        })

def check_ae_aeout(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    check_description = "Check for AE entries with inconsistent AESTDTC and AEOUT when AEOUT is FATAL"
    AE = load_data(data_path, 'ae')
    required_columns = ["USUBJID", "AESTDTC", "AEOUT"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with inconsistent AESTDTC and AEOUT"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Datasets":[datasets]
        })
    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    aestdtc_null = AE['AESTDTC'].apply(is_null_or_empty)
    # Filter for inconsistencies between AESTDTC and AEOUT
    df = AE.loc[((AE['AEOUT'] == "FATAL") & (aestdtc_null))][["USUBJID", "AESTDTC", "AEOUT"]]
    
    # Return message depending on whether there are inconsistencies
  
    if not df.empty:
        notes = f"{len(df)} AE(s) with inconsistent AESTDTC and AEOUT found."
        message="Fail"
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message)
        df.insert(2, "Notes", notes)
        df.insert(3,"Datasets", datasets)
        return df
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
def check_ae_aeout_aeendtc_aedthdtc(data_path, preproc=lambda df: df, **kwargs):
    datasets= "AE"
    check_description = "Check for AE entries with AEOUT = 'FATAL' but AESTDTC and AEENDTC inconsistent"
    AE = load_data(data_path, 'ae')
    required_columns = ["USUBJID", "AETERM", "AEENDTC", "AESTDTC", "AEOUT"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
        # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AEOUT = 'FATAL' but AESTDTC and AEENDTC inconsistent"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Datasets":[datasets]
        })
    has_deaths = AE["AEOUT"] == "FATAL"
    if not has_deaths.any():
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AEOUT = 'FATAL' but AESTDTC and AEENDTC inconsistent"],
            "Message": ["Check not run, No records with AEOUT = FATAL found"],
            "Datasets":[datasets]
        })

    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    aeendtc_null = AE['AEENDTC'].apply(is_null_or_empty)
    # Filter for inconsistencies between AESTDTC and AEENDTC where AEOUT = 'FATAL'
    df = AE.loc[(AE['AEOUT'] == 'FATAL') & ((AE['AEENDTC'] != AE['AESTDTC']) | (aeendtc_null))][["USUBJID", "AETERM", "AEENDTC", "AESTDTC", "AEOUT"]]
    
    # Add note
    df["NOTE"] = "**QUERY ONLY IF TEAM AGREES**"
    
    # Return message depending on whether there are inconsistencies

    if not df.empty:
        message = "Fail"
        notes = f"{len(df)} AE(s) with AEOUT = 'FATAL' but AESTDTC and AEENDTC inconsistent."
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message)
        df.insert(2, "Notes", notes)
        df.insert(3,"Datasets", datasets)
        return df
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes" :[""],
            "Datasets":[datasets]
        })
def check_ae_aeout_aeendtc_nonfatal(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    check_description = "Check for non-fatal AE entries with inconsistent AEENDTC and AEOUT"
    AE = load_data(data_path, 'ae')
    required_columns = ["USUBJID", "AESTDTC", "AETERM", "AEENDTC", "AEOUT"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for non-fatal AE entries with inconsistent AEENDTC and AEOUT"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Datasets":[datasets]
        })
    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    AE['AEOUT'] = AE['AEOUT'].str.upper()

    aeendtc_null = AE['AEENDTC'].apply(is_null_or_empty)
    # Filter for inconsistencies between AEENDTC and AEOUT for non-fatal AEs
    df = AE.loc[
        (aeendtc_null & AE['AEOUT'].isin(["RECOVERED/RESOLVED", "RECOVERED/RESOLVED WITH SEQUELAE"])) |
        (~aeendtc_null & AE['AEOUT'].isin(["UNKNOWN", "NOT RECOVERED/NOT RESOLVED", "RECOVERING/RESOLVING"]))
    ][["USUBJID", "AETERM", "AESTDTC", "AEENDTC", "AEOUT"]]
    
    # Return message depending on whether there are inconsistencies

    if not df.empty:
        message = "Fail"
        notes = f"{len(df)} non-fatal AE(s) with inconsistent AEENDTC and AEOUT found."
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message)
        df.insert(2, "Notes", notes)
        df.insert(3,"Datasets", datasets)
        return df
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Datasets":[datasets]
        })
def check_ae_aerel(data_path, preproc=lambda df: df, **kwargs):
    datasets= "AE"
    check_description = "Check for AE entries with missing or unexpected AEREL values"
    AE = load_data(data_path, 'ae')

    # Check that required variables exist and return a message if they don't
    required_columns = ["USUBJID", "AESTDTC", "AETERM", "AEREL"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with missing or unexpected AEREL values"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Datasets":[datasets]
        })
    # Keep only AEREL, AEREL1 - AERELN
    all_aerel = [col for col in AE.columns if "AEREL" in col and "AERELNS" not in col]



    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    AE = AE[[col for col in ["USUBJID", "AESTDTC", "AETERM"] + all_aerel if col in AE.columns]]

    mydf_sub = AE

    # Filter rows with missing AEREL
    mydf_miss = mydf_sub[(AE["AEREL"].isna()) & (AE["AEREL"] != "NA")]

    # Filter rows with non-missing AEREL
    mydf_nmiss = mydf_sub[~AE["AEREL"].isna()]

    # Calculating number of columns without AEREL-AEREL[n]
    n_col = mydf_nmiss.shape[1] - len(all_aerel)

    if len(all_aerel) > 1:
        index_y = mydf_nmiss.iloc[:, n_col:].apply(lambda x: x == 'Y')
        index_n = mydf_nmiss.iloc[:, n_col:].apply(lambda x: x == 'N')
        index_na = mydf_nmiss.iloc[:, n_col:].apply(lambda x: x == 'NA')
        index_m = mydf_nmiss.iloc[:, n_col:].apply(lambda x: x == '')

        y = index_y.any(axis=1)
        na = index_na.all(axis=1)
        n1 = index_n.any(axis=1)
        m = index_m.all(axis=1)

        n = n1 & ~y

        # Check if there is any unexpected AEREL
        mydf_y = mydf_nmiss[(AE["AEREL"] == 'Y') & ~y]
        mydf_n = mydf_nmiss[(AE["AEREL"] == 'N') & ~n]
        mydf_na = mydf_nmiss[(AE["AEREL"] == 'NA') & ~na]
        mydf_m = mydf_nmiss[(AE["AEREL"] == '') & ~m]

        if not mydf_miss.empty:
            index_all = mydf_miss.iloc[:, n_col:].apply(lambda x: x.isin(['Y', 'NA', 'N', '']).any(), axis=1)
            mydf_all = mydf_miss[index_all]

            mydf = pd.concat([mydf_y, mydf_n, mydf_m, mydf_all])
        else:
            mydf = pd.concat([mydf_y, mydf_na, mydf_n])
    else:
        mydf = mydf_miss

    mydf.reset_index(drop=True, inplace=True)


    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Datasets":[datasets]
        })
    elif len(mydf) == 1:
        message = 'Fail'
        notes = "There is one observation with missing AEREL but one of AEREL1 - AEREL[n] is equal to Y/N/NA, or AEREL has unexpected value, or AEREL[n] missing."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
        
    else:
        message = 'Fail'
        notes = f"AE has {len(mydf)} observations where AEREL is missing but one of AEREL1 - AEREL[n] is equal to Y/N/NA, or AEREL has an unexpected value, or AEREL[n] missing."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3,"Datasets", datasets)
        return mydf
def check_ae_aesdth_aedthdtc(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    check_description = "Check for AE entries with AESDTH equal to 'Y' but AESTDTC missing"
    AE = load_data(data_path, 'ae')
    required_columns = ["USUBJID", "AESDTH", "AETERM", "AEDECOD", "AESTDTC"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
        # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AESDTH equal to 'Y' but AE Death Date missing"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Datasets":[datasets]
        })
    # Rows where AESDTH is "Y"
    has_aesdth = AE["AESDTH"] == "Y"
    if not has_aesdth.any():
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AESDTH = 'Y' but AESTDTC inconsistent"],
            "Message": ["Check not run, No records with AESDTH = 'Y' found"],
            "Datasets":[datasets]
        })

    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    
    # Rows where AEDTHDTC is NA or empty

    no_aedthdtc = AE['AESTDTC'].apply(is_null_or_empty)
    # Subsets AE to select variables and rows where AESDTH = "Y" and AEDTHDTC does not have a value
    df = AE.loc[has_aesdth & no_aedthdtc, ["USUBJID", "AETERM", "AEDECOD", "AESTDTC", "AESDTH"]]
    
    # Return message depending on whether there are instances where AESDTH = "Y" and AEDTHDTC does not have a value

    if df.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Datasets":[datasets]
        })
    else:
        message = "Fail"
        notes = f"AE has {len(df)} record(s) with AESDTH equal to 'Y' where AESTDTC does not have a value."
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message)
        df.insert(2, "Notes", notes)
        df.insert(3,"Datasets", datasets)
        return df

def check_ae_aestdtc_after_aeendtc(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    check_description = "Check for AE entries with AESTDTC after AEENDTC"
    AE = load_data(data_path, 'ae')
    required_columns = ["USUBJID", "AETERM", "AEDECOD", "AESTDTC", "AEENDTC"]
        # Check if AE DataFrame is empty
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check

    # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE entries with AESTDTC after AEENDTC"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Datasets":[datasets]
        })
    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    
    # Get minimum length for when AESTDTC and AEENDTC are different lengths
    min_length = AE[['AESTDTC', 'AEENDTC']].applymap(len).min(axis=1)
    
    AE['startdate'] = AE.apply(lambda x: x['AESTDTC'][:min_length.loc[x.name]], axis=1)
    AE['enddate'] = AE.apply(lambda x: x['AEENDTC'][:min_length.loc[x.name]], axis=1)
    
    # Convert string to date/time
    def convert_to_datetime(date_str):
        formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H", "%Y-%m-%d", "%Y-%m", "%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    AE['DT1'] = AE['startdate'].apply(convert_to_datetime)
    AE['DT2'] = AE['enddate'].apply(convert_to_datetime)
    
    # Filter records where AESTDTC is after AEENDTC
    mydf = AE.loc[AE['DT1'] > AE['DT2'], ["USUBJID", "AETERM", "AEDECOD", "AESTDTC", "AEENDTC"]]
    

    
    # Return message if no records with issue
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Datasets":[datasets]
        })
    else:
        # Return subset dataframe if there are issues with start date after end date
        message = "Fail"
        notes = f"AE has {len(mydf)} records with AESTDTC after AEENDTC."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf

def impute_day01(date_series):
    return date_series.apply(lambda x: x if pd.isna(x) else f"{x[:10]}-01" if len(x) == 7 else x)
# Check this function later
def check_ae_aestdtc_after_dd(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for AE entries with AESTDTC after death date"
    datasets = "AE, DS, DD"
    
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    DD = load_data(data_path, 'dd')
    
    required_ae_columns = ["USUBJID", "AESTDTC", "AEDECOD", "AETERM", "AESDTH", "AEOUT"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    required_ds_columns = ["USUBJID", "DSSTDTC", "DSDECOD", "DSTERM"]
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    required_dd_columns = ["USUBJID", "DDDTC"]
    if not set(required_dd_columns).issubset(DD.columns):
        missing = set(required_dd_columns) - set(DD.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in EX: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    DS = preproc(DS, **kwargs)
    DD = preproc(DD, **kwargs)
    # Update AEDTHDTC in AE
    AE["AEDTHDTC"] = AE["AEENDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
    
    # Impute missing day as 01 for all date columns
    AE["AEDTHDTC"] = impute_day01(AE["AEDTHDTC"])
    AE["AESTDTC"] = impute_day01(AE["AESTDTC"])
    AE["AEENDTC"] = impute_day01(AE["AEENDTC"])
    DS["DSSTDTC"] = impute_day01(DS["DSSTDTC"])
    DD["DDDTC"] = impute_day01(DD["DDDTC"])
    
    # Subset AE to fewer variables
    AE = AE[["USUBJID", "AETERM", "AEDECOD", "AEDTHDTC", "AESTDTC","AEENDTC"]]
    
    # Get earliest death date by USUBJID from AE and DS
    ae_dd = AE.loc[~AE["AEDTHDTC"].isna(), ["USUBJID", "AEDTHDTC"]].drop_duplicates().sort_values(by=["USUBJID", "AEDTHDTC"])
    ds_dd = DS.loc[
        (DS["DSDECOD"].str.contains("DEATH", case=False, na=False) | DS["DSTERM"].str.contains("DEATH", case=False, na=False)) & 
        ~DS["DSSTDTC"].isna(),
        ["USUBJID", "DSSTDTC"]
    ].drop_duplicates()
    
    # Combine death dates from AE and DS
    death_dates = pd.merge(ae_dd, ds_dd, on="USUBJID", how="outer")

    if death_dates.empty:
        return pass_check(check_description, datasets)

    # Convert date columns to datetime
    death_dates["AEDTHDTC"] = pd.to_datetime(death_dates["AEDTHDTC"], errors='coerce')
    death_dates["DSSTDTC"] = pd.to_datetime(death_dates["DSSTDTC"], errors='coerce')
    death_dates["EARLIEST_DTHDTC"] = death_dates[["AEDTHDTC", "DSSTDTC"]].min(axis=1)

    df1 = AE.loc[AE["USUBJID"].isin(death_dates["USUBJID"]) & ~AE["AESTDTC"].isna()]

    df1["AESTDTC"] = pd.to_datetime(df1["AESTDTC"], errors='coerce')
    df1["AEENDTC"] = pd.to_datetime(df1["AEENDTC"], errors='coerce')

    df2 = df1.merge(death_dates, on="USUBJID", suffixes=(".AE", ".DS"), how="left")
    df = df2.loc[df2["AEENDTC"] > df2["EARLIEST_DTHDTC"], ["USUBJID", "AETERM", "AESTDTC", "AEENDTC", "EARLIEST_DTHDTC"]]

    if df.empty:
        return pass_check(check_description, datasets)
    else:
        message = "Fail"
        notes = f"{len(df['USUBJID'].unique())} patient(s) with AE occurring after death date."
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message)
        df.insert(2, "Notes", notes)
        df.insert(3, "Datasets", datasets)
        return df
def check_ae_aetoxgr(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    check_description = "Check for AE records where both AESEV and AETOXGR have missing values"
    AE = load_data(data_path, 'ae')
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    
    required_columns = ["USUBJID", "AETERM", "AESTDTC", "AEDECOD"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE records where both AESEV and AETOXGR have missing values"],
            "Message": [f"Check stopped running due to mssing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    if all(col in AE.columns for col in ["AETOXGR", "AESEV"]):
        has_na = AE["AETOXGR"].isna() & AE["AESEV"].isna()
        if has_na.any():
            df = AE.loc[has_na, ["USUBJID", "AETERM", "AESTDTC", "AEDECOD", "AETOXGR", "AESEV"]]
            return pd.DataFrame({
                "CHECK": ["Check for AE records where both AESEV and AETOXGR have missing values"],
                "Message": ["Fail"],
                "Notes": ["AE has records where both AESEV and AETOXGR have missing values."],
                "Datasets":[datasets],
                "Data": [df]
            })
        else:
            return pd.DataFrame({
                "CHECK": ["Check for AE records where both AESEV and AETOXGR have missing values"],
                "Message": ["Pass"],
                "Notes": [""],
                "Datasets":[datasets],
                "Data": [pd.DataFrame()]  # Return an empty DataFrame
            })
    
    if not any(col in AE.columns for col in ["AETOXGR", "AESEV"]):
        return pd.DataFrame({
            "CHECK": ["Check for AE records where both AESEV and AETOXGR have missing values"],
            "Message": ["Fail"],
            "Notes": ["AE is missing both the AETOXGR and AESEV variable."],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    toxgr_var = "AETOXGR" if "AETOXGR" in AE.columns else "AESEV"
    has_na = AE[toxgr_var].apply(is_null_or_empty)

    if has_na.any():
        df = AE.loc[has_na, ["USUBJID", "AETERM", "AESTDTC", "AEDECOD", toxgr_var]]
        message = 'Fail'
        notes = f"AE has {len(df)} record(s) with missing {toxgr_var}"
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message)
        df.insert(2, "Notes", notes)
        df.insert(3, "Datasets", datasets)
        return df
       
    else:
        return pd.DataFrame({
            "CHECK": ["Check for AE records where both AESEV and AETOXGR have missing values"],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

def check_ae_death(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    check_description = "Check for AE records with Grade 5 but inconsistencies in death-related variables"
    AE = load_data(data_path, 'ae')
    required_columns = ["USUBJID", "AETOXGR", "AEOUT", "AESTDTC", "AESDTH"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
        # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE records with Grade 5 but inconsistencies in death-related variables"],
            "Message": [f"Check stopped running due to missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    has_aesdth = AE["AETOXGR"] == "5"
    if not has_aesdth.any():
        return pd.DataFrame({
            "CHECK": ["Check for AE records with Grade 5 but inconsistencies in death-related variables"],
            "Message": ["Check not run, No records with AETOXGR = 5 found"],
            "Notes": [""],
            "Datasets":[datasets]
        })

    
    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    no_aedthdtc = AE['AESTDTC'].apply(is_null_or_empty)
    # Subset AE to records with Grade 5 AE but have missing death date, or not marked fatal, or death not indicated
    ae5 = AE.loc[
        (AE["AETOXGR"] == '5') &
        ((AE["AEOUT"] != 'FATAL') | AE["AEOUT"].isna() | no_aedthdtc| (AE["AESDTH"] != 'Y') | AE["AESDTH"].isna()),
        ['USUBJID', 'AETOXGR', 'AEOUT', 'AESTDTC', 'AESDTH']
    ]
    

    
    # Return message if no such Grade 5 records
    if ae5.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        message = "Fail"
        # Return subset dataframe if there are records with Grade 5 AE with missing death date, or not marked fatal, or death not indicated
        notes = f"Total number of records with grade 5 AEs and inconsistencies among AE death variables is {len(ae5)}."
        ae5.insert(0, "CHECK", check_description)
        ae5.insert(1, "Message", message)
        ae5.insert(2, "Notes", notes)
        ae5.insert(3, "Datasets", datasets)
        return ae5
def check_ae_ds_partial_death_dates(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE, DS"
    check_description = "Check for partial death dates in AE and DS"
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    required_ds_columns = ["USUBJID", "DSSCAT", "DSSTDTC", "DSDECOD"]
    required_ae_columns = ["USUBJID", "AESTDTC", "AEDECOD"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist in DS
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for partial death dates in AE and DS"],
            "Message": [f"Check stopped running due to missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Check if required variables exist in AE
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for partial death dates in AE and DS"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    DS = preproc(DS, **kwargs)
    no_aedthdtc = AE['AESTDTC'].apply(is_null_or_empty)
    no_dsstdtc = AE['AESTDTC'].apply(is_null_or_empty)
    # Find records with partial death dates (length < 10) in AE and DS
    mydf1 = DS.loc[(DS["DSDECOD"] == "DEATH") & no_dsstdtc & (DS["DSSTDTC"].str.len() < 10), ["USUBJID", "DSSCAT", "DSDECOD", "DSSTDTC"]]
    mydf2 = AE.loc[no_aedthdtc & (AE["AESTDTC"].str.len() < 10), ["USUBJID", "AEDECOD", "AESTDTC"]]

    mydf = pd.merge(mydf1, mydf2, on="USUBJID", how="outer")



    # Return message if no records
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        message = "Fail"
        # Return subset dataframe if there are records with partial dates
        notes = f"There are {len(mydf['USUBJID'].unique())} patients with partial death dates."
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
def check_ae_dup(data_path):
    datasets = "AE"
    check_description = "Check for duplicated AE entries"
    AE = load_data(data_path, 'ae')
    required_columns = ["USUBJID", "AEDECOD", "AESTDTC", "AEENDTC", "AETERM"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for duplicated AE entries"],
            "Message": [f"Check stopped running due to missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    if all(col in AE.columns for col in ["AETOXGR", "AESEV"]):
        return pd.DataFrame({
            "CHECK": ["Check for duplicated AE entries"],
            "Message": ["Fail"],
            "Notes": ["AE has both variables: AETOXGR and AESEV."],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    if not any(col in AE.columns for col in ["AETOXGR", "AESEV"]):
        return pd.DataFrame({
            "CHECK": ["Check for duplicated AE entries"],
            "Message": ["Fail"],
            "Notes": ["AE is missing both the AETOXGR and AESEV variable."],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    # Use either AETOXGR or AESEV, depending on which is in the AE dataset
    toxgr_var = "AETOXGR" if "AETOXGR" in AE.columns else "AESEV"
    lat_var = "AELAT" if "AELAT" in AE.columns else None

    if "AEMODIFY" not in AE.columns:
        # When AEMODIFY not in AE
        # Subsets to duplicated entries only
        df = AE[["USUBJID", "AETERM", "AEDECOD", "AESTDTC", "AEENDTC", toxgr_var] + ([lat_var] if lat_var else [])]
        df = df[df.duplicated(keep=False)]
    else:
        # When AEMODIFY in AE
        # Subsets to duplicated entries only
        df = AE[["USUBJID", "AETERM", "AEDECOD", "AESTDTC", "AEENDTC", "AEMODIFY", toxgr_var] + ([lat_var] if lat_var else [])]
        df = df[df.duplicated(keep=False)]

    # Outputs a resulting message depending on whether there are duplicates
    if not df.empty:
        message = "Fail"
        # Return subset dataframe if there are records with partial dates
        notes = f"There is {len(df['USUBJID'].unique())} with duplicate AE records"
        df.insert(0, "CHECK", check_description)
        df.insert(1, "Message", message)
        df.insert(2, "Notes", notes)
        df.insert(3, "Datasets", datasets)
        return df
    
    else:
        return pd.DataFrame({
            "CHECK": ["Check for duplicated AE entries"],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
def check_ae_fatal(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE"
    check_description = "Check for AE records with inconsistencies in fatal outcomes"
    AE = load_data(data_path, 'ae')
    required_columns = ["USUBJID", "AEDECOD", "AESTDTC", "AEOUT", "AESDTH"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check
    # Check if required variables exist
    if not set(required_columns).issubset(AE.columns):
        missing = set(required_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE records with inconsistencies in fatal outcomes"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
   
    outlist = []  # Empty list for results
    
    # Check if AEOUT == 'FATAL' and there is a corresponding AEDTHDTC (death date)
    
    # 1. AETOXGR exists and is populated
    if "AETOXGR" in AE.columns and not AE["AETOXGR"].isna().all():
        outlist.append(
            AE[(AE["AEOUT"] == 'FATAL') & 
               (AE["AEDTHDTC"].isna() | (AE["AETOXGR"] != '5') | AE["AETOXGR"].isna() | (AE["AESDTH"] != 'Y') | AE["AESDTH"].isna())]
        )
    
    # 2. AESEV exists and is populated
    if "AESEV" in AE.columns and not AE["AESEV"].isna().all():
        outlist.append(
            AE[(AE["AEOUT"] == 'FATAL') & 
               (AE["AEDTHDTC"].isna() | (AE["AESEV"] != 'SEVERE') | (AE["AESDTH"] != 'Y') | AE["AESDTH"].isna())]
        )
    
    # 3. If neither AETOXGR nor AESEV exist
    if "AETOXGR" not in AE.columns and "AESEV" not in AE.columns:
        outlist.append(
            AE[(AE["AEOUT"] == 'FATAL') & 
               (AE["AEDTHDTC"].isna() | (AE["AESDTH"] != 'Y') | AE["AESDTH"].isna())]
        )
    
    # 4. If both AETOXGR and AESEV exist but both are not populated
    if "AETOXGR" in AE.columns and "AESEV" in AE.columns:
        if AE["AETOXGR"].isna().all() and AE["AESEV"].isna().all():
            outlist.append(
                AE[(AE["AEOUT"] == 'FATAL') & 
                   (AE["AEDTHDTC"].isna() | (AE["AESDTH"] != 'Y') | AE["AESDTH"].isna())]
            )
    
    mydf = pd.concat(outlist).drop_duplicates()
    
    # Leave only variables on which we want to check for fatalities and their corresponding death dates
    mydf = mydf[list(set(AE.columns) & set(["USUBJID", "AEDECOD", "AESTDTC", "AEDTHDTC", "AEOUT", "AESEV", "AETOXGR", "AESDTH"]))]
    

    
    # Return message if no inconsistency between AEOUT and AEDTHDTC
    if mydf.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    # Return subset dataframe if there are records with inconsistency
    message = "Fail"
    notes = f"AE has {len(mydf['USUBJID'].unique())} patient(s) with AE death variable inconsistencies when outcome marked FATAL."
    mydf.insert(0, "CHECK", check_description)
    mydf.insert(1, "Message", message)
    mydf.insert(2, "Notes", notes)
    mydf.insert(3,"Datasets", datasets)
    return mydf

def check_ae_withdr_ds_discon(data_path, preproc=lambda df: df, **kwargs):
    datasets = "AE, DS"
    check_description = "Check for AE withdrawal and corresponding DS discontinuation"
    AE = load_data(data_path, 'ae')
    DS = load_data(data_path, 'ds')
    ts_file_path = os.path.join(data_path, "ts.sas7bdat")
    if  os.path.exists(ts_file_path):
        
        TS = load_data(data_path, 'ts')
        required_ts_columns = ["TSPARMCD", "TSVAL"]
    else:
        return pd.DataFrame({
            "CHECK": ["Check for AE withdrawal and corresponding DS discontinuation"],
            "Message": [f"Check stopped running due to TS dataset not found at the specified location: {ts_file_path}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    


    required_ae_columns = ["USUBJID", "AEACN"]
    empty_check = check_empty_dataset(AE,"AE",datasets,check_description)
    if empty_check is not None:
        return empty_check

    # Check if required variables exist in AE
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE withdrawal and corresponding DS discontinuation"],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Check if required variables exist in DS
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE withdrawal and corresponding DS discontinuation"],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Check if required variables exist in TS
    if not set(required_ts_columns).issubset(TS.columns):
        missing = set(required_ts_columns) - set(TS.columns)
        return pd.DataFrame({
            "CHECK": ["Check for AE withdrawal and corresponding DS discontinuation"],
            "Message": [f"Missing columns in TS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company specific preprocessing function
    AE = preproc(AE, **kwargs)
    DS = preproc(DS, **kwargs)
    TS = preproc(TS, **kwargs)

    # Calculate number of drugs in the study
    agent_num = TS[TS["TSPARMCD"].isin(["TRT", "COMPTRT"])].shape[0]

    # If a study is not single agent the check won't be executed
    if agent_num != 1:
        return pd.DataFrame({
            "CHECK": ["Check for AE withdrawal and corresponding DS discontinuation"],
            "Message": ["This check is only applicable for single agent studies, but based on TS domain this study is not single agent or study type cannot be determined."],
            "Notes": [""],
            "Datasets":[datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Only run for single agent studies
    if agent_num == 1:
        # In AE keep rows where the drug was withdrawn
        ae0 = AE[AE["AEACN"] == "DRUG WITHDRAWN"][["USUBJID", "AEACN", "AEDECOD"]]

        # Find matching patients in DS
        ds0 = DS[DS["USUBJID"].isin(ae0["USUBJID"])]
        ds1 = ds0[(ds0["DSSCAT"].str.contains("DISCON", case=False, na=False) |
                   ds0["DSSCAT"].str.upper().contains(['TREATMENT COMPLETION/EARLY DISCONTINUATION', 'TREATMENT EARLY DISCONTINUATION/COMPLETION', 'STUDY TREATMENT'])) &
                  (ds0["DSDECOD"].str.upper() != "COMPLETED") &
                  (ds0["DSCAT"].str.contains("DISPO", case=False, na=False))][["USUBJID", "DSSCAT", "DSCAT"]]

        # Check which patients have TREATMENT DISCON FORM
        mydfprep = pd.merge(ds1.drop_duplicates(), ae0, on="USUBJID", how="right")

        mydf = mydfprep[mydfprep["DSSCAT"].isna()]
        mydf = mydf.reset_index(drop=True)



        # Return message if no records with missing TREATMENT DISCON form
        if mydf.empty:
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Pass"],
                "Notes": [""],
                "Datasets":[datasets],
                "Data": [pd.DataFrame()]  # Return an empty DataFrame
            })

        # Return subset dataframe if there are records with missing TREATMENT DISCON
        notes = f"There are {mydf['USUBJID'].nunique()} patient(s) where AE data shows treatment discontinuation but no treatment discontinuation record in DS."
        message = "Fail"
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
       
# ae_plots.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

def compute_count(df, group_vars):
    # Assuming compute_count creates a count DataFrame grouped by specified variables
    return df.groupby(group_vars).size().reset_index(name='Count')

def generate_ae_plots(data_path):
    plots = []
    df = load_data(data_path, 'ae')
    # Determine the severity column
    ae_severity_col = None
    if "AESEV" in df.columns:
        ae_severity_col = "AESEV"
    elif "AETOXGR" in df.columns:
        ae_severity_col = "AETOXGR"

    # Heatmap Plot of AE by System Organ Class and Severity
    if ae_severity_col:
        ae_pivot = df.pivot_table(index="AEBODSYS", columns=ae_severity_col, aggfunc='size').fillna(0)
        x_labels = ae_pivot.columns.values.tolist()
        y_labels = ae_pivot.index.values.tolist()
      
        fig_heatmap = go.Figure(data=go.Heatmap(
            x=x_labels,
            y=y_labels,
            z=ae_pivot.values.tolist(),
            colorscale='YlGnBu',
            hoverongaps=False,
            hovertemplate='<b>System Organ Class:</b> %{y}<br>' +
                          '<b>Severity:</b> %{x}<br>' +
                          '<b>Count:</b> %{z}<br><extra></extra>'
        ))
        fig_heatmap.update_layout(
            title='Heat Map of Adverse Events by System Organ Class and Severity',
            xaxis_title='Severity',
            yaxis_title='System Organ Class',
            height=500,
            width=1000,
            margin=dict(l=60, r=60, t=60, b=60)
        )
        #plots.append(dcc.Graph(id='ae-heatmap', figure=fig_heatmap, style={'width': '100%'}))
        plot_html = fig_heatmap.to_html(full_html=False)
        plots.append(plot_html)
    # Bar Plot of AE by AETERM and AESTDY
    fig_bar = px.bar(
        df,
        x='AESTDY',
        y='AEDECOD',
        color=ae_severity_col,
        orientation='h',
        barmode='group',
        height=700,
        width=1000
    )
    fig_bar.update_layout(
        title='Bar Plot of Adverse Events by AETERM and AESTDY',
        xaxis_title='Start Day',
        yaxis_title='Adverse Event Term',
        margin=dict(l=60, r=60, t=60, b=60)
    )
    plot_html = fig_bar.to_html(full_html=False)
    plots.append(plot_html)
    #plots.append(dcc.Graph(id='ae-bar', figure=fig_bar, style={'width': '100%'}))

    # Bar Plot of AE by System Organ Class and Treatment
    counts_df = compute_count(df, ['AEBODSYS'])
    fig_bar_soc = px.bar(
        counts_df.sort_values(by=['AEBODSYS'], ascending=[False]),
        x='Count',
        y='AEBODSYS',
        orientation='h',
        barmode='group',
        height=1000,
        width=1000
    )
    fig_bar_soc.update_traces(texttemplate='(%{value})', textposition='outside')
    fig_bar_soc.update_layout(
        title='Bar Plot of Adverse Events by System Organ Class',
        xaxis_title='Number of Subjects',
        yaxis_title='System Organ Class',
        margin=dict(l=60, r=60, t=60, b=60)
    )
    plot_html = fig_bar_soc.to_html(full_html=False)
    plots.append(plot_html)
    #plots.append(dcc.Graph(id='ae-bar-soc', figure=fig_bar_soc, style={'width': '100%'}))

    # Treemap Plot of AE by Body System and Preferred Term
    grouped_df = df.groupby(['AEBODSYS', 'AEDECOD']).size().reset_index(name='count')
    fig_treemap = px.treemap(
        grouped_df,
        path=['AEBODSYS', 'AEDECOD'],
        values='count',
        color='AEBODSYS',
        color_discrete_sequence=px.colors.qualitative.Dark2,
        height=1000,
        width=1000
    )
    fig_treemap.update_layout(
        title='Treemap Plot of Adverse Events by Body System and Preferred Term',
        margin=dict(l=10, r=10, t=60, b=10)
    )
    plot_html = fig_treemap.to_html(full_html=False)
    plots.append(plot_html)

    return plots
    #plots.append(dcc.Graph(id='ae-treemap', figure=fig_treemap, style={'width': '100%'}))

    # Arrange plots in rows of three
    #plot_rows = [html.Div(plot, style={'width': '100%', 'margin-bottom': '40px'}) for plot in plots]

    #return plot_rows
