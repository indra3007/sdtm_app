# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 12:38:58 2024

@author: inarisetty
"""
import pandas as pd
from pandas.api.types import is_string_dtype
from datetime import datetime, timedelta
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month
import os


def check_ts_aedict(data_path):
    required_columns = ["TSPARMCD", "TSVAL"]
    check_description = "Check for MedDRA version in TS"
    datasets = "TS"
    ts_file_path = os.path.join(data_path, "ts.sas7bdat")

    if not os.path.exists(ts_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TS dataset not found at the specified location: {ts_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TS = load_data(data_path, 'ts')
    if not set(required_columns).issubset(TS.columns):
        missing = set(required_columns) - set(TS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    # Identify current MedDRA version
    today = datetime.today()
    year = today.year

    # Determine first Monday of May and November
    may_first = datetime(year, 5, 1)
    november_first = datetime(year, 11, 1)

    date1 = may_first + timedelta(days=(0 - may_first.weekday()) % 7)
    date2 = november_first + timedelta(days=(0 - november_first.weekday()) % 7)

    meddra_version = year - 2021 + 24

    # Determine MedDRA version number
    if today < date1:
        meddra_version_num = str(meddra_version - 0.9)
    elif date1 <= today < date2:
        meddra_version_num = f"{meddra_version}.0"
    else:
        meddra_version_num = str(meddra_version + 0.1)

    # Subset TS to only AEDICT records
    mydf = TS[TS["TSPARMCD"] == "AEDICT"][["TSPARMCD", "TSVAL"]]

    # Print to report
    if len(mydf) == 1:
        mydf["Current_MedDRA_version"] = meddra_version_num

        meddra = mydf["TSVAL"].values[0].strip()
        meddra_short = meddra[-4:]

        if pd.isna(meddra) or meddra == '':
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Fail"],
                "Notes": ["No value in TS.TSVAL where TS.TSPARMCD=AEDICT."],
                "Datasets": [datasets],
                "Data": [mydf]
            })
        elif meddra_short != meddra_version_num:
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Fail"],
                "Notes": [f"MedDRA version in TS.TSVAL where TS.TSPARMCD=AEDICT is not the latest version as of {today.date()}"],
                "Datasets": [datasets],
                "Data": [mydf]
            })
        elif "MEDDRA" not in meddra.upper():
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Fail"],
                "Notes": ["The string 'MedDRA' not found in TS.TSVAL where TS.TSPARMCD=AEDICT."],
                "Datasets": [datasets],
                "Data": [mydf]
            })
        else:
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Pass"],
                "Notes": [""],
                "Datasets": [datasets],
                "Data": [pd.DataFrame()]  # Return an empty DataFrame
            })

    elif len(mydf) < 1:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["No record where TS.TSPARMCD=AEDICT."],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["Multiple records where TS.TSPARMCD=AEDICT."],
            "Datasets": [datasets],
            "Data": [mydf]
        })
def check_ts_cmdict(data_path):
    required_columns = ["TSPARMCD", "TSVAL"]
    check_description = "Check for WHODrug version in TS"
    datasets = "TS"
    ts_file_path = os.path.join(data_path, "ts.sas7bdat")

    if not os.path.exists(ts_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TS dataset not found at the specified location: {ts_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TS = load_data(data_path, 'ts')
    if not set(required_columns).issubset(TS.columns):
        missing = set(required_columns) - set(TS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Identify current WHODrug version
    today = datetime.today()
    year = today.year

    # Determine first Monday of May and November
    may_first = datetime(year, 5, 1)
    november_first = datetime(year, 11, 1)

    date1 = may_first + timedelta(days=(0 - may_first.weekday()) % 7)
    date2 = november_first + timedelta(days=(0 - november_first.weekday()) % 7)

    # Determine WHODrug version
    if today < date1:
        whodrug_ver = f"SEPTEMBER 1, {year - 1}"
    elif date1 <= today < date2:
        whodrug_ver = f"MARCH 1, {year}"
    else:
        whodrug_ver = f"SEPTEMBER 1, {year}"

    version = f"WHODRUG GLOBAL B3 {whodrug_ver}"

    # Subset TS to only CMDICT records
    mydf = TS[TS["TSPARMCD"] == "CMDICT"][["TSPARMCD", "TSVAL"]]

    if len(mydf) == 1:
        mydf["Current_WHODRUG_ver"] = version

        whodrug = mydf["TSVAL"].values[0].strip()

        if pd.isna(whodrug) or whodrug == '':
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Fail"],
                "Notes": ["No value in TS.TSVAL where TS.TSPARMCD=CMDICT."],
                "Datasets": [datasets],
                "Data": [mydf]
            })

        elif whodrug.upper() != version.upper():
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Fail"],
                "Notes": [f"WHODrug version in TS.TSVAL where TS.TSPARMCD=CMDICT is not the latest version as of {today.date()} or not an exact string match."],
                "Datasets": [datasets],
                "Data": [mydf]
            })

        elif "WHODRUG" not in whodrug.upper():
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Fail"],
                "Notes": ["The string 'WHODRUG' not found in TS.TSVAL where TS.TSPARMCD=CMDICT."],
                "Datasets": [datasets],
                "Data": [mydf]
            })

        else:
            return pd.DataFrame({
                "CHECK": [check_description],
                "Message": ["Pass"],
                "Notes": [""],
                "Datasets": [datasets],
                "Data": [pd.DataFrame()]  # Return an empty DataFrame
            })

    elif len(mydf) < 1:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["No record where TS.TSPARMCD=CMDICT."],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["Multiple records where TS.TSPARMCD=CMDICT."],
            "Datasets": [datasets],
            "Data": [mydf]
        })
def check_ts_sstdtc_ds_consent(data_path):
    check_description = "Check for Study Start Date in TS"
    datasets = "TS, DS"
    ts_file_path = os.path.join(data_path, "ts.sas7bdat")

    if not os.path.exists(ts_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to TS dataset not found at the specified location: {ts_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    TS = load_data(data_path, 'ts')
    DS = load_data(data_path, 'ds')
    required_ds_columns = ["DSCAT", "DSSCAT", "DSDECOD", "DSSTDTC"]
    required_ts_columns = ["TSPARMCD", "TSPARM", "TSVAL"]


    if not set(required_ds_columns).issubset(DS.columns):
        missing = set(required_ds_columns) - set(DS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in DS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_ts_columns).issubset(TS.columns):
        missing = set(required_ts_columns) - set(TS.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in TS: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if "SSTDTC" not in TS["TSPARMCD"].values:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["TS.TSPARMCD = 'SSTDTC' (Study Start Date), which is required for FDA submissions, not found. Date in TSVAL should correspond with earliest informed consent date of enrolled patient."],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset TS to only SSTDTC record
    mydf = TS[TS["TSPARMCD"] == "SSTDTC"][["TSPARMCD", "TSPARM", "TSVAL"]]
    mydf["DS_FIRST_ICDATE"] = None

    # Identify earliest informed consent date
    ic = DS[(DS["DSDECOD"] == "INFORMED CONSENT OBTAINED") &
            (DS["DSCAT"] == 'PROTOCOL MILESTONE') &
            (DS["DSSCAT"].str.startswith('PROTOCOL'))][["DSCAT", "DSSCAT", "DSDECOD", "DSSTDTC"]]

    if len(ic) >= 1:
        ic["icdate"] = ic["DSSTDTC"].str[:10]
        ic = ic[ic["DSSTDTC"].str.len() == 10]
        ic["icdate"] = pd.to_datetime(ic["icdate"])
        ic = ic[ic["icdate"] == ic["icdate"].min()]
        mydf["DS_FIRST_ICDATE"] = ic["icdate"].values[0]

    # Check for various conditions and return appropriate messages
    if len(mydf) > 1:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["Multiple records with TS.TSPARMCD = 'SSTDTC' (Study Start Date) found when only one expected. TS with Study Start Date required for FDA submissions."],
            "Datasets": [datasets],
            "Data": [mydf]
        })

    if mydf["TSVAL"].isna().any():
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["TS.TSPARMCD = 'SSTDTC' (Study Start Date) has missing TS.TSVAL (yyyy-mm-dd) character date. TS with Study Start Date required for FDA submissions."], 
            "Datasets": [datasets],
            "Data": [mydf]
        })

    if mydf["TSVAL"].str.len().any() < 10:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["TS.TSPARMCD = 'SSTDTC' (Study Start Date) is missing complete TS.TSVAL (yyyy-mm-dd) character date. TS with Study Start Date required for FDA submissions."],
           
            "Datasets": [datasets],
            "Data": [mydf]
        })

    if mydf["DS_FIRST_ICDATE"].isna().any():
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Fail"],
            "Notes": ["TS.TSPARMCD = 'SSTDTC' (Study Start Date) has TS.TSVAL (yyyy-mm-dd), which is required for FDA submissions, but earliest informed consent date from DS cannot be calculated as a reference date."],
            "Datasets": [datasets],
            "Data": [mydf]
        })

    if mydf["TSVAL"].values[0] == mydf["DS_FIRST_ICDATE"].values[0]:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    return pd.DataFrame({
        "CHECK": [check_description],
        "Message": ["Fail"],
        "Notes": ["TS.TSPARMCD = 'SSTDTC' (Study Start Date) has TS.TSVAL that does not match earliest informed consent date based on DS. TS with Study Start Date required for FDA submissions."],
        "Datasets": [datasets],
        "Data": [mydf]
    })