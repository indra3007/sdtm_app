import os
import pandas as pd
import pyreadstat
from datetime import datetime, date as dt_date
import numpy as np
# Function to filter the required columns from a dataframe
def filter_columns(df, dataset_name, date_vars, time_vars):
    # Check if X_SUBJID exists, if not, create it from USUBJID
    if 'X_SUBJID' not in df.columns:
        if 'USUBJID' in df.columns:
            df['X_SUBJID'] = df['USUBJID']
        else:
            raise ValueError(f"Neither X_SUBJID nor USUBJID found in dataset {dataset_name}.")

    # Extract the date and time variables and ensure X_SUBJID and DATAPAGENAME (if exists) are included
    columns_to_keep = ['X_SUBJID'] + date_vars + list(time_vars)
    if 'DATAPAGENAME' in df.columns:
        columns_to_keep.append('DATAPAGENAME')
    else:
        df['DATAPAGENAME'] = dataset_name
        columns_to_keep.append('DATAPAGENAME')
    if "FOLDERNAME" in df.columns:
        columns_to_keep.append('FOLDERNAME')
    else:
            df['FOLDERNAME'] = "No Folder name"
            columns_to_keep.append('FOLDERNAME')
    df_filtered = df[columns_to_keep]

    # Add the dataset column with the dataset name
    df_filtered['dataset'] = dataset_name

    return df_filtered


# Function to preprocess the Dates column
def preprocess_dates(date):
    time_part = ''
    
    # Separate the time part if 'T' is in the date
    if isinstance(date, str) and 'T' in date:
        date, time_part = date.split('T')
    
    # Handle NaN values (skip processing if the date is NaN)
    if pd.isna(date):
        return np.nan
    
    # If the date is numeric, convert it to a string
    if isinstance(date, (int, float)):
        date = str(int(date))
    
    if isinstance(date, str):
        # Attempt to handle '24JAN2024' or '19OCT2023' format
        try:
            date = datetime.strptime(date, '%d%b%Y').strftime('%Y-%m-%d')
            return date + ('T' + time_part if time_part else '')
        except ValueError:
            pass

        # Attempt to handle '04 JAN 2024' or '19 OCT 2023' format
        try:
            date = datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
            return date + ('T' + time_part if time_part else '')
        except ValueError:
            pass
        
        # Handle partial dates like '2023-11'
        if len(date.split('-')) == 2:
            return date + ('T' + time_part if time_part else '')

        # Handle the '2024-01-04' format
        try:
            date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
            return date + ('T' + time_part if time_part else '')
        except ValueError:
            pass
        
        # Handle the 'UN UNK 2023' format
        if 'UN UNK' in date:
            return date.split()[-1]

        # Handle the 'UN DEC 2023' format
        if date.startswith('UN'):
            parts = date.split()
            if len(parts) == 3:
                year = parts[-1]
                month = parts[1]
                date = f"{year}-{datetime.strptime(month, '%b').month:02d}"
            return date + ('T' + time_part if time_part else '')

        # Handle compact date format '19OCT2023'
        if len(date) == 9:
            try:
                day = date[:2]
                month = date[2:5]
                year = date[5:]
                date = datetime.strptime(f'{day} {month} {year}', '%d %b %Y').strftime('%Y-%m-%d')
                return date + ('T' + time_part if time_part else '')
            except ValueError:
                pass
    
    # If the date is already a datetime.datetime or datetime.date, convert it to a string
    if isinstance(date, (datetime, dt_date)):
        date = date.strftime('%Y-%m-%d')
    
    return date + ('T' + time_part if time_part else '')



# =============================================================================
# def preprocess_dates(date):
#     time_part = ''
#     if isinstance(date, str):
#         # Separate the time part if 'T' is in the date
#         if 'T' in date:
#             date, time_part = date.split('T')
#         
#         # Handle the 'UN UNK 2023' format
#         if 'UN UNK' in date:
#             return date.split()[-1]
# 
#         # Handle the 'UN DEC 2023' format
#         if date.startswith('UN'):
#             parts = date.split()
#             if len(parts) == 3:
#                 year = parts[-1]
#                 month = parts[1]
#                 date = f"{year}-{datetime.strptime(month, '%b').month:02d}"
#         if len(date) == 9:
#             date = f"{date[:2]} {date[2:5]} {date[5:]}"
#         # Handle partial dates like '2023-11'
#         if len(date.split('-')) == 2:
#             return date + ('T' + time_part if time_part else '')
# 
#         # Handle the '04 JAN 2024' format
#         try:
#             date = datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
#         except ValueError:
#             pass
# 
#         # Handle the '2024-01-04' format
#         try:
#             date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
#         except ValueError:
#             pass
# 
#     return date + ('T' + time_part if time_part else '')
# =============================================================================


