# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 13:18:39 2024

@author: inarisetty
"""
import pyreadstat
import pandas as pd 

import dtale
from openpyxl import load_workbook

excel_file = "G:/projects/p624/s624637603/csdtm_dev/draft1/docs/sdtm/s624637603_csdtm_dev_sdtm_mapping.xlsx"
exclude_sheets = ['Standards','TOC','<ds>','Codelist','COmputation','Valuelist','Maintenance','Findings']
sheet_name = "DM"
workbook = load_workbook(excel_file)

sheet = workbook[sheet_name]
data = sheet.values
columns = next(data)[0:]
df_xl = pd.DataFrame(data, columns=columns)

def load_data(file_name):
    file_path = f"G:/projects/p624/s624637603/csdtm_dev/draft1/rawdata/{file_name}.sas7bdat"
    df, meta = pyreadstat.read_sas7bdat(file_path, encoding="LATIN1")
    return df

DM = load_data("DM")
    
def transform_usubjid(usubjid):
    parts = usubjid.split('-')
    
    # Get the second last and the last part
    second_last_part = parts[-2]
    last_part = parts[-1]
    
    # Concatenate with a hyphen
    result = second_last_part + '-' + last_part
    
    return result




# Step 2: Filter rows where input_variables starts with 'raw.'
df_xl['Input Variables'] = df_xl['Input Variables'].fillna('')
mapping_df = df_xl[df_xl['Input Variables'].str.startswith('raw.dm')]

# Step 3: Extract source variable from input_variables
def extract_source_variable(input_variable):
    if pd.isna(input_variable):
        return None
    parts = input_variable.split('.')
    if len(parts) >= 3:
        return parts[2]
    return None

mapping_df['source_variable'] = mapping_df['Input Variables'].apply(extract_source_variable)

# Step 4: Create a mapping dictionary from source_variable to variable
mapping_dict = mapping_df.set_index('source_variable')['Variable'].to_dict()


# Step 6: Rename the columns in the source DataFrame using the mapping
DM_sdtm = DM.rename(columns=mapping_dict)

d = dtale.show(DM_sdtm, open_browser=True)
# Step 7: Display the transformed DataFrame
print(mapping_df)
#print(DM_sdtm)