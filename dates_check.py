# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 15:12:34 2024

@author: inarisetty
"""
import pyreadstat
import pandas as pd 

import dtale
from openpyxl import load_workbook
import os

from datetime import datetime
excel_file = "G:/users/inarisetty/private/python/combined_data.xlsx"
sas_directory = "G:/projects/p624/s624637603/csdtm_dev/draft1/rawdata/"
workbook = load_workbook(excel_file)
sheet_name = 'Sheet1'
sheet = workbook[sheet_name]
data = sheet.values
columns = next(data)[0:]
df_xl = pd.DataFrame(data, columns=columns)
df_xl = df_xl[(df_xl['Dataset'] == 'DM') & (df_xl['Variable'] == 'RFPENDTC')]

df_xl = df_xl.loc[:, ['Dataset','Variable', 'Input Variables','Mapping Action','Implemented SAS Code']]

print(df_xl)
dataframes = []

# Function to filter the required columns from a dataframe
def filter_columns(df, dataset_name, date_vars):
    # Extract the date variables and ensure SUBJID and data_page_name (if exists) are included
    columns_to_keep = ['SUBJID'] + date_vars
    if 'DATAPAGENAME' in df.columns:
        columns_to_keep.append('DATAPAGENAME')
    else:
        df['DATAPAGENAME'] = dataset_name
        columns_to_keep.append('DATAPAGENAME')
    df_filtered = df[columns_to_keep]

    # Add the dataset column with the dataset name
    df_filtered['dataset'] = dataset_name

    return df_filtered

# Function to preprocess the Dates column
def preprocess_dates(date):
    if isinstance(date, str):
        # Handle the case where date contains 'T'
        if 'T' in date:
            date = date.split('T')[0]
        
        # Handle the 'UN UNK 2023' format
        if 'UN UNK' in date:
            return date.split()[-1]
        
        # Handle the 'UN DEC 2023' format
        if date.startswith('UN'):
            parts = date.split()
            if len(parts) == 3:
                year = parts[-1]
                month = parts[1]
                return f"{year}-{datetime.strptime(month, '%b').month:02d}"
        if len(date) == 9:
            date = f"{date[:2]} {date[2:5]} {date[5:]}"
        # Handle partial dates like '2023-11'
        if len(date.split('-')) == 2:
            return date

        # Handle the '20 FEB 2024' format
        try:
            return datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
        except ValueError:
            pass

    return date
date_vars_dict = {}

for input_var in df_xl['Input Variables']:
    vairables = input_var.split(',')
    print(vairables)
    for var in vairables:
        parts = var.strip().split('.')
        #print(parts)
        #print(len(parts))
        if len(parts) == 3:
            dataset_name = parts[1]
            date_var = parts[2].upper()
            print(dataset_name)
            if dataset_name not in date_vars_dict:
                
                date_vars_dict[dataset_name] = []
            date_vars_dict[dataset_name].append(date_var)

# Iterate through each dataset and its date variables
for dataset_name, date_vars in date_vars_dict.items():
    
    print(date_vars)
    dataset_file = os.path.join(sas_directory, dataset_name + ".sas7bdat")
    if not os.path.exists(dataset_file):
        print(f"Dataset file {dataset_file} does not exist. Skipping.")
        continue

    # Read the SAS dataset
    df, meta = pyreadstat.read_sas7bdat(dataset_file)

    # Filter the columns and add the dataset column
    filtered_df = filter_columns(df, dataset_name, date_vars)

    # Preprocess the Dates columns
    for date_var in date_vars:
        if date_var in filtered_df.columns:
            filtered_df[date_var] = filtered_df[date_var].apply(preprocess_dates)

    # Unpivot the date columns
    df_unpivoted = filtered_df.melt(id_vars=['SUBJID', 'dataset', 'DATAPAGENAME'],
                                    value_vars=date_vars, var_name='Date_Type', value_name='Dates')

    # Add the filtered and unpivoted dataframe to the list
    dataframes.append(df_unpivoted)

# Concatenate all filtered dataframes
final_df = pd.concat(dataframes, ignore_index=True)

# Subset the dataframe to include only rows where SUBJID is "1234"
#final_df_subset = final_df[final_df['SUBJID'] == "1234"]
final_df_subset = final_df.copy()
# Remove duplicates based on SUBJID and Dates
final_df_subset = final_df_subset.drop_duplicates(subset=['SUBJID', 'Dates'])

# Apply pd.to_datetime only on dates with length 10 (YYYY-MM-DD)
final_df_subset['Dates'] = final_df_subset['Dates'].apply(lambda x: pd.to_datetime(x, errors='coerce') if isinstance(x, str) and len(x) == 10 else x)

# Ensure all dates are in the correct format
final_df_subset['Dates'] = final_df_subset['Dates'].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, pd.Timestamp) else x)
final_df_subset['Dates_bf']  = final_df_subset['Dates'] 
# Sort the dataframe by SUBJID and descending Dates
final_df_subset = final_df_subset.sort_values(by=['SUBJID', 'Dates'], ascending=[True, False])




# Group by SUBJID and get the maximum date
max_dates_df = final_df_subset.groupby('SUBJID', as_index=False).agg({'Dates': 'max'})

# Save the final subset dataframe with max dates to an Excel file
max_dates_df.to_excel('final_max_dates.xlsx', index=False)
