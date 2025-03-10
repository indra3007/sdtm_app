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
from dm_checks import (check_dm_actarm_arm,
                       check_dm_ae_ds_death,
                       check_dm_age_missing,
                       check_dm_armnrs_missing,
                       check_dm_armcd,
                       check_dm_dthfl_dthdtc,
                       check_dm_usubjid_ae_usubjid,
                       check_dm_usubjid_dup,
                       check_dm_arm_scrnfl,
                       check_dm_ds_icdtc,
                       check_dm_rficdtc,
                       generate_dm_plots_html
                       )
from ae_checks import (check_ae_aeacn_ds_disctx_covid,
                      check_ae_aeacnoth,
                      check_ae_aeacnoth_ds_disctx,
                      check_ae_aeacnoth_ds_stddisc_covid,
                      check_ae_aedecod,
                      check_ae_aedthdtc_aesdth,
                      check_ae_aedthdtc_ds_death,
                      check_ae_aeout,
                      check_ae_aeout_aeendtc_aedthdtc,
                      check_ae_aeout_aeendtc_nonfatal,
                      check_ae_aerel,
                      check_ae_aesdth_aedthdtc,
                      check_ae_aestdtc_after_aeendtc,
                      check_ae_aestdtc_after_dd,
                      check_ae_aetoxgr,
                      check_ae_death,
                      check_ae_ds_partial_death_dates,
                      check_ae_dup,
                      check_ae_fatal,
                      check_ae_withdr_ds_discon,
                      generate_ae_plots
                )

from ce_checks import (check_ce_missing_month
                       )

from cm_checks import (check_cm_cmdecod,
                       check_cm_cmindc,
                       check_cm_cmlat,
                       check_cm_missing_month
                       )
from dd_checks import (check_dd_ae_aedthdtc_ds_dsstdtc,
                       check_dd_ae_aeout_aedthdtc,
                       check_dd_death_date
                       )
from ds_checks import (check_ds_ae_discon,
                       check_ds_dsdecod_death,
                       check_ds_dsdecod_dsstdtc,
                       check_ds_dsscat,
                       check_ds_dsterm_death_due_to,
                       check_ds_duplicate_randomization,
                       check_ds_ex_after_discon,
                       check_ds_multdeath_dsstdtc,
                       check_ds_sc_strat,
                       comp_status_dis,
                       study_status_arm,
                       dispo_time,
                       sub_stat_epoch,
                       dispo_event,
                       dispo_reas
                       )
from dv_checks import (check_dv_ae_aedecod_covid,
                       check_dv_covid
                       )
from eg_checks import (check_eg_egdtc_visit_ordinal_error
                       )
from ex_checks import (check_ex_dup,
                       check_ex_exdose_exoccur,
                       check_ex_exdose_pos_exoccur_no,
                       check_ex_exdosu,
                       check_ex_exoccur_exdose_exstdtc,
                       check_ex_exoccur_mis_exdose_nonmis,
                       check_ex_exstdtc_after_dd,
                       check_ex_exstdtc_visit_ordinal_error,
                       check_ex_extrt_exoccur,
                       check_ex_infusion_exstdtc_exendtc,
                       check_ex_visit
                       )
from lb_checks import (check_lb_lbdtc_after_dd,
                       check_lb_lbdtc_visit_ordinal_error,
                       check_lb_lbstnrlo_lbstnrhi,
                       check_lb_lbstresc_char,
                       check_lb_lbstresn_missing,
                       check_lb_lbstresu,
                       check_lb_missing_month
                       )
from mh_checks import (check_mh_missing_month
                       )
from mi_checks import (check_mi_mispec
                       )
from pr_checks import (check_pr_missing_month,
                       check_pr_prlat
                       )
from qs_checks import (check_qs_dup,
                       check_qs_qsdtc_after_dd,
                       check_qs_qsdtc_visit_ordinal_error,
                       check_qs_qsstat_qsreasnd,
                       check_qs_qsstat_qsstresc
                       
                       )
from rs_checks import (check_rs_rscat_rsscat,
                       check_rs_rsdtc_across_visit,
                       check_rs_rsdtc_visit
                      )
from sc_checks import (check_sc_dm_eligcrit
                       )
from ss_checks import (check_ss_ssdtc_alive_dm,
                       check_ss_ssdtc_dead_ds,
                       check_ss_ssdtc_dead_dthdtc,
                       check_ss_ssstat_ssorres
                       )
from tr_checks import (check_tr_dup,
                       check_tr_trdtc_across_visit,
                       check_tr_trdtc_visit_ordinal_error,
                       check_tr_trstresn_ldiam
                       )