# Function to preprocess the Time column
def preprocess_time(time):
    if isinstance(time, str) and time not in ['12:00:00', '00:00:00']:
        return time  # Keep the original format
    return None

# Function to combine date and time into a single datetime column
def combine_date_time(date, time):
    # Check if either date or time is NaN or empty
    if pd.isna(date) or date == '':
        return time if pd.notna(time) else None  # Return only time if date is missing, or None if both are missing
    
    if pd.isna(time) or time == '':
        return date  # Return only date if time is missing
    
    # If both date and time are present, combine them
    try:
        return f"{date}T{time}"
    except Exception:
        return date  # Fallback: return date only if something goes wrong

def safe_convert(date_str):
    try:
        return datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
    except ValueError:
        #print(f"Failed to convert: {date_str}")
        return date_str  # or return np.nan if you want to set it to NaN
# =============================================================================
# def filter_and_unpivot_columns(df, file_name):
#     # Handle the special case for 'labcorp' dataset
#     if 'labcorp' in file_name:
#         if 'SUBJID' not in df.columns or 'LBDTM' not in df.columns:
#             print(f"Labcorp dataset {file_name} does not have SUBJID or LBDTM columns. Skipping this dataset.")
#             return None
#         df_filtered = df.loc[:, ['SUBJID', 'LBDTM']]
#         df_filtered.loc[:, 'dataset'] = file_name
#         df_filtered = df_filtered.rename(columns={'LBDTM': 'Dates'})
#         df_filtered.loc[:, 'data_page_name'] = 'labcorp'  # Assuming a placeholder name since 'data_page_name' is not present
#         return df_filtered
#     
#     # Check if required columns are present
#     if 'SUBJID' not in df.columns or 'data_page_name' not in df.columns:
#         print(f"Dataset {file_name} does not have SUBJID or data_page_name columns. Skipping this dataset.")
#         return None
#     
#     # Select columns that end with '_DAT_RAW' and 'SUBJID'
#     columns_to_keep = [col for col in df.columns if col.endswith('_DAT_RAW') or or col.endswith('DTM') or col in ['SUBJID', 'data_page_name']]
#     df_filtered = df.loc[:, columns_to_keep]
#     df_filtered.loc[:, 'dataset'] = file_name
#     
#     # Unpivot the date columns
#     date_columns = [col for col in df_filtered.columns if col.endswith('_DAT_RAW') or col.endswith('DTM')]
#     df_unpivoted = df_filtered.melt(id_vars=['SUBJID', 'data_page_name', 'dataset'], value_vars=date_columns, var_name='Date_Type', value_name='Dates')
#     return df_unpivoted
# =============================================================================
# Function to process datasets

