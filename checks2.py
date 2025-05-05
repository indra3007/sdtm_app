# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pyreadstat
import pandas as pd 
#import dtale
from datetime import datetime
import os
from utils import load_data,is_null_or_empty
import re 
import plotly.graph_objects as go
import pytz
from openpyxl import load_workbook
import re
from sqlalchemy import text
from sqlalchemy import create_engine
from urllib.parse import quote_plus 
from connection import get_engine  
import glob
def drop_quality_checks_table():
    """
    Drops the 'Quality_checks_combined' table if it exists in the database.
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            # Begin a transaction
            trans = connection.begin()
            try:
                # Drop the table if it exists
                drop_table_query = text("DROP TABLE IF EXISTS dbo.Quality_checks_combined")
                connection.execute(drop_table_query)
                print("Table 'Quality_checks_combined' dropped successfully!")
                # Commit the transaction
                trans.commit()
            except Exception as e:
                # Rollback the transaction in case of an error
                trans.rollback()
                print(f"Error dropping table 'Quality_checks_combined': {e}")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
#delete the SQL table if exists.
drop_quality_checks_table()  
# Get the SQLAlchemy engine
engine = get_engine()

# Define the query
query = "SELECT * FROM MACRO.dbo.specstor_spec WHERE spec_type LIKE '%SDTM%'"

# Execute the query and fetch results using Pandas
try:
    with engine.connect() as connection:
        df_db = pd.read_sql(query, connection)  # Execute the query and load the result into a DataFrame
        print("Query executed successfully!")
        print(df_db.head())  # Print the first few rows of the DataFrame

    # Save the results to an Excel file
    output_excel_path = "df_db_output.xlsx"  # Specify the output file path
    df_db.to_excel(output_excel_path, index=False, engine='openpyxl')
    print(f"Data saved to {output_excel_path}")
except Exception as e:
    print(f"Failed to execute query or save data: {e}")

# Dispose of the SQLAlchemy engine
engine.dispose()
from dm_checks import *
from ae_checks import *
from ce_checks import *
from cm_checks import *
from dd_checks import *
from ds_checks import *
from dv_checks import *
from eg_checks import *
from ex_checks import *
from lb_checks import * 
from mh_checks import *
from mi_checks import *
from pr_checks import *
from qs_checks import *
from rs_checks import *
from sc_checks import *
from ss_checks import *
from tr_checks import *
from ts_checks import *
from tu_checks import *
from vs_checks import *#
from sv_checks import *
from cdisc_gil_req_vars import(req_vars)
from dates_all_chk import process_datasets
#from mean_plot import(generate_test_plot)
local_tz = pytz.timezone('America/New_York')
df_db['study'] = df_db['path'].str.extract(r'/projects/(p\d+)')
df_db['project'] = df_db['path'].str.extract(r'/projects/p\d+/(s\d+)')
df_db['source'] = df_db['path'].str.extract(r'/docs/(\w+)/')
df_db['sdtm_data'] = df_db['path'].str.rsplit('/', n=3).str[0] + '/sdtmdata'
df_db = df_db.drop_duplicates(subset=['study', 'project', 'source', 'analysis_task', 'analysis_version', 'protocol'])
#subset_df = df_db[
    #(df_db['project'].str.contains("s6216463", case=False, na=False)) &
    #(df_db['analysis_task'].str.contains("csdtm_dev", case=False, na=False))
#]
df_db.to_excel("test_studies.xlsx", index=False, engine='openpyxl')
subset_df = df_db[
	df_db['study'].notna() &
    df_db['study'].str.contains("p627|p624|p592", case=False, na=False) 
    #df_db['project'].str.contains("s21", case=False, na=False)
    #(df_db['analysis_task'].str.contains("csdtm_dev", case=False, na=False))
]
output_excel_path = "df_db_output.xlsx"  # Specify the output file path
subset_df.to_excel(output_excel_path, index=False, engine='openpyxl')
#project = "p621"
#study = "s6216463"
#data_path = f"G:/projects/{project}/{study}/csdtm_dev/draft1/sdtmdata" #use specstor_spec
#raw_data_path = data_path.replace("sdtmdata", "rawdata")
 
# Load the dataframe]
# Run the check function
#result = check_ae_aeacn_ds_disctx_covid()
def generate_quality_checks_path(summary_df):
    """
    Generate the quality checks path based on the Data_Path column in the summary DataFrame.
    """
    if not summary_df.empty and "Data_Path" in summary_df.columns:
        original_path = summary_df.iloc[0]["Data_Path"]
        if "biometrics" in original_path.lower():
            original_path = original_path.lower().replace("biometrics", "/biometrics")
        else:
            original_path = f"/{original_path.lstrip('/')}"  # Ensure it starts with "/"
        
        two_steps_back = os.path.normpath(os.path.join(original_path, "../"))
        # Append the new path structure
        new_path = os.path.join(
            two_steps_back,
            "docs/sdtm"
        )
        # Replace backslashes with forward slashes and ensure it starts with "/"
        new_path = new_path.replace("\\", "/")
        if not new_path.startswith("/"):
            new_path = f"/{new_path}"  # Ensure it starts with "/"
        return new_path
    else:
        raise ValueError("The summary DataFrame is empty or does not contain the 'Data_Path' column.")
def process_directory(row):
    """
    Process a single directory for quality checks.
    """
    try:
        data_path = row['sdtm_data']
        project = row['project']
        protocol = row['study']
        source = row['source']
        analysis_task = row['analysis_task']
        analysis_version = row['analysis_version']
        raw_data_path = data_path.replace("sdtmdata", "rawdata")

        print(f"Processing directory: {data_path}")

        # Run the checks for the current data_path
        results = [
            check_dm_actarm_arm(data_path),
            check_dm_ae_ds_death(data_path),
            check_dm_age_missing(data_path),
            check_dm_armnrs_missing(data_path),
            check_dm_armcd(data_path),
            check_dm_arm_scrnfl(data_path),
            check_dm_ds_icdtc(data_path),
            check_dm_rficdtc(data_path),
            check_dm_usubjid_ae_usubjid(data_path),
            check_dm_usubjid_dup(data_path),
            check_dm_dthfl_dthdtc(data_path),
            check_ae_aeacn_ds_disctx_covid(data_path),
            check_ae_aeacnoth(data_path),
            check_ae_aeacnoth_ds_disctx(data_path),
            check_ae_aeacnoth_ds_stddisc_covid(data_path),
            check_ae_aedecod(data_path),
            check_ae_aedthdtc_aesdth(data_path),
            check_ae_aedthdtc_ds_death(data_path),
            check_ae_aeout(data_path),
            check_ae_aeout_aeendtc_aedthdtc(data_path),
            check_ae_aeout_aeendtc_nonfatal(data_path),
            check_ae_aerel(data_path),
            check_ae_aesdth_aedthdtc(data_path),
            check_ae_aestdtc_after_aeendtc(data_path),
            check_ae_aestdtc_after_dd(data_path),
            check_ae_aetoxgr(data_path),
            check_ae_death(data_path),
            check_ae_ds_partial_death_dates(data_path),
            check_ae_dup(data_path),
            check_ae_fatal(data_path),
            check_ae_withdr_ds_discon(data_path),
            check_ce_missing_month(data_path),
            check_cm_cmdecod(data_path),
            check_cm_cmlat(data_path),
            check_cm_missing_month(data_path),
            check_dd_ae_aedthdtc_ds_dsstdtc(data_path),
            check_dd_ae_aeout_aedthdtc(data_path),
            check_dd_death_date(data_path),
            check_ds_ae_discon(data_path),
            check_ds_dsdecod_death(data_path),
            check_ds_dsdecod_dsstdtc(data_path),
            check_ds_dsscat(data_path),
            check_ds_dsterm_death_due_to(data_path),
            check_ds_duplicate_randomization(data_path),
            check_ds_ex_after_discon(data_path),
            check_ds_multdeath_dsstdtc(data_path),
            check_ds_sc_strat(data_path),
            check_dv_ae_aedecod_covid(data_path),
            check_dv_covid(data_path),
            check_eg_egdtc_visit_ordinal_error(data_path),
            check_ex_dup(data_path),
            check_ex_exdose_exoccur(data_path),
            check_ex_exdose_pos_exoccur_no(data_path),
            check_ex_exdosu(data_path),
            check_ex_exoccur_mis_exdose_nonmis(data_path),
            check_ex_exstdtc_after_dd(data_path),
            check_ex_exstdtc_visit_ordinal_error(data_path),
            check_ex_extrt_exoccur(data_path),
            check_ex_infusion_exstdtc_exendtc(data_path),
            check_ex_visit(data_path),
            check_lb_lbdtc_after_dd(data_path),
            check_lb_lbdtc_visit_ordinal_error(data_path),
            check_lb_lbstnrlo_lbstnrhi(data_path),
            check_lb_lbstresc_char(data_path),
            check_lb_lbstresn_missing(data_path),
            check_lb_lbstresu(data_path),
            check_lb_missing_month(data_path),
            check_mh_missing_month(data_path),
            check_mi_mispec(data_path),
            check_pr_missing_month(data_path),
            check_qs_dup(data_path),
            check_qs_qsdtc_after_dd(data_path),
            check_qs_qsdtc_visit_ordinal_error(data_path),
            check_qs_qsstat_qsreasnd(data_path),
            check_qs_qsstat_qsstresc(data_path),
            check_rs_rscat_rsscat(data_path),
            check_rs_rsdtc_across_visit(data_path),
            check_rs_rsdtc_visit(data_path),
            check_sc_dm_eligcrit(data_path),
            check_ss_ssdtc_alive_dm(data_path),
            check_ss_ssdtc_dead_ds(data_path),
            check_ss_ssdtc_dead_dthdtc(data_path),
            check_ss_ssstat_ssorres(data_path),
            check_tr_dup(data_path),
            check_tr_trdtc_across_visit(data_path),
            check_tr_trdtc_visit_ordinal_error(data_path),
            check_tr_trstresn_ldiam(data_path),
            check_ts_aedict(data_path),
            check_ts_cmdict(data_path),
            check_ts_sstdtc_ds_consent(data_path),
            check_tu_rs_new_lesions(data_path),
            check_tu_tudtc(data_path),
            check_tu_tudtc_across_visit(data_path),
            check_tu_tudtc_visit_ordinal_error(data_path),
            check_tu_tuloc_missing(data_path),
            check_vs_height(data_path),
            check_vs_sbp_lt_dbp(data_path),
            check_vs_vsdtc_after_dd(data_path),
            check_sv_svstdtc_visit_ordinal_error(data_path),
            check_sv_dupc_visit(data_path)
        ]

        # Combine all results into a single DataFrame
        combined_results = pd.concat(results, ignore_index=True)
        unique_datasets = set()

        # Extract unique datasets
        for datasets in combined_results["Datasets"]:
            if isinstance(datasets, str):  # Ensure the value is a string
                for dataset in datasets.split(", "):
                    unique_datasets.add(dataset.upper())

        # Check if you have permission to access the directory
        if os.access(data_path, os.R_OK):
            all_files = [os.path.join(data_path, f) for f in os.listdir(data_path) if f.endswith('.sas7bdat') and not f.lower().startswith('supp')]
            file_datasets = set([os.path.splitext(os.path.basename(f))[0].upper() for f in all_files])

            # Initialize a variable to store the maximum modified date
            max_modified_date = None

            # Iterate through each file and get the last modified date
            for file_path in all_files:
                try:
                    modified_time_utc = datetime.utcfromtimestamp(os.path.getmtime(file_path))  # Get UTC time
                    modified_time_local = pytz.utc.localize(modified_time_utc).astimezone(local_tz)  # Convert to local time
                    if max_modified_date is None or modified_time_local > max_modified_date:
                        max_modified_date = modified_time_local
                except Exception as e:
                    print(f"Error getting modified time for file {file_path}: {e}")

            # Format the maximum modified date
            max_modified_date_str = max_modified_date.strftime('%Y-%m-%d') if max_modified_date else None

            # Find files in data_path that are not in combined_results
            missing_files = list(file_datasets - unique_datasets)

            # Create summary and detailed data
            summary_data = []
            detailed_data = []
            req_vars_chk = req_vars(data_path)[["CHECK", "Message", "Notes", "Datasets"]].to_dict('records')

            # Add "Pass" for all required variables checks
            pass_datasets = [row["Datasets"] for row in req_vars_chk if row["Message"] == "Pass"]
            if pass_datasets:
                summary_data.append(["All required variables present", "Pass", "", ", ".join(pass_datasets), ""])

            # Add "Fail" records for required variable checks
            for row in req_vars_chk:
                if row["Message"] == "Fail":
                    summary_data.append([row["CHECK"], row["Message"], row["Notes"], row["Datasets"], ""])

            # Handle missing datasets information
            missing_files_notes = f'Checks not performed for datasets: {", ".join(missing_files)}'
            summary_data.append(["Checks not performed", "Fail", missing_files_notes, "", ""])

            # Populate summary and detailed sheets
            for i, result in enumerate(results):
                if result.empty:
                    continue  # Skip empty results

                check_name = result["CHECK"].iloc[0]
                status = str(result["Message"].iloc[0])  # Convert to string to handle non-iterable types
                notes = result["Notes"].iloc[0] if 'Notes' in result.columns else ""
                datasets = result["Datasets"].iloc[0] if 'Datasets' in result.columns else ""

                if "Fail" in status:
                    sheet_name = f'Sheet{i+1}'  # Create dynamic sheet name
                    detailed_data.append((sheet_name, result))
                    summary_data.append([check_name, status, notes, datasets, sheet_name])
                else:
                    summary_data.append([check_name, status, notes, datasets, ""])

            # Convert summary to DataFrame and filter unwanted entries
            summary_df = pd.DataFrame(summary_data, columns=["CHECK", "Message", "Notes", "Datasets", "Data"])
            summary_df = summary_df[~summary_df["Message"].str.contains("dataset not found at the specified location", na=False, case=False)]
            summary_df["Data_Path"] = data_path
            summary_df["Project"] = project
            summary_df["Protocol"] = protocol
            summary_df["Source"] = source
            summary_df["Analysis_Task"] = analysis_task
            summary_df["Analysis_Version"] = analysis_version
            summary_df["Max_Modified_Date"] = max_modified_date_str
            quality_checks_path = generate_quality_checks_path(summary_df)
            # Write summary sheet
            if "csdtm_dev" in analysis_task:
                summary_df["More information"] = summary_df["Source"] + f" Quality_checks_{project}_{analysis_task}_{analysis_version}.xlsx"
                writer = pd.ExcelWriter(f"{quality_checks_path}/Quality_checks_{project}_{analysis_task}_{analysis_version}.xlsx", engine='xlsxwriter')
                workbook = writer.book
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            else:
                summary_df["More information"] = None

            # Write to SQL database
            try:
                engine = get_engine()
                summary_df_sql = summary_df.drop(columns=["Data"])  # Drop unnecessary column
                summary_df_sql.to_sql(
                    name="Quality_checks_combined",
                    con=engine,
                    if_exists="append",
                    index=False
                )
                print(f"Data for {data_path} successfully appended to the SQL database.")
            except Exception as e:
                print(f"Error writing to SQL database for {data_path}: {e}")
            finally:
                engine.dispose()
            # Write to Excel
            if "csdtm_dev" in analysis_task:
                
                print(f"Quality checks path: {quality_checks_path}")

                # Ensure the directory exists
                if not os.path.exists(quality_checks_path):
                    #os.makedirs(quality_checks_path)  # Create the directory if it doesn't exist
                    print(f"Created directory: {quality_checks_path}")

                # Save the Excel file

                summary_df = summary_df.drop(columns=["Data_Path", "Protocol", "Project", "Source", "Analysis_Task", "Analysis_Version", "Max_Modified_Date", "More information"])
                
                dates_df, all_dates = process_datasets(raw_data_path, aggregation='max', remove_time=True, all_dates=True)
                dates_df.to_excel(writer, sheet_name='all_dates', index=False)

                # Write detailed sheets for failed checks
                sheet_counter = 1
                sheet_names = {}
                for data, df in detailed_data:
                    sheet_name = f'Sheet{sheet_counter}'
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    sheet_names[data] = sheet_name
                    sheet_counter += 1

                # Add hyperlinks in the summary sheet
                worksheet = writer.sheets['Summary']
                for i, (check_name, status, notes, datasets, data) in enumerate(summary_df.values):
                    if "Fail" in status and data:
                        sheet_name = sheet_names.get(data)
                        if sheet_name:
                            worksheet.write_url(i + 1, 4, f'internal:{sheet_name}!A1', string=sheet_name)

                writer.close()
                print(f"Excel file saved to: {quality_checks_path}/Quality_checks_{project}_{analysis_task}_{analysis_version}.xlsx")
            print(f"Processing completed for {data_path}")
            # After writing the Excel file, check for the P21 Report directory and process the latest Pinnacle 21 report
            p21_report_dir = None
            if not quality_checks_path.endswith("/"):
                quality_checks_path += "/"
            # Look for the "P21 Report" directory (case-insensitive)
            for root, dirs, files in os.walk(quality_checks_path):
                print(f"Checking in directory: {root}")  # Debugging: Print the current directory being checked
                for dir_name in dirs:
                    print(f"Found directory: {dir_name}")  # Debugging: Print the directories found
                    if dir_name.lower() == "p21 report":
                        p21_report_dir = os.path.join(root, dir_name)
                        break
                if p21_report_dir:
                    break

# Find the latest Pinnacle 21 report file
            report_files = glob.glob(os.path.join(p21_report_dir, "pinnacle21-report-*.xlsx"))
            if report_files:
                # Sort files by modification time and pick the latest one
                latest_report = max(report_files, key=os.path.getmtime)
                print(f"Latest Pinnacle 21 report: {latest_report}")

                # Read the latest report into a DataFrame
                try:
                    # Read the 'Issue Summary' sheet starting from row 4
                    p21_df = pd.read_excel(latest_report, sheet_name="Issue Summary", skiprows=3, engine='openpyxl')
                    print(f"Pinnacle 21 report loaded successfully with {len(p21_df)} rows.")
                    p21_df['Source'] = p21_df['Source'].fillna(method='ffill')
                    # Add metadata columns to the DataFrame
                    p21_df["Data_Path"] = data_path
                    p21_df["Project"] = project
                    p21_df["Protocol"] = protocol
                    p21_df["Source_Type"] = source
                    p21_df["Analysis_Task"] = analysis_task
                    p21_df["Analysis_Version"] = analysis_version

                    # Write the DataFrame to the SQL database
                    try:
                        engine = get_engine()
                        p21_df.to_sql(
                            name="Combined P21 checks",
                            con=engine,
                            if_exists="append",
                            index=False
                        )
                        print("Pinnacle 21 report successfully written to the SQL database under 'Combined P21 checks'.")
                    except Exception as e:
                        print(f"Error writing Pinnacle 21 report to the SQL database: {e}")
                    finally:
                        engine.dispose()
                except Exception as e:
                    print(f"Error reading Pinnacle 21 report: {e}")
            else:
                print("No Pinnacle 21 report files found in the P21 Report directory.")
    except Exception as e:
        print(f"Error processing directory '{data_path}': {e}")

# Process each directory in the subset DataFrame
for _, row in subset_df.iterrows():
    process_directory(row)