# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 15:39:42 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month, format_dates
import os


def check_qs_dup(data_path):
    check_description = "Check for duplicate dates in QS for the same visit"
    datasets = "QS"
    qs_file_path = os.path.join(data_path, "qs.sas7bdat")

    if not os.path.exists(qs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to QS dataset not found at the specified location: {qs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    QS = load_data(data_path, 'qs')
    required_columns = ["USUBJID", "QSCAT", "QSDTC", "VISIT"]

    # Check if required variables exist in QS
    if not set(required_columns).issubset(QS.columns):
        missing = set(required_columns) - set(QS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in PR: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    # Remove time and get unique records by category, date, visit
    QS["QSDTC1"] = QS["QSDTC"].str[:10]

    df = QS.loc[~QS["VISIT"].str.upper().str.contains("UNSCHEDU"), ["USUBJID", "QSCAT", "QSDTC1", "VISIT"]].drop_duplicates()
    df = df.rename(columns={"QSDTC1": "QSDTC"})

    # Get duplicates records by category, date
    df2 = df.groupby(["USUBJID", "QSCAT", "VISIT"]).filter(lambda x: len(x) > 1)

    # Outputs a resulting message depending on whether there are duplicates
    if not df2.empty:
        return fail_check(check_description, "QS", "Multiple dates for the same visit in QS.", df2)
    else:
        return pass_check(check_description, "QS")

def check_qs_qsdtc_after_dd(data_path):
    check_description = "Check for QS records with QSDTC occurring after death date"
    datasets = "QS, AE, DS"
    qs_file_path = os.path.join(data_path, "qs.sas7bdat")
    if  os.path.exists(qs_file_path):
        QS = load_data(data_path, 'qs')
        required_qs_columns = ["USUBJID", "QSDTC", "QSCAT", "QSORRES", "VISIT"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to QS dataset not found at the specified location: {qs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    ae_file_path = os.path.join(data_path, "ae.sas7bdat")
    if  os.path.exists(ae_file_path):
        AE = load_data(data_path, 'ae')
        required_ae_columns = ["USUBJID", "AESTDTC", "AEDECOD", "AETERM"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to AE dataset not found at the specified location: {ae_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    ds_file_path = os.path.join(data_path, "ds.sas7bdat")
    if  os.path.exists(ds_file_path):
        DS = load_data(data_path, 'ds')
        required_ds_columns = ["USUBJID", "DSSTDTC", "DSDECOD", "DSTERM"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to DS dataset not found at the specified location: {ds_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    # Check if required variables exist in AE, DS, and QS
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    
    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    
    if not set(required_qs_columns).issubset(QS.columns):
        missing = set(required_qs_columns) - set(QS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in QS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    # Add day of "01" to dates that are in the format of "yyyy-mm"
    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
    AE["AEDTIMP"] = impute_day01(AE["AEDTHDTC"])
    AE["AESTDTIMP"] = impute_day01(AE["AESTDTC"])
    DS["DSSTDTIMP"] = impute_day01(DS["DSSTDTC"])
    QS["QSDTC"] = impute_day01(QS["QSDTC"])

    # Get earliest death date by USUBJID
    ae_dd = AE.loc[~AE["AEDTIMP"].apply(is_null_or_empty), ["USUBJID", "AEDTHDTC", "AEDTIMP"]].drop_duplicates().sort_values(by=["USUBJID", "AEDTIMP"])
    ds_dd = DS.loc[((DS["DSDECOD"].str.contains("DEATH", case=False, na=False)) | (DS["DSTERM"].str.contains("DEATH", case=False, na=False))) & ~DS["DSSTDTIMP"].apply(is_null_or_empty), ["USUBJID", "DSSTDTC", "DSSTDTIMP"]].drop_duplicates().sort_values(by=["USUBJID", "DSSTDTIMP"])

    death_dates = pd.merge(ae_dd, ds_dd, on="USUBJID", how="outer")

    if death_dates.empty:
        return pass_check(check_description, "QS")

    death_dates["EARLIEST_DTHDT"] = death_dates[["AEDTIMP", "DSSTDTIMP"]].min(axis=1)
    death_dates["EARLIEST_DTHDTC"] = death_dates.apply(lambda row: row["AEDTHDTC"] if row["AEDTIMP"] <= row["DSSTDTIMP"] else row["DSSTDTC"], axis=1)

    if "QSSTAT" in QS.columns:
        mydf0 = QS.loc[~QS["QSSTAT"].str.contains("NOT DONE", case=False, na=False) & QS["USUBJID"].isin(death_dates["USUBJID"]) & ~QS["QSDTC"].apply(is_null_or_empty) & ~QS["QSORRES"].apply(is_null_or_empty)]
    else:
        mydf0 = QS.loc[QS["USUBJID"].isin(death_dates["USUBJID"]) & ~QS["QSDTC"].apply(is_null_or_empty) & ~QS["QSORRES"].apply(is_null_or_empty)]

    mydf0 = pd.merge(mydf0, death_dates, on="USUBJID", how="left")
    mydf = mydf0.loc[pd.to_datetime(mydf0["EARLIEST_DTHDT"]) < pd.to_datetime(mydf0["QSDTC"]), ["USUBJID", "QSDTC", "VISIT", "QSCAT", "AEDTHDTC", "DSSTDTC", "EARLIEST_DTHDTC"]]

    if mydf.empty:
        return pass_check(check_description, "QS")
    else:
        
        return fail_check(check_description, "QS", f"{mydf['USUBJID'].nunique()} unique patient(s) with {len(mydf)} QS record(s) occurring after death date.", mydf.drop_duplicates())
def check_qs_qsdtc_visit_ordinal_error(data_path):
    check_description = "Check for QS entries with QSDTC Visit Ordinal Error"
    datasets = "QS"
    qs_file_path = os.path.join(data_path, "qs.sas7bdat")
    if  os.path.exists(qs_file_path):
        QS = load_data(data_path, 'qs')
        required_qs_columns = ["USUBJID", "VISITNUM", "VISIT", "QSDTC", "QSSTAT"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to QS dataset not found at the specified location: {qs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    # First check that required variables exist and return a message if they don't
    if not set(required_qs_columns).issubset(QS.columns):
        missing = set(required_qs_columns) - set(QS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in QS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Don't run if VISITNUM is all missing
    if QS["VISITNUM"].nunique() <= 1:
        return fail_check(check_description, datasets, "VISITNUM exists but only a single value.")

    # Only keep records not indicated as NOT DONE and drop Unscheduled and Tx Discon visits
    subset_df = QS[(QS["QSSTAT"] != "NOT DONE") & (~QS["VISIT"].str.contains("UNSCHEDU|TREATMENT OR OBSERVATION FU COMP EARLY DISC", case=False))]
    
    if subset_df.empty:
        return fail_check(check_description, datasets, "No QS records when subset to exclude NOT DONE.")
    
    # Remove duplicates and sort by USUBJID, VISITNUM, and QSDTC
    subset_df = subset_df.drop_duplicates(subset=["USUBJID", "VISITNUM", "QSDTC"])
    subset_df = subset_df.sort_values(by=["USUBJID", "VISITNUM", "QSDTC"]).reset_index(drop=True)

    # Check for QSDTC order within VISITNUM
    #subset_df["QSDTC"] = pd.to_datetime(subset_df["QSDTC"], errors='coerce')
    subset_df["QSDTC"] = subset_df["QSDTC"].apply(format_dates)
    subset_df["DTC_order"] = subset_df.groupby("USUBJID")["QSDTC"].rank(method="first", ascending=True)
    subset_df["Vis_order"] = subset_df.groupby("USUBJID")["VISITNUM"].rank(method="first", ascending=True)

    # Subset if Vis_order not equal to DTC_order
    myout = subset_df[subset_df["DTC_order"] != subset_df["Vis_order"]]
    
    # Add sorting
    myout = myout.sort_values(by=["USUBJID", "VISITNUM", "QSDTC"]).reset_index(drop=True)
    

        # Return message if no records with QSDTC per VISITNUM
    if myout.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"QS has {len(myout)} record(s) with Possible QSDTC data entry error.", myout)
def check_qs_qsstat_qsreasnd(data_path):
    check_description = "Check for QS records with QSSTAT 'NOT DONE' but QSREASND not given"
    datasets = "QS"
    qs_file_path = os.path.join(data_path, "qs.sas7bdat")
    if  os.path.exists(qs_file_path):
        QS = load_data(data_path, 'qs')
        required_columns = ["USUBJID", "QSCAT", "QSDTC", "QSSTAT", "QSREASND"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to QS dataset not found at the specified location: {qs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    


    # Check if required variables exist in QS

    if not set(required_columns).issubset(QS.columns):
        missing = set(required_columns) - set(QS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in QS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    select_vars = list(set(required_columns + ["VISIT"]).intersection(QS.columns))

    # Filter QS for records where QSSTAT is 'NOT DONE' and QSREASND is missing
    check_results = QS.loc[
        (QS["QSSTAT"].str.upper().str.strip() == 'NOT DONE') & (QS["QSREASND"].apply(is_null_or_empty)),
        select_vars
    ]

    if check_results.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(
            check_description, 
            datasets, 
            f"Completion status for {len(check_results)} record(s) is 'NOT DONE' but Reason Not Performed not given.", 
            check_results
        ) 
def check_qs_qsstat_qsstresc(data_path):
    check_description = "Check for QS records with QSSTAT 'NOT DONE' but QSSTRESC not missing"
    datasets = "QS"
    qs_file_path = os.path.join(data_path, "qs.sas7bdat")

    # Check if QS file exists
    if not os.path.exists(qs_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to QS dataset not found at the specified location: {qs_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Load QS dataset
    QS = load_data(data_path, 'qs')
    #print(f"Columns in QS: {list(QS.columns)}")  # Debugging: Print the columns in QS

    # Check if QS is empty
    if QS.empty:
        print("QS dataset is empty.")  # Debugging: Print a message if QS is empty
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["QS dataset is empty. No checks performed."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Define required columns
    required_columns = ["USUBJID", "QSSTRESC", "QSSTAT", "QSCAT", "QSDTC", "QSTESTCD"]

    # Add VISIT to required columns if it exists
    if "VISIT" in QS.columns:
        required_columns.append("VISIT")

    # Check for missing columns
    missing_columns = set(required_columns) - set(QS.columns)
    if missing_columns:
        print(f"Missing columns in QS: {missing_columns}")  # Debugging: Print missing columns
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in QS: {', '.join(missing_columns)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset QS to rows where QSSTAT = NOT DONE and QSTESTCD = QSALL
    qsND = QS[(QS["QSSTAT"] == "NOT DONE") & (QS["QSTESTCD"] == "QSALL")][required_columns]

    # Subset QS to rows where QSSTRESC is not missing
    qsANS = QS[~QS["QSSTRESC"].apply(is_null_or_empty)][required_columns]

    # Merge the datasets on common columns
    merge_columns = ["USUBJID", "QSCAT", "QSDTC"]
    if "VISIT" in QS.columns:
        merge_columns.append("VISIT")

    qsPREP = pd.merge(
        qsND[merge_columns + ["QSSTAT"]],
        qsANS[merge_columns + ["QSSTRESC"]],
        on=merge_columns,
        how="left"
    )

    # Filter the merged dataset to find records with issues
    mydf = qsPREP[(qsPREP["QSSTAT"] == "NOT DONE") & (~qsPREP["QSSTRESC"].apply(is_null_or_empty))]

    # Remove duplicates
    mydf = mydf.drop_duplicates().reset_index(drop=True)

    # Return message if no records with issue in QS
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        # Return subset dataframe if there are issues in QS with NOT DONE but results
        return fail_check(
            check_description,
            datasets,
            "There are non-missing QSSTRESC records for the following visits when QSSTAT=NOT DONE and QSTESTCD=QSALL.",
            mydf
        )