def process_datasets(df_xl, sas_directory, aggregation='max', remove_time=False, all_dates=False, remove_partial=True):
    date_vars_dict = {}
    time_vars_dict = {}
    dataframes = []

    for input_var in df_xl['Input Variables']:
        input_var = str(input_var).strip()
    
        # Insert commas before occurrences of 'raw' or 'RAW' that are not at the start of the string
        formatted_input_var = ''
        parts = input_var.split('raw.')  # Split the string by 'raw'
        formatted_input_var += parts[0]  # Start with the first part (before 'raw')
    
        for part in parts[1:]:
            if formatted_input_var:  # Only add a comma if this isn't the very first segment
                formatted_input_var += ',raw.'
            else:
                formatted_input_var += 'raw.'
            formatted_input_var += part
    
        input_var = formatted_input_var.strip()  # Apply any final trimming if needed

        # Now process the input_var as before
        variables = input_var.split(',')
        for var in variables:
            parts = var.strip().split('.')
            if len(parts) == 3:
                dataset_name = parts[1]
                var_name = parts[2].upper()
                if not var_name.endswith('_RAW'):
                    raw_var_name = f"{var_name}_RAW"
                    dataset_file = os.path.join(sas_directory, f"{dataset_name}.sas7bdat")
                
                    if os.path.exists(dataset_file):
                        df, meta = pyreadstat.read_sas7bdat(dataset_file)
                        if raw_var_name in df.columns:
                            var_name = raw_var_name

                if var_name.endswith('TIM') or var_name.endswith('TTM'):
                    if dataset_name not in time_vars_dict:
                        time_vars_dict[dataset_name] = []
                    time_vars_dict[dataset_name].append(var_name)
                else:
                    if dataset_name not in date_vars_dict:
                        date_vars_dict[dataset_name] = []
                    date_vars_dict[dataset_name].append(var_name)

    # Iterate through each dataset and its date variables
    for dataset_name in set(date_vars_dict) | set(time_vars_dict):
        date_vars = date_vars_dict.get(dataset_name, [])
        time_vars = time_vars_dict.get(dataset_name, [])

        dataset_file = os.path.join(sas_directory, dataset_name + ".sas7bdat")
        if not os.path.exists(dataset_file):
            print(f"Dataset file {dataset_file} does not exist. Skipping.")
            continue

        # Read the SAS dataset
        df, meta = pyreadstat.read_sas7bdat(dataset_file)
        if df.empty:
            print(f"Read dataset {dataset_name} with shape {df.shape} - Empty dataset")
            continue
        else:
            print(f"Read dataset {dataset_name} with shape {df.shape}")

        # Filter the columns and add the dataset column
        filtered_df = filter_columns(df, dataset_name, date_vars, time_vars)
        print(f"Filtered columns for dataset {dataset_name}, resulting shape: {filtered_df.shape}")
        for date_var in date_vars:
            print("Processing date variable: ", date_var)
            if date_var in filtered_df.columns:
                filtered_df[date_var] = filtered_df[date_var].apply(preprocess_dates)
                filtered_df[date_var] = filtered_df[date_var].apply(safe_convert)
        # Combine date and time columns before preprocessing
        for date_var in date_vars:
            base_name = date_var[:-4]  # Get the base name by removing '_RAW'
            print("base name", base_name)
            # Generate possible corresponding time variable names
            if "ST" in base_name:
                possible_time_vars = [
                    f"{base_name.replace('DT', '')}TIM",  # Replace 'DT' with 'ST' and add TIM
                    f"{base_name.replace('DT', '')}TM"   # Replace 'DT' with 'ST' and add TTM
                ]
            else:
                possible_time_vars = [
                    f"{base_name}TIM",  # base + TIM
                    f"{base_name}TTM",  # base + TTM
                    f"{base_name.replace('DT', 'ST')}TIM",  # Replace 'DT' with 'ST' and add TIM
                    f"{base_name.replace('DT', 'ST')}TM"   # Replace 'DT' with 'ST' and add TTM
                ]
            
            print("possible time var",possible_time_vars)
            # Check for the existence of time variables and apply the combine_date_time function
            for time_var in possible_time_vars:
                if time_var in filtered_df.columns:
                    print(f"Processing time variable {time_var} for date variable {date_var}")
                    filtered_df[date_var] = filtered_df.apply(
                        lambda row: combine_date_time(row[date_var], row[time_var]) if pd.notna(row[time_var]) else row[date_var],
                        axis=1
                    )
                    break  # Stop after finding the first valid time variable
            
        # Preprocess the Dates columns


        print(f"Preprocessed dates and times for dataset {dataset_name}")

        # Unpivot the date columns
        df_unpivoted = filtered_df.melt(id_vars=['X_SUBJID', 'dataset', 'DATAPAGENAME','FOLDERNAME'],
                                        value_vars=date_vars, var_name='Var_Name', value_name='Dates')
        print(f"Unpivoted dataframe for dataset {dataset_name}, resulting shape: {df_unpivoted.shape}")

        # Drop rows where Dates are None or empty
        df_unpivoted = df_unpivoted.dropna(subset=['Dates'])
        df_unpivoted.to_excel('all_chk.xlsx', index=False)

        # Add the filtered and unpivoted dataframe to the list
        dataframes.append(df_unpivoted)

    # Concatenate all filtered dataframes
    if dataframes:
        final_df = pd.concat(dataframes, ignore_index=True)
        
    else:
        print("No dataframes to concatenate.")
        return pd.DataFrame()

    print(f"Concatenated dataframe shape: {final_df.shape}")
    final_df.to_excel('all_chk1.xlsx', index=False)
    
    #final_df['Dates'] = final_df['Dates'].apply(preprocess_dates)
    final_df = final_df[final_df['Dates'].notnull() & (final_df['Dates'].str.strip() != '')]
    #final_df = final_df[~final_df['Dates'].str.contains('[A-Za-z]', regex=True)]
    final_df = final_df[~final_df['Dates'].str.contains('[A-SU-Za-su-z]', regex=True)]

    #final_df = final_df[~final_df['Dates'].str.contains('UN')]


    col_name=df_xl['Variable']
    print(col_name)
    # Sort the dataframe by X_SUBJID, Dates, and DATAPAGENAME
    final_df = final_df.sort_values(by=['X_SUBJID', 'Dates', 'DATAPAGENAME','FOLDERNAME','Var_Name'], ascending=[True, False, False,False,False])
    final_df.to_excel('all_chk2.xlsx', index=False)
    # Remove time part if specified
    if remove_time:
        final_df.to_excel('all_date_time.xlsx', index=False)
        final_df['Dates'] = final_df['Dates'].apply(lambda x: x.split('T')[0] if 'T' in x else x)
        
    if remove_partial:
        final_df = final_df[final_df['Dates'].apply(lambda x: len(x) == 10)]
    if all_dates:
        final_df.to_excel('all_dates.xlsx', index=False)
    col_name=df_xl['Variable']    
    if not df_xl['Variable'].empty:
        final_col_name = df_xl['Variable'].iloc[0]
        print("col name", final_col_name)
        final_df = final_df.rename(columns={'Dates': final_col_name})
        
    max_dates_df = final_df.groupby('X_SUBJID', as_index=False).agg({final_col_name: aggregation})
    max_dates_with_datapagename = pd.merge(max_dates_df, final_df[['X_SUBJID', final_col_name, 'DATAPAGENAME','FOLDERNAME','Var_Name']], on=['X_SUBJID', final_col_name], how='left')
    max_dates_with_datapagename = max_dates_with_datapagename.groupby(['X_SUBJID', final_col_name,'FOLDERNAME'], as_index=False).agg({
            'DATAPAGENAME': 'first',  # or use 'last'/'min'/'max' depending on your requirement
            'Var_Name': lambda x: ' '.join(sorted(set(x)))  # concatenate the Var_Name values with space
        })
    
    # Filter death dates from the main DataFrame
    dth_dts = final_df[final_df["DATAPAGENAME"].str.contains("DEATH", case=False, na=False)]
    
    # Rename the 'Dates' column to 'Death_date'
    dth_dts = dth_dts.rename(columns={final_col_name: 'Death_date'})
    dth_dts.to_excel('all_dates_dth.xlsx', index=False)
    # Check if the death dates DataFrame is not empty
    if not dth_dts.empty:
        # Merge with the main DataFrame based on 'X_SUBJID'
        max_dates_with_datapagename = pd.merge(max_dates_with_datapagename, dth_dts[['X_SUBJID', 'Death_date']], on='X_SUBJID', how='left')
        
        # Update the date variable if it is greater than the death date
        max_dates_with_datapagename[final_col_name] = np.where(
            (max_dates_with_datapagename[final_col_name] > max_dates_with_datapagename['Death_date']) & ~max_dates_with_datapagename['Death_date'].isna(),
            max_dates_with_datapagename['Death_date'], max_dates_with_datapagename[final_col_name]
        )
        
        # Drop the 'Death_date' column after adjustments
        max_dates_with_datapagename = max_dates_with_datapagename.drop(columns=['Death_date'])

    return max_dates_with_datapagename



# Usage example:
# df_xl = pd.read_excel("path_to_excel_file.xlsx")
# sas_directory = "path_to_sas_files_directory"
# result_df = process_datasets(df_xl, sas_directory, aggregation='max')
# result_df = get_max_dates_with_datapagename(result_df)
# print(result_df)
