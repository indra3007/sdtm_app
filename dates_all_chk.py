import os
import pyreadstat
import pandas as pd
import numpy as np
from datetime import datetime, date as dt_date


def process_datasets(sas_directory, aggregation='max', remove_time=False, all_dates=False, remove_partial=True):
    dataframes = []

    # Loop through each file in the directory
    for file_name in os.listdir(sas_directory):
        if file_name.endswith(".sas7bdat"):
            dataset_name = os.path.splitext(file_name)[0]
            dataset_file = os.path.join(sas_directory, file_name)

            try:
                # Read the SAS dataset
                df, meta = pyreadstat.read_sas7bdat(dataset_file)
                if df.empty:
                    print(f"Dataset {dataset_name} is empty. Skipping.")
                    continue
            except Exception as e:
                print(f"Error reading dataset {dataset_name}: {str(e)}")
                continue

            # Filter the columns and add the dataset column
            filtered_df = filter_columns(df, dataset_name)
            if filtered_df is None:
                print(f"Skipping dataset {dataset_name}: 'X_SUBJID' or 'USUBJID' missing.")
                continue

            # Identify date variables
            date_vars = [col for col in filtered_df.columns if col.endswith(('DAT_RAW', 'DTM', 'DTC', 'DTN'))]
            if not date_vars:
                print(f"No date columns found in dataset {dataset_name}. Skipping.")
                continue

            # Combine date and time columns before preprocessing
            for date_var in date_vars:
                time_var = f"{date_var[:4]}TIM"
                if time_var in filtered_df.columns:
                    filtered_df[date_var] = filtered_df.apply(
                        lambda row: combine_date_time(row[date_var], row[time_var]) if pd.notna(row[time_var]) else row[date_var],
                        axis=1
                    )

            # Preprocess the date columns
            for date_var in date_vars:
                try:
                    filtered_df[date_var] = filtered_df[date_var].apply(preprocess_dates)
                except Exception as e:
                    print(f"Error preprocessing date column {date_var} in dataset {dataset_name}: {str(e)}")
                    continue

            # Unpivot the date columns
            try:
                df_unpivoted = filtered_df.melt(
                    id_vars=['X_SUBJID', 'dataset', 'DATAPAGENAME'],
                    value_vars=date_vars,
                    var_name='Var_Name', value_name='Dates'
                )
            except KeyError as e:
                print(f"Error unpivoting dataset {dataset_name}: {str(e)}")
                continue

            # Drop rows where Dates are missing
            df_unpivoted = df_unpivoted.dropna(subset=['Dates'])

            # Add the processed dataframe to the list
            dataframes.append(df_unpivoted)

    # Concatenate all filtered dataframes
    if dataframes:
        final_df = pd.concat(dataframes, ignore_index=True)
    else:
        print("No valid dataframes to concatenate.")
        return pd.DataFrame(), pd.DataFrame()

    # Process Dates column
    final_df['Dates'] = final_df['Dates'].astype(str)
    final_df = final_df[final_df['Dates'] != '']
    final_df = final_df[~final_df['Dates'].str.contains('UN')]

    # Sort the dataframe
    final_df = final_df.sort_values(by=['X_SUBJID', 'Dates', 'DATAPAGENAME', 'Var_Name'], ascending=[True, False, False, False])

    # Remove time part if specified
    if remove_time:
        final_df['Dates'] = final_df['Dates'].apply(lambda x: x.split('T')[0] if 'T' in x else x)
    if remove_partial:
        final_df = final_df[final_df['Dates'].apply(lambda x: len(x) == 10)]
    if all_dates:
        final_df = final_df.drop_duplicates()

    # Aggregate the dates
    final_col_name = 'Dates'
    max_dates_df = final_df.groupby('X_SUBJID', as_index=False).agg({final_col_name: aggregation})
    max_dates_with_datapagename = pd.merge(
        max_dates_df,
        final_df[['X_SUBJID', final_col_name, 'DATAPAGENAME', 'Var_Name']],
        on=['X_SUBJID', final_col_name], how='left'
    )
    max_dates_with_datapagename = max_dates_with_datapagename.groupby(['X_SUBJID', final_col_name], as_index=False).agg({
        'DATAPAGENAME': 'first',
        'Var_Name': lambda x: ' '.join(sorted(set(x)))
    })

    return max_dates_with_datapagename, final_df


def filter_columns(df, dataset_name):
    """Filter columns for processing, ensuring X_SUBJID or USUBJID is present."""
    if 'X_SUBJID' not in df.columns:
        if 'USUBJID' in df.columns:
            df['X_SUBJID'] = df['USUBJID']
        else:
            return None

    date_vars = [col for col in df.columns if col.endswith(('DAT_RAW', 'DTM', 'DTC', 'DTN'))]
    columns_to_keep = ['X_SUBJID'] + date_vars

    if 'DATAPAGENAME' in df.columns:
        columns_to_keep.append('DATAPAGENAME')
    else:
        df['DATAPAGENAME'] = dataset_name
        columns_to_keep.append('DATAPAGENAME')
    df['dataset'] = dataset_name
    return df


def preprocess_dates(date):
    """Process various date formats into ISO 8601 format."""
    time_part = ''

    if isinstance(date, str) and 'T' in date:
        date, time_part = date.split('T')

    if pd.isna(date):
        return np.nan

    if isinstance(date, (int, float)):
        date = str(int(date))

    if isinstance(date, str):
        # Handle '24JAN2024' format
        try:
            return datetime.strptime(date, '%d%b%Y').strftime('%Y-%m-%d') + ('T' + time_part if time_part else '')
        except ValueError:
            pass

        # Other formats (partial dates, etc.)
        # Add format-specific handling here

    if isinstance(date, (datetime, dt_date)):
        return date.strftime('%Y-%m-%d') + ('T' + time_part if time_part else '')

    return date


def combine_date_time(date, time):
    """Combine date and time into ISO 8601 format."""
    if pd.isna(time):
        return date
    try:
        return f"{date}T{time}"
    except Exception:
        return date

#project = "p621"
#study = "s6216463"
# #excel_file = "G:/users/inarisetty/private/python/combined_data_s5926173.xlsx"
#sas_directory = f"G:/projects/{project}/{study}/csdtm_dev/draft1/rawdata/"

#result_df,all_dates = process_datasets(sas_directory, aggregation='max', remove_time=True, all_dates=True)
# print('dates', all_dates)
# print('result', result_df)
#all_dates.to_excel('all_dates.xlsx', index=False)