from ts_checks import (check_ts_aedict,
                       check_ts_cmdict,
                       check_ts_sstdtc_ds_consent
                       )
from tu_checks import (check_tu_rs_new_lesions,
                       check_tu_tudtc,
                       check_tu_tudtc_across_visit,
                       check_tu_tudtc_visit_ordinal_error,
                       check_tu_tuloc_missing
                       )
from vs_checks import (check_vs_height,
                       check_vs_sbp_lt_dbp,
                       check_vs_vsdtc_after_dd
                       )
from sv_checks import (check_sv_svstdtc_visit_ordinal_error,
                       check_sv_dupc_visit
                       )
from cdisc_gil_req_vars import(req_vars)
from dates_all_chk import process_datasets
#from mean_plot import(generate_test_plot)
project = "p621"
study = "s6216463"
data_path = f"G:/projects/{project}/{study}/csdtm_dev/draft1/sdtmdata"
raw_data_path = data_path.replace("sdtmdata", "rawdata")


   
# Load the dataframe]
# Run the check function
#result = check_ae_aeacn_ds_disctx_covid()
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
    #check_dm_usubjid_ae_usubjid(data_path),
    check_dm_usubjid_dup(data_path),
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
    #check_cm_cmindc(data_path)
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
    #check_ex_exoccur_exdose_exstdtc(data_path) check this later on date time function 
    check_ex_exoccur_mis_exdose_nonmis(data_path),
    check_ex_exstdtc_after_dd(data_path),
    check_ex_exstdtc_visit_ordinal_error(data_path),
    check_ex_extrt_exoccur(data_path),
    check_ex_infusion_exstdtc_exendtc(data_path),
    check_ex_visit(data_path),
    check_lb_lbdtc_after_dd(data_path),
    check_lb_lbdtc_visit_ordinal_error(data_path),#re-check
    check_lb_lbstnrlo_lbstnrhi(data_path), #re-check
    check_lb_lbstresc_char(data_path),
    check_lb_lbstresn_missing(data_path),
    check_lb_lbstresu(data_path),
    check_lb_missing_month(data_path),
    check_mh_missing_month(data_path),
    check_mi_mispec(data_path),
    check_pr_missing_month(data_path),
    #check_pr_prlat(data_path) #modify this later 
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

all_files = [f for f in os.listdir(data_path) if f.endswith('.sas7bdat') and not f.lower().startswith('supp')]
file_datasets = set([os.path.splitext(f)[0].upper() for f in all_files])

# Find files in data_path that are not in combined_results
missing_files = list(file_datasets - unique_datasets)

# Initialize Excel writer
match = re.search(r's\d+', data_path)
if match:
    study = match.group(0)

writer = pd.ExcelWriter(f"Quality_checks_{study}.xlsx", engine='xlsxwriter')
workbook = writer.book

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

# Write summary sheet
summary_df.to_excel(writer, sheet_name='Summary', index=False)

# Create and write the all_dates sheet
#%%
dates_df, all_dates = process_datasets(raw_data_path, aggregation='max', remove_time=True, all_dates=True)
dates_df.to_excel(writer, sheet_name='all_dates', index=False)

#Write detailed sheets for failed checks with custom naming and keep track of sheet names
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

# Save the Excel file
writer.close()

# Write combined results to an Excel file
#combined_results.to_excel('sdtm_checks.xlsx', index=False)
#results.to_excel('sdtm_checks.xlsx', index=False)

dm_plot_html_list = generate_dm_plots_html(data_path)
ae_plot_html_list = generate_ae_plots(data_path)
comp_status_dis_html = comp_status_dis(data_path)
study_status_arm_html = study_status_arm(data_path)
dispo_time_html = dispo_time(data_path)
sub_stat_epoch_html = sub_stat_epoch(data_path)
dispo_event_html = dispo_event(data_path)
dispo_reas_html = dispo_reas(data_path)
# Combine all plot HTML lists
ds_html_list = comp_status_dis_html + study_status_arm_html + dispo_time_html + sub_stat_epoch_html + dispo_event_html + dispo_reas_html




def summary_stats_fig(df, count_var, visit_col_n, visit_col, test_col):
    """
    Generalized function to calculate summary statistics for any test column.
    """
    # Aggregate summary statistics
    fig_summary_stats = df.groupby([visit_col_n, visit_col, test_col], as_index=False).agg(
        N=(count_var, "count"),
        Mean=(count_var, "mean"),
        SEM=(count_var, "sem"),
        SD=(count_var, "std"),
        Min=(count_var, "min"),
        Max=(count_var, "max"),
        Median=(count_var, "median")
    )
    return fig_summary_stats

def generate_test_plot(df, test_value, test_col, visit_col_n, visit_col):
    """
    Generalized function to generate plots for any test column and dynamically detected value column.
    """
    # Dynamically detect the value column ending with "STRESN"
    value_columns = [col for col in df.columns if col.endswith("STRESN")]
    if not value_columns:
        return "No column ending with 'STRESN' found in the data."

    value_col = value_columns[0]  # Use the first detected value column

    # Filter data for the selected test value and drop rows with NaN in the value column
    filtered_data = df[df[test_col] == test_value].dropna(subset=[value_col])

    # Ensure necessary columns exist
    required_columns = {test_col, value_col, visit_col_n, visit_col}
    if not required_columns.issubset(filtered_data.columns):
        return f"Required columns {', '.join(required_columns)} not found in data."

    # Calculate summary statistics
    summary_stats = summary_stats_fig(filtered_data, value_col, visit_col_n, visit_col, test_col)
    summary_stats["LCLM"] = summary_stats["Mean"] - summary_stats["SEM"]
    summary_stats["UCLM"] = summary_stats["Mean"] + summary_stats["SEM"]

    # Define x-axis order based on visit column
    x_order = filtered_data.sort_values(by=[visit_col_n])[visit_col].unique()

    # Create line plot with error bars
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=summary_stats[visit_col],
            y=summary_stats["Mean"],
            mode="lines",
            name=test_value,
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
        title=f"Mean Plot of {test_value} by Visit",
        xaxis=dict(title="Visit", categoryorder="array", categoryarray=x_order),
        yaxis=dict(title="Mean"),
        hovermode="x",
        height=500,
        width=1200  # Specify a numeric width in pixels
    )
    return fig.to_html(full_html=False)

def generate_static_html(data_path, dataset_name):
    df = load_data(data_path, dataset_name)
    normalized_columns = [col.strip().upper() for col in df.columns]
    test_columns = [col for col, normalized_col in zip(df.columns, normalized_columns) if normalized_col.endswith("TEST")]
    value_columns = [col for col, normalized_col in zip(df.columns, normalized_columns) if normalized_col.endswith("STRESN")]

    if test_columns and value_columns:
        test_column = test_columns[0]  # Use the first matching column
        test_values = df[test_column].unique()

        # Initialize HTML content for the tab
        tab_content = f"""
        <div class="tab-content" id="LB">
            <h3 style="font-size: 20px; font-weight: bold; color: #4B0082; text-align: center; margin-bottom: 15px;">
                Mean plots for Data Review - LB
            </h3>
        """

        # Loop through all test values and generate plots
        for test_value in test_values:
            plot_html = generate_test_plot(df, test_value, test_column, "VISITNUM", "VISIT")
            tab_content += f"<h4 style='text-align: center;'>{test_value}</h4>"
            tab_content += plot_html

        # Close the tab content
        tab_content += """
        </div>
        """

        return tab_content

# Example usage

dataset_name = "lb"
lb_tab_content = generate_static_html(data_path, dataset_name)

# Initialize HTML content for the main file
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Combined Plots</title>
    <style>
        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
        }
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
        }
        .tab button:hover {
            background-color: #ddd;
        }
        .tab button.active {
            background-color: #ccc;
        }
        .tab-content {
            display: none;
            padding: 6px 12px;
            border-top: none;
            min-height: 100vh; /* Ensure minimum height */
            overflow: auto; /* Enable scrolling if content overflows */
            width: 100%;
        }
    </style>
</head>
<body>

<div class="tab">
    <button class="tablinks" onclick="openTab(event, 'DM')">DM</button>
    <button class="tablinks" onclick="openTab(event, 'AE')">AE</button>
    <button class="tablinks" onclick="openTab(event, 'LB')">LB</button>
    <button class="tablinks" onclick="openTab(event, 'DS')">DS</button>
</div>

<div id="DM" class="tab-content">
"""

# Add the tab content for DM
for plot_html in dm_plot_html_list:
    html_content += plot_html

# Close the DM tab content
html_content += """
</div>
"""

# Add the tab content for AE
html_content += """
<div id="AE" class="tab-content">
"""
for plot_html in ae_plot_html_list:
    html_content += plot_html

# Close the AE tab content
html_content += """
</div>
"""

# Add the tab content for LB
html_content += lb_tab_content

# Add the tab content for DS
html_content += """
<div id="DS" class="tab-content">
"""
for plot_html in ds_html_list:
    html_content += plot_html

# Close the DS tab content
html_content += """
</div>
"""

# Close the HTML content
html_content += """
<script>
function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}
document.getElementsByClassName("tablinks")[0].click(); // Open the first tab by default
</script>

</body>
</html>
"""

# Write the combined HTML content to a single file
with open("combined_plots.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("Combined HTML report generated successfully!")