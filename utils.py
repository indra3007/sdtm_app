# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 12:38:07 2024

@author: inarisetty
"""
import pyreadstat
import pandas as pd
import re
from datetime import datetime
import os
def load_data(data_path,file_name):
    file_path = f"{data_path}/{file_name}.sas7bdat"
    if os.path.exists(file_path):
        df, meta = pyreadstat.read_sas7bdat(file_path, encoding="LATIN1")
    else:
        return pd.DataFrame()  # Return an empty DataFrame if the file doesn't exist
    return df


def is_null_or_empty(val):
    return pd.isna(val) or val == '' or val is None

def is_null_or_empty2(series):
    return series.isna() | (series == '') | series.isnull()

    
# =============================================================================
# def missing_month(date_series):
#     return date_series.str.match(r'^\d{4}---\d{2}$')
# =============================================================================
def missing_month(date_str):
    return isinstance(date_str, str) and bool(re.match(r'^\d{4}---\d{2}$', date_str))
def is_null_or_empty_numeric(series):
    return series.isna() | (series == '') 

def fail_check(check_description, datasets, msg, data=None):
    # Initialize a new DataFrame if no data is passed
    if data is None or data.empty:
        data = pd.DataFrame()

    # Add values to the DataFrame
    data["CHECK"] = check_description
    data["Message"] = "Fail"
    data["Notes"] = msg
    data["Datasets"] = datasets

    # Ensure the specified columns appear first
    primary_columns = ["CHECK", "Message", "Notes", "Datasets"]
    remaining_columns = [col for col in data.columns if col not in primary_columns]
    data = data[primary_columns + remaining_columns]

    return data

# def fail_check(check_description,datasets,msg, data=pd.DataFrame()):
#         #data = data.reset_index(drop=True)
#         message = "Fail"
#         notes = msg
#         data.insert(0, "CHECK", check_description)
#         data.insert(1, "Message", message)
#         data.insert(2, "Notes", notes)
#         data.insert(3, "Datasets", datasets)
#         return data


# =============================================================================
# def fail_check(check_description, datasets, message, data=pd.DataFrame()):
#     #data = data.reset_index(drop=True)
#     data.insert(0, "CHECK", check_description)
#     data.insert(1, "Message", "Fail")
#     data.insert(2, "Notes", message)
#     data.insert(3, "Datasets", datasets)
#     return data[["CHECK", "Message", "Notes", "Datasets", "Data"]]
# =============================================================================
    # Helper function for generating pass message
def pass_check(check_description,datasets):
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": ["Pass"],
            "Notes": [""],
            "Datasets": [datasets]
            
        })
def lacks_any(df, required_columns):
    return [col for col in required_columns if col not in df.columns]

def lacks_all(df, required_columns):
    return all(col not in df.columns for col in required_columns)


def impute_day01(date_series):
    return pd.to_datetime(date_series, errors='coerce').fillna(pd.to_datetime(date_series.str[:7] + '-01', errors='coerce')).fillna(pd.to_datetime(date_series.str[:4] + '-01-01', errors='coerce'))

# =============================================================================
# def impute_day01(date_series):
#     def impute_date(date):
#         if pd.isna(date):
#             return pd.NaT
#         try:
#             return pd.to_datetime(date, errors='coerce')
#         except:
#             pass
#         
#         try:
#             return pd.to_datetime(date[:7] + '-01', errors='coerce')
#         except:
#             pass
#         
#         try:
#             return pd.to_datetime(date[:4] + '-01-01', errors='coerce')
#         except:
#             return pd.NaT
#     
#     return date_series.apply(impute_date)
# =============================================================================
# =============================================================================
# def miss_col(check_description, required_columns, domain, datasets):
#     if not set(required_columns).issubset(domain.columns):
#         missing = set(required_columns) - set(domain.columns)
#         return pd.DataFrame({
#             "CHECK": [check_description],
#             "Message": [f"Missing columns in {domain}: {', '.join(missing)}"],
#             "Notes": [""],
#             "Datasets": [datasets],
#             "Data": [pd.DataFrame()]  # Return an empty DataFrame
#         })
# =============================================================================
def miss_col(check_description, required_columns, domain, domain_name, datasets):
    missing = lacks_any(domain, required_columns)
    if missing:
        return fail_check(check_description, datasets, f"Missing columns in {domain_name}: {', '.join(missing)}")
    return None

def dtc_dupl_early(df, vars, groupby, dtc):
        df = df.sort_values(by=[vars[0], vars[1], vars[2], vars[3]])
        df['visit_order'] = df.groupby(groupby).cumcount() + 1
        df['dtc_order'] = df.groupby(groupby)[dtc].rank(method='dense')
        df['check_flag'] = df.apply(lambda x: 'Duplicated' if x['visit_order'] != x['dtc_order'] else None, axis=1)
        return df
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
def convert_date(df, column):
    """
    Convert and format the SVSTDTC column in the given DataFrame.
    
    Parameters:
    df (pd.DataFrame): The input DataFrame containing the SVSTDTC column.
    column (str): The name of the column to process. Default is "SVSTDTC".
    
    Returns:
    pd.DataFrame: The DataFrame with the processed SVSTDTC column.
    """
    
    # Convert column to datetime, coercing errors to NaT
    df[column] = df[column].apply(preprocess_dates)
    #df[column] = pd.to_datetime(df[column], errors='coerce')
    
    # Ensure all dates are in the correct format
    df[column] =  df[column].apply(lambda x: pd.to_datetime(x, errors='coerce') if isinstance(x, str) and len(x) == 10 else x)
    df[column] = df[column].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, pd.Timestamp) else x)
 
    
    return df
def format_dates(date):
    if isinstance(date, pd.Timestamp):
        if date.time() != datetime.min.time():
            return date.strftime('%Y-%m-%dT%H:%M' if date.second == 0 else '%Y-%m-%dT%H:%M:%S')
        else:
            return date.strftime('%Y-%m-%d')
    return date
def check_empty_dataset(df, data, dataset_name, check_description):
    if df.empty:
        return pd.DataFrame({
            "CHECK": [check_description],
            "Message": [f"No records in {data} dataset."],
            "Datasets": [dataset_name]
        })
    return None  # Return None if the dataset is not empty
