# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 11:03:17 2024

@author: inarisetty
"""

import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month, convert_date, format_dates
import os
import pandas as pd
import plotly.graph_objects as go
import re
from dash import dcc, html

def check_lb_lbdtc_after_dd(data_path):
    check_description = "Check for LB entries with LBDTC after death date"
    datasets = "LB, DS, AE"
    lb_file_path = os.path.join(data_path, "lb.sas7bdat")
    if  os.path.exists(lb_file_path):
        LB = load_data(data_path, 'lb')
        required_lb_columns = ["USUBJID", "LBDTC", "LBTESTCD", "LBORRES"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to LB dataset not found at the specified location: {lb_file_path}"],
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
    if not set(required_lb_columns).issubset(LB.columns):
        missing = set(required_lb_columns) - set(LB.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in LB: {', '.join(missing)}"],
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
    if not set(required_ae_columns).issubset(AE.columns):
        missing = set(required_ae_columns) - set(AE.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in AE: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Apply imputation
    AE["AEDTHDTC"] = AE["AESTDTC"].where((AE["AESDTH"] == "Y") | (AE["AEOUT"] == "FATAL"), other=None)
    AE["AESTDTC"] = impute_day01(AE["AESTDTC"])
    DS["DSSTDTC"] = impute_day01(DS["DSSTDTC"])
    
    LB["LBDTC"] = impute_day01(LB["LBDTC"]) 
    AE["AEDTHDTC"] = pd.to_datetime(AE["AEDTHDTC"], errors='coerce')
    DS["DSSTDTC"] = pd.to_datetime(DS["DSSTDTC"], errors='coerce')
    LB["LBDTC"] = pd.to_datetime(LB["LBDTC"], errors='coerce')
    # Get earliest death date by USUBJID
    ae_dd = (AE[~AE["AEDTHDTC"].apply(is_null_or_empty)]
             .drop_duplicates(subset=["USUBJID", "AEDTHDTC"])
             .sort_values(by=["USUBJID", "AEDTHDTC"]))
    
    ds_dd = (DS[(DS["DSDECOD"].str.contains("DEATH", case=False, na=False) | DS["DSTERM"].str.contains("DEATH", case=False, na=False)) & 
                ~DS["DSSTDTC"].apply(is_null_or_empty)]
             .drop_duplicates(subset=["USUBJID", "DSSTDTC"])
             .sort_values(by=["USUBJID", "DSSTDTC"]))
    
    death_dates = pd.merge(ae_dd, ds_dd, on="USUBJID", how="outer")

    if death_dates.empty:
        return pass_check(check_description, datasets)

    death_dates["EARLIEST_DTHDTC"] = death_dates[["AEDTHDTC", "DSSTDTC"]].min(axis=1)

    mydf0 = (LB[(LB["USUBJID"].isin(death_dates["USUBJID"])) & 
                ~LB["LBDTC"].apply(is_null_or_empty) & 
                ~LB["LBORRES"].apply(is_null_or_empty)]
             .drop(columns=["LBORRES"])
             .merge(death_dates, on="USUBJID", how="left"))

    #mydf = mydf0[pd.to_datetime(mydf0["EARLIEST_DTHDTC"]) < pd.to_datetime(mydf0["LBDTC"])]
    mydf = mydf0[mydf0['EARLIEST_DTHDTC'] < mydf0['LBDTC']]
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"{len(mydf['USUBJID'].unique())} patient(s) with LB occurring after death date.", mydf)
    
def check_lb_lbdtc_visit_ordinal_error(data_path):
    check_description = "Check for LB entries with LBDTC Visit Ordinal Error"
    datasets = "LB"
    lb_file_path = os.path.join(data_path, "lb.sas7bdat")
    if  os.path.exists(lb_file_path):
        LB = load_data(data_path, 'lb')
        required_lb_columns = ["USUBJID", "VISITNUM", "VISIT", "LBDTC", "LBSTAT"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to LB dataset not found at the specified location: {lb_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    # First check that required variables exist and return a message if they don't
    if not set(required_lb_columns).issubset(LB.columns):
        missing = set(required_lb_columns) - set(LB.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in LB: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Don't run if VISITNUM is all missing
    if LB["VISITNUM"].nunique() <= 1:
        return fail_check(check_description, datasets, "VISITNUM exists but only a single value.")

    # Only keep records not indicated as NOT DONE and drop Unscheduled and Tx Discon visits
    subset_df = LB[(LB["LBSTAT"] != "NOT DONE") & (~LB["VISIT"].str.contains("UNSCHEDU|TREATMENT OR OBSERVATION FU COMP EARLY DISC", case=False))]
    
    if subset_df.empty:
        return fail_check(check_description, datasets, "No lab records when subset to exclude NOT DONE.")
    
    # Remove duplicates and sort by USUBJID, VISITNUM, and LBDTC
    subset_df = subset_df.drop_duplicates(subset=["USUBJID", "VISITNUM", "LBDTC"])
    subset_df = subset_df.sort_values(by=["USUBJID", "VISITNUM", "LBDTC"]).reset_index(drop=True)

    # Check for LBDTC order within VISITNUM
    #subset_df["LBDTC"] = pd.to_datetime(subset_df["LBDTC"], errors='coerce')
    #subset_df = convert_date(subset_df, "LBDTC")
    subset_df["LBDTC"] = subset_df["LBDTC"].apply(format_dates)

    subset_df["DTC_order"] = subset_df.groupby("USUBJID")["LBDTC"].rank(method="first", ascending=True)
    subset_df["Vis_order"] = subset_df.groupby("USUBJID")["VISITNUM"].rank(method="first", ascending=True)

    # Subset if Vis_order not equal to DTC_order
    myout = subset_df[subset_df["DTC_order"] != subset_df["Vis_order"]]
    
    # Add sorting
    myout = myout.sort_values(by=["USUBJID", "VISITNUM", "LBDTC"]).reset_index(drop=True)
    

        # Return message if no records with LBDTC per VISITNUM
    if myout.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets, f"LB has {len(myout)} record(s) with Possible LBDTC data entry error.", myout)
  

def check_lb_lbstnrlo_lbstnrhi(data_path):
    check_description = "Check for LB entries with missing reference range when numeric result is present"
    datasets = "LB, DM"
    lb_file_path = os.path.join(data_path, "lb.sas7bdat")
    if  os.path.exists(lb_file_path):
        LB = load_data(data_path, 'lb')
        required_lb_columns = ["USUBJID", "LBTEST", "LBSTRESN", "LBSTNRLO", "LBSTNRHI"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to LB dataset not found at the specified location: {lb_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    dm_file_path = os.path.join(data_path, "dm.sas7bdat")
    if  os.path.exists(dm_file_path):
        DM = load_data(data_path, 'dm')
        required_dm_columns = ["USUBJID", "SITEID"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to DM dataset not found at the specified location: {dm_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    


    # First check that required variables exist and return a message if they don't
    if not set(required_lb_columns).issubset(LB.columns):
        missing = set(required_lb_columns) - set(LB.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in LB: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    if not set(required_dm_columns).issubset(DM.columns):
        missing = set(required_dm_columns) - set(DM.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in DM: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    # Subset LB to only records with missing reference range (missing LBSTNRLO or LBSTNRHI) when numeric result in std unit (LBSTRESN) is not missing
    mydf1 = LB.loc[
        (~LB["LBSTRESN"].apply(is_null_or_empty)) & 
        (LB["LBSTNRLO"].apply(is_null_or_empty) | LB["LBSTNRHI"].apply(is_null_or_empty)),
        ["USUBJID", "LBTEST", "LBSTRESN", "LBSTNRLO", "LBSTNRHI"]
    ]

    if mydf1.empty:
        return pass_check(check_description, datasets)
    else:
        # Merge to get SITEID
        site = DM[["USUBJID", "SITEID"]]
        mydf2 = pd.merge(mydf1, site, on="USUBJID", how="left")

        mydf = (
            mydf2.groupby(["SITEID", "LBTEST"]).size().reset_index(name="Freq")
        )
        mydf = mydf[mydf["Freq"] != 0].sort_values(by=["SITEID", "LBTEST", "Freq"]).reset_index(drop=True)
        return fail_check(check_description, datasets, f"Lab tests with missing reference range in standard units when standard numeric result is not missing: {mydf['LBTEST'].nunique()} LBTEST(s) across {mydf['SITEID'].nunique()} unique SITEID(s).", mydf)
def check_lb_lbstresc_char(data_path):
    check_description = "Check for LB entries where LBSTRESN is missing but LBORRES/LBSTRESC is populated with a number beginning with character > or <"
    datasets = "LB"
    lb_file_path = os.path.join(data_path, "lb.sas7bdat")
    if  os.path.exists(lb_file_path):
        LB = load_data(data_path, 'lb')
        required_columns = ["USUBJID", "LBTEST", "LBDTC", "LBORRES", "LBORRESU", "LBSTRESN", "LBSTRESC"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to LB dataset not found at the specified location: {lb_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    

    # Check if required variables exist in LB
    if not set(required_columns).issubset(LB.columns):
        missing = set(required_columns) - set(LB.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in LB: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Subset data to contain relevant column variables
    vars = ["USUBJID", "LBTEST", "LBDTC", "LBORRES", "LBORRESU", "LBSTRESN", "LBSTRESC"]

    # Subset to LBORRES populated but LBSTRESN not
    mydf = LB.loc[
        (~LB["LBORRES"].apply(is_null_or_empty)) &
        (~LB["LBSTRESC"].apply(is_null_or_empty)) &
        (LB["LBSTRESN"].apply(is_null_or_empty)) &
        (LB["LBSTRESC"].str.contains(r"[><]{1}[0-9]", regex=True)),
        vars
    ]

    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
        return fail_check(check_description, datasets,f"LBSTRESN missing but LBORRES/LBSTRESC populated with number beginning with character > or < for {len(mydf)} record(s).", mydf)
def check_lb_lbstresn_missing(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for LB entries where LBORRES is populated but LBSTRESN and LBSTRESC are missing"
    datasets = "LB"
    lb_file_path = os.path.join(data_path, "lb.sas7bdat")
    if  os.path.exists(lb_file_path):
        LB = load_data(data_path, 'lb')
        required_columns = ["USUBJID", "LBTESTCD", "LBDTC", "LBORRES", "LBORRESU", "LBSTRESN", "LBSTRESC"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to LB dataset not found at the specified location: {lb_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    

    # Check if required variables exist in LB
    if not set(required_columns).issubset(LB.columns):
        missing = set(required_columns) - set(LB.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in LB: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })


    # Apply company specific preprocessing function
    LB = preproc(LB, **kwargs)

    # Subset LB to fewer variables
    vars = ["USUBJID", "LBTESTCD", "LBDTC", "LBORRES", "LBORRESU", "LBSTRESN", "LBSTRESC", "VISIT"]
    LB = LB[vars]

    # Subset to LBORRES populated but LBSTRESN and LBSTRESC not
    mydf = LB.loc[
        (~LB["LBORRES"].apply(is_null_or_empty)) &
        (LB["LBSTRESN"].apply(is_null_or_empty)) &
        (LB["LBSTRESC"].apply(is_null_or_empty))
    ]

    if mydf.empty:
        return pass_check(check_description, datasets)
    else:  
        notes = f"{len(mydf['USUBJID'].unique())} unique patient(s) with {len(mydf)} lab record(s) with result reported without standard value."
        return fail_check(check_description, datasets, notes, mydf)
def check_lb_lbstresu(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for LB entries with missing LBSTRESU and non-missing test results"
    datasets = "LB"
    lb_file_path = os.path.join(data_path, "lb.sas7bdat")
    if  os.path.exists(lb_file_path):
        LB = load_data(data_path, 'lb')
        required_columns = ["USUBJID", "LBSTRESC", "LBSTRESN", "LBSTRESU", "LBORRES", "LBTESTCD", "LBDTC"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to LB dataset not found at the specified location: {lb_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    

    # Check if required variables exist in LB
    if not set(required_columns).issubset(LB.columns):
        missing = set(required_columns) - set(LB.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in LB: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Apply company-specific preprocessing function
    LB = preproc(LB, **kwargs)

    # Exclude records with qualitative results if LBMETHOD exists
    if "LBMETHOD" in LB.columns:
        LB = LB[~LB["LBMETHOD"].str.contains("QUALITATIVE", na=False)]

    # Exclude records marked as not done if LBSTAT exists
    if "LBSTAT" in LB.columns:
        LB = LB[~LB["LBSTAT"].str.contains("NOT DONE", case=False, na=False)]

    # Subset LB to fewer variables
    vars = ['USUBJID', 'LBTESTCD', 'LBORRES', 'LBSTRESU', 'LBSTRESC', 'LBDTC', 'VISIT']
    df = LB[vars]

    # Exclude particular labs known to be unitless
    df = df[~df["LBTESTCD"].isin(["PH", "SPGRAV"]) & 
            ~df["LBORRES"].str.contains("^NEGATIVE$|^POSITIVE$|^NOT DONE$", case=False, regex=True, na=False)]

    # Subset LB to records with missing lab units and non-missing lab test results
    missingunit = df[is_null_or_empty2(df["LBSTRESU"]) & ~is_null_or_empty_numeric(df["LBORRES"])]

    if missingunit.empty:
        return pass_check(check_description, datasets)
    else:
        notes = f"{len(missingunit['USUBJID'].unique())} unique patient(s) with {len(missingunit)} record(s) with missing lab units and non-missing test results."
        return fail_check(check_description, datasets, notes, missingunit)
def check_lb_missing_month(data_path, preproc=lambda df: df, **kwargs):
    check_description = "Check for LB entries with missing month in LBDTC"
    datasets = "LB"
    lb_file_path = os.path.join(data_path, "lb.sas7bdat")
    if  os.path.exists(lb_file_path):
        LB = load_data(data_path, 'lb')
        required_columns = ["USUBJID", "LBTEST", "LBDTC", "VISIT"]
    else:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to LB dataset not found at the specified location: {lb_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    
    

    # Check if required variables exist in LB
    if not set(required_columns).issubset(LB.columns):
        missing = set(required_columns) - set(LB.columns)
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Missing columns in LB: {', '.join(missing)}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })
    

    # Apply company-specific preprocessing function
    LB = preproc(LB, **kwargs)

    # Check if LBDTC has missing month and is in format 'yyyy---dd'
    mydf = LB.loc[LB["LBDTC"].apply(missing_month), ["USUBJID", "LBTEST", "LBDTC", "VISIT"]]
    mydf = mydf.reset_index(drop=True)

    # Return message if there are lab dates with only missing month
    if mydf.empty:
        return pass_check(check_description, datasets)
    else:
     
        notes = f"There are {mydf['USUBJID'].nunique()} patients with a lab date that has year and day present but missing month."
        return fail_check(check_description, datasets, notes, mydf)
def check_dtc_time_format(data_path):
    """
    Check for missing or incorrectly formatted time in '--DTC' columns in the LB dataset.
    """
    check_description = "Time component is missing or incorrectly formatted after 'T' in --DTC columns."
    datasets = "LB"
    lb_file_path = os.path.join(data_path, "lb.sas7bdat")

    # Check if the LB dataset exists
    if not os.path.exists(lb_file_path):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"Check stopped running due to LB dataset not found at the specified location: {lb_file_path}"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Load the LB dataset
    LB = load_data(data_path, 'lb')

    # Find columns ending with '--DTC'
    dtc_columns = [col for col in LB.columns if col.endswith("DTC")]

    if not dtc_columns:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["No --DTC columns found in the LB dataset."],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Initialize a list to store issues
    issues = []

    for col in dtc_columns:
        for index, value in LB[col].dropna().items():
            # Check if the value includes 'T' and is missing time after it
            if 'T' in value:
                time_part = value.split('T')[1] if len(value.split('T')) > 1 else ''
                if not re.match(r"^\d{2}:\d{2}$", time_part):  # Check for the time format HH:MM
                    issues.append({
                        "USUBJID": LB.loc[index, "USUBJID"] if "USUBJID" in LB.columns else None,
                        "LBTEST": LB.loc[index, "LBTEST"] if "LBTEST" in LB.columns else None,
                        "VISIT": LB.loc[index, "VISIT"] if "VISIT" in LB.columns else None,
                        "Column": col,
                        "Value": value,
                        "Issue": "Time component missing or incorrectly formatted after 'T'."
                    })

    # Return a "Pass" message if no issues are found
    if not issues:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets],
            "Data": [pd.DataFrame()]  # Return an empty DataFrame
        })

    # Convert issues to a DataFrame
    issues_df = pd.DataFrame(issues)

    # Return a "Fail" message with the details of the issues
    return fail_check(
        check_description,
        datasets,
        f"There are {len(issues_df)} issues found in '--DTC' columns.",
        issues_df
    )

# Callback function to update plot based on selected parameter
def update_param_plot(selected_param, data_path):
    df = load_data(data_path, 'lb')
    # Filter data for the selected parameter
    filtered_data = df[df["LBTEST"] == selected_param]
    
    # Check if AVAL column exists
    if "LBSTRESN" not in filtered_data.columns:
        return html.Div("No data available for this parameter.")
    
    # Calculate summary statistics
    summary_stats = summary_stats_fig(filtered_data, "LBSTRESN", "AVISITN", "AVISIT")
    summary_stats["LCLM"] = summary_stats["Mean"] - summary_stats["SEM"]
    summary_stats["UCLM"] = summary_stats["Mean"] + summary_stats["SEM"]

    # Define x-axis order based on visit column
    x_order = filtered_data.sort_values(by=["AVISITN"])["AVISIT"].unique()

    # Create line plot with error bars
    fig = go.Figure()
    #for group in filtered_data[treatment_var].unique():
    #group_data = summary_stats[summary_stats[treatment_var] == group]
    fig.add_trace(
            go.Scatter(
                x=group_data["AVISIT"],
                y=group_data["Mean"],
                mode="lines",
                name=group,
                error_y=dict(
                    type="data",
                    array=group_data["SEM"],
                    symmetric=True,
                    color="purple"
                ),
                line=dict(width=2)
            )
        )

    # Update layout of the plot
    fig.update_layout(
        title=f"Mean Plot of {selected_param} by Visit",
        xaxis=dict(title="Visit", categoryorder="array", categoryarray=x_order),
        yaxis=dict(title=selected_param),
        hovermode="x",
        height=500,
        width="100%"
    )

    return dcc.Graph(figure=fig)
# param_plots.py
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

# Summary statistics function
def summary_stats_fig(df, count_var, visit_col_n, visit_col):
    # Aggregate summary statistics
    fig_summary_stats = df.groupby([visit_col_n, visit_col, "LBTEST"], as_index=False).agg(
        N=(count_var, "count"),
        Mean=(count_var, "mean"),
        SEM=(count_var, "sem"),
        SD=(count_var, "std"),
        Min=(count_var, "min"),
        Max=(count_var, "max"),
        Median=(count_var, "median")
    )
    return fig_summary_stats

# Generate plots for each LBTEST
def generate_lbtest_plot(lb_df, lbtest_value):
    # Filter data for the selected LBTEST value and drop rows with NaN in LBSTRESN
    filtered_data = lb_df[lb_df["LBTEST"] == lbtest_value].dropna(subset=["LBSTRESN"])

    # Ensure necessary columns exist
    if "LBTEST" not in filtered_data.columns or "LBSTRESN" not in filtered_data.columns:
        return html.Div("Required columns 'LBTEST' or 'LBSTRESN' not found in data.")

    # Calculate summary statistics
    summary_stats = summary_stats_fig(filtered_data, "LBSTRESN", "VISITNUM", "VISIT")
    summary_stats["LCLM"] = summary_stats["Mean"] - summary_stats["SEM"]
    summary_stats["UCLM"] = summary_stats["Mean"] + summary_stats["SEM"]

    # Define x-axis order based on visit column
    x_order = filtered_data.sort_values(by=["VISITNUM"])["VISIT"].unique()

    # Create line plot with error bars
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=summary_stats["VISIT"],
            y=summary_stats["Mean"],
            mode="lines",
            name=lbtest_value,
            error_y=dict(
                type="data",
                array=summary_stats["SEM"],
                symmetric=True,
                color="purple"
            ),
            line=dict(width=2)
        )
    )

    # Update layout of the plot
    fig.update_layout(
        title=f"Mean Plot of {lbtest_value} by Visit",
        xaxis=dict(title="Visit", categoryorder="array", categoryarray=x_order),
        yaxis=dict(title=lbtest_value),
        hovermode="x",
        height=500,
        width=1200  # Specify a numeric width in pixels
    )

    return dcc.Graph(figure=fig)


