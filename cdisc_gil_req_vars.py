
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 12:33:12 2024

@author: inarisetty
"""

import os
import pandas as pd
import pyreadstat

# Set the directory path containing the datasets and the path to the Excel file

def req_vars(datasets_path):
    excel_file_sdtm = f"G:/users/inarisetty/private/sdtm_checks_311/combined_data_reqvars.xlsx"
    document_path = f'{excel_file_sdtm}' # replace with the path to your Excel file


    # Read the Excel file
    excel_meta = pd.read_excel(document_path)
    excel_meta.loc[excel_meta["Dataset"] == "QNAM", "Dataset"] = "SUPP" + excel_meta["Sheet"]
    excel_meta.to_excel('test.xlsx', index=False)
    # Create a list to store the results
    df_results = []

    # Iterate through each unique dataset in the Excel metadata
    for dataset_name in excel_meta['Dataset'].unique():
        dataset_file_path = next((os.path.join(datasets_path, file) for file in os.listdir(datasets_path) if file.lower() == f'{dataset_name.lower()}.sas7bdat'), None)
        
        # Check if the dataset file exists
        if dataset_file_path and os.path.exists(dataset_file_path):
            # Read the dataset with metadata
            data, meta = pyreadstat.read_sas7bdat(dataset_file_path)
            #print(meta.column_names)
            # Get the list of required variables for this dataset from the Excel file
            required_vars = excel_meta.loc[excel_meta['Dataset'] == dataset_name, 'Variable'].tolist()
            
            # Find missing variables
            #missing_vars = [var for var in required_vars if var not in meta.column_names]
            
            # Store the results
            if "supp" in dataset_name.lower():
                # Get unique QNAM values in the dataset
                unique_qnam = data["QNAM"].unique().tolist() if "QNAM" in data.columns else []

                # Check if each required variable exists in unique QNAM values
                missing_vars = [var for var in required_vars if var not in unique_qnam]

                if missing_vars:
                    df_results.append({"Datasets": dataset_name, "CHECK": "SUPP QNAM check", "Notes": "Missing QNAM Variables","Message": "Fail", "Notes": ', '.join(missing_vars)})
                else:
                    df_results.append({"Datasets": dataset_name, "CHECK": "SUPP QNAM check", "Notes": "", "Message": "Pass"})
            else:
                # Standard variable check
                missing_vars = [var for var in required_vars if var not in meta.column_names]

                if missing_vars:
                    df_results.append({"Datasets": dataset_name, "CHECK": "All required variables present", "Notes": "Missing Variables","Message": "Fail", "Notes": ', '.join(missing_vars)})
                else:
                    df_results.append({"Datasets": dataset_name, "CHECK": "All required variables present", "Notes": "", "Message": "Pass"})



    # Convert the results to a DataFrame
    results_df = pd.DataFrame(df_results)
    
    return results_df
