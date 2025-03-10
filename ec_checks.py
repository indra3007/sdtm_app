# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 09:41:53 2024

@author: inarisetty
"""
import pandas as pd 
import os 
from datetime import datetime

from utils import load_data,is_null_or_empty, is_null_or_empty2

def check_ec_sc_lat(data_path):
    datasets = "EC, SC"
    ec_file_path = os.path.join(data_path, "ec.sas7bdat")
    if  os.path.exists(ec_file_path):
        EC = load_data(data_path, 'EC')
        required_columns_EC = ["USUBJID", "ECMOOD", "ECSTDY", "VISIT", "ECSTDTC", "ECOCCUR", "ECROUTE"]
    else:
        return pd.DataFrame({
            "CHECK": ["Check for EC and SC consistency"],
            "Message": [f"Check stopped running due to EC dataset not found at the specified location: {ec_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    sc_file_path = os.path.join(data_path, "sc.sas7bdat")
    if  os.path.exists(ec_file_path):
        SC = load_data(data_path, 'SC')
        required_columns_SC = ["USUBJID", "SCTEST", "SCTESTCD", "SCCAT", "SCORRES", "SCDTC"]
    else:
        return pd.DataFrame({
            "CHECK": ["Check for EC and SC consistency"],
            "Message": [f"Check stopped running due to SC dataset not found at the specified location: {sc_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    def lacks_msg(df, cols):
        missing = [col for col in cols if col not in df.columns]
        return f"Missing columns: {', '.join(missing)}"

    
    

    if not set(required_columns_SC).issubset(SC.columns):
        return pd.DataFrame({
            "CHECK": ["Check for EC and SC consistency"],
            "Message": [lacks_msg(SC, required_columns_SC)],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    if not set(required_columns_EC).issubset(EC.columns):
        return pd.DataFrame({
            "CHECK": ["Check for EC and SC consistency"],
            "Message": [lacks_msg(EC, required_columns_EC)],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Filter for records where Study Drug was administered in the eye
    EC = EC[EC["ECROUTE"].isin([
        "INTRAVENOUS", "ORAL", "INTRAMUSCULAR", "SUBCUTANEOUS",
        "INTRATHECAL", "INTRAPERITONEAL", "INTRA-ARTERIAL","INTRAARTERIAL", "TOPICAL",
        "INTRAVESICAL", "INHALATION","RECTAL"
    ])]

    if EC.empty:
        return pd.DataFrame({
            "CHECK": ["Check for EC and SC consistency"],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    additional_required_columns_EC = ["ECLAT", "ECLOC"]
    if not set(additional_required_columns_EC).issubset(EC.columns):
        return pd.DataFrame({
            "CHECK": ["Check for EC and SC consistency"],
            "Message": [lacks_msg(EC, additional_required_columns_EC)],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Process SC data
    SC = SC[SC["SCTESTCD"].str.upper() == "FOCID"]
    SC["SC_STUDYEYE"] = SC["SCORRES"].str.upper().replace({"OS": "LEFT", "OD": "RIGHT"})

    # Process EC data
    if "ECCAT" in EC.columns:
        EC = EC[(EC["ECMOOD"].str.upper() == "PERFORMED") & (EC["ECOCCUR"] == "Y") &
                (EC["ECLOC"].str.upper() == "EYE") & (~EC["ECCAT"].str.contains("FELLOW", case=False))]
    else:
        EC = EC[(EC["ECMOOD"].str.upper() == "PERFORMED") & (EC["ECOCCUR"] == "Y") &
                (EC["ECLOC"].str.upper() == "EYE")]

    my_select_var = ["USUBJID", "ECCAT", "ECROUTE", "ECLOC", "ECMOOD", "ECLAT", "ECSTDY", "VISIT", "ECSTDTC", "ECOCCUR"]
    EC = EC[my_select_var]

    # Merge SC & EC by USUBJID & Create a variable when STUDYEYE do not match with ECLAT
    mydf1 = SC.merge(EC, on="USUBJID", how="outer")
    mydf1["MISFLAG"] = ((mydf1["SC_STUDYEYE"].str.upper() != mydf1["ECLAT"].str.upper()) |
                        mydf1["ECLAT"].apply(is_null_or_empty2)).astype(int)

    mydf = mydf1[(mydf1["MISFLAG"] == 1) & ((mydf1["ECROUTE"] != "NON-OCULAR ROUTE") | mydf1["ECROUTE"].apply(is_null_or_empty2))]
    mydf = mydf.drop(columns=["MISFLAG", "SCTESTCD", "SCTEST", "SCCAT", "ECLOC", "ECMOOD", "ECOCCUR", "SCORRES"])

    if mydf.empty:
        return pd.DataFrame({
            "CHECK": ["Check for EC and SC consistency"],
            "Message": ["Pass"],
            "Notes": [""],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    else:
        message = "Fail"
        notes = f"{len(mydf)} record(s) with Study Drug not administered in the Study."
        check_description = "Check for EC and SC consistency"
        mydf.insert(0, "CHECK", check_description)
        mydf.insert(1, "Message", message)
        mydf.insert(2, "Notes", notes)
        mydf.insert(3, "Datasets", datasets)
        return mydf
