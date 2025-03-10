# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 16:04:35 2025

@author: inarisetty
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pyreadstat
import pandas as pd 
import dash
from datetime import datetime
import os
from utils import load_data,is_null_or_empty
import re 
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH
import dash_ag_grid as dag
from dash import dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import time
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
                       generate_dm_plots
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
                       check_ex_visit,
                       dose_overtime,
                       dose_cumdose
                       )
from lb_checks import (check_lb_lbdtc_after_dd,
                       check_lb_lbdtc_visit_ordinal_error,
                       check_lb_lbstnrlo_lbstnrhi,
                       check_lb_lbstresc_char,
                       check_lb_lbstresn_missing,
                       check_lb_lbstresu,
                       check_lb_missing_month,
                       check_dtc_time_format,
                       generate_lbtest_plot,
                       update_param_plot
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
                       surv_dist
                       #check_ss_ssstat_ssorres
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
                       check_sv_dupc_visit,
                       subject_compliance_plot,
                       visit_timing_distribution_plot,
                       visit_sequence_plot,
                       cumulative_visit_completion_plot,
                       subject_dropout_analysis_plot


                       )
from se_checks import (subject_timeline,
                       subject_time_spent,
                       subject_duration,
                       study_elements
                        )           
from cdisc_gil_req_vars import(req_vars)
from mean_plot import(generate_test_plot)
from specs_transform import specs_transform
from dates_all_chk import process_datasets
from narrative import generate_domain_narrative
#project = "p123"
#study = "s123456"

#ata_path = f"G:/projects/{project}/{study}/csdtm_dev/draft1/sdtmdata"


   
# Load the dataframe]
# Run the check function
#result = check_ae_aeacn_ds_disctx_covid()
def run_checks(data_path):
    results = [

        check_dm_actarm_arm(data_path),
        check_dm_ae_ds_death(data_path),
        check_dm_age_missing(data_path),
        #check_dm_armnrs_missing(data_path),
        #check_dm_armcd(data_path),
        #check_dm_arm_scrnfl(data_path),
        check_dm_ds_icdtc(data_path),
        #check_dm_rficdtc(data_path),
        #check_dm_usubjid_ae_usubjid(data_path),
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
        check_dtc_time_format(data_path),
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
        #check_ss_ssstat_ssorres(data_path),
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

    combined_results = pd.concat(results, ignore_index=True)

    # Extract unique datasets from 'Datasets' column
    unique_datasets = set()
    for datasets in combined_results["Datasets"]:
        if isinstance(datasets, str):
            for dataset in datasets.split(", "):
                unique_datasets.add(dataset.upper())

    # List of all dataset files
    all_files = [f for f in os.listdir(data_path) if f.endswith('.sas7bdat') and not f.lower().startswith('supp')]
    file_datasets = set([os.path.splitext(f)[0].upper() for f in all_files])

    # Find missing files
    missing_files = list(file_datasets - unique_datasets)

    # Prepare summary data
    summary_data = []
    detailed_data = {}
    for i, result in enumerate(results):
        if result.empty:
            continue

        check_name = result["CHECK"].iloc[0]
        status = str(result["Message"].iloc[0])
        notes = result["Notes"].iloc[0] if 'Notes' in result.columns else ""
        datasets = result["Datasets"].iloc[0] if 'Datasets' in result.columns else ""
        
        if "Fail" in status:
            sheet_name = f'Sheet{i+1}'
            detailed_data[check_name] = result  # Store the detailed DataFrame
            data_link = f"View Data"
        else:
            data_link = ""
        summary_data.append({
            "CHECK": check_name,
            "Message": status,
            "Notes": notes,
            "Datasets": datasets,
            "Data": data_link
        })

    # Adding missing files to summary
    missing_files_notes = f'Checks not performed for datasets: {", ".join(missing_files)}'
    summary_data.append({
        "CHECK": "Checks not performed",
        "Message": "Fail",
        "Notes": missing_files_notes,
        "Datasets": "",
        "Data": ""
    })

    # Convert to DataFrame
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df[
    ~summary_df["Message"].str.contains("dataset not found at the specified location", na=False, case=False)
]
    return summary_df, detailed_data




# Initialize app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
base_dir = "G:/users/inarisetty"

# Helper functions to get projects and studies dynamically
def get_projects():
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

def get_studies(project):
    project_path = os.path.join(base_dir, project)
    return [d for d in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, d))]

def get_analysis_folders(project, study):
    study_path = os.path.join(base_dir, project, study)
    return [d for d in os.listdir(study_path) if os.path.isdir(os.path.join(study_path, d))]

# Main layout of the app
app.layout = html.Div([
    html.H1("SDTM Quality Checks", style={
        "color": "#2E8B57", 
        "font-weight": "bold", 
        "text-align": "center", 
        "margin-bottom": "20px"}), 

    # Project, Study, and Analysis Folder selection
    html.Div([
        # Project Dropdown
        html.Div([
            html.Label("Select Project", style={"font-size": "16px", "font-weight": "bold", "color": "#2E8B57"}),
            dcc.Dropdown(
                id="project-dropdown",
                options=[{"label": proj, "value": proj} for proj in get_projects()],
                placeholder="Choose a project...",
                clearable=False,
                style={
                    "width": "80%", "margin": "10px 0", "padding": "10px", "border": "1px solid #A2D2A2",
                    "border-radius": "8px", "font-size": "14px"
                }
            )
        ], style={"width": "30%", "display": "inline-block", "vertical-align": "top", "margin-right": "2%"}),

        # Study Dropdown
        html.Div([
            html.Label("Select Study", style={"font-size": "16px", "font-weight": "bold", "color": "#2E8B57"}),
            dcc.Dropdown(
                id="study-dropdown",
                placeholder="Choose a study...",
                clearable=False,
                style={
                    "width": "80%", "margin": "10px 0", "padding": "10px", "border": "1px solid #A2D2A2",
                    "border-radius": "8px", "font-size": "14px"
                }
            )
        ], style={"width": "30%", "display": "inline-block", "vertical-align": "top", "margin-right": "2%"}),

        # Analysis Folder Dropdown
        html.Div([
            html.Label("Choose Analysis Folder", style={"font-size": "16px", "font-weight": "bold", "color": "#2E8B57"}),
            dcc.Dropdown(
                id="analysis-folder-dropdown",
                placeholder="Choose an analysis folder...",
                clearable=False,
                style={
                    "width": "80%", "margin": "10px 0", "padding": "10px", "border": "1px solid #A2D2A2",
                    "border-radius": "8px", "font-size": "14px"
                }
            )
        ], style={"width": "30%", "display": "inline-block", "vertical-align": "top"})
    ], style={"display": "flex", "justify-content": "center", "margin-bottom": "20px"}),
    dcc.Store(id="selected-state", storage_type="memory"),
    # Run checks button
    html.Div([
        html.Button("Run Checks", id="run-checks-button", n_clicks=0, style={
            "background-color": "#2E8B57", "color": "white", "border": "none", 
            "border-radius": "8px", "padding": "10px 20px", "font-size": "16px",
            "font-weight": "bold", "cursor": "pointer"
        }),
        dcc.Loading(
            id="loading-progress",
            type="default",  # Spinner style: "circle", "dot", or "default"
            children=html.Div(id="loading-output", style={"margin-top": "20px"})
        )
    ], style={"text-align": "center", "margin-bottom": "20px"}),

    # Tabs container
    html.Div(id='tabs-container', style={"margin-bottom": "20px"}),

    # Content area for selected tab
    html.Div(id='tab-content', style={
        "border": "2px solid #A2D2A2", 
        "border-radius": "10px", 
        "padding": "20px",
        "backgroundColor": "#ffffff",
        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)"
    })
])

# Callback to update study dropdown based on selected project
@app.callback(
    Output('study-dropdown', 'options'),
    Input('project-dropdown', 'value')
)
def update_study_dropdown(selected_project):
    if not selected_project:
        raise PreventUpdate
    studies = get_studies(selected_project)
    return [{"label": study, "value": study} for study in studies]

# Callback to update analysis folder dropdown based on selected study
@app.callback(
    Output('analysis-folder-dropdown', 'options'),
    [Input('project-dropdown', 'value'), Input('study-dropdown', 'value')]
)
def update_analysis_folder_dropdown(selected_project, selected_study):
    if not selected_project or not selected_study:
        raise PreventUpdate
    folders = get_analysis_folders(selected_project, selected_study)
    return [{"label": folder, "value": folder} for folder in folders]

# Callback to generate tabs and data path after "Run Checks" is clicked
@app.callback(
    [Output('tabs-container', 'children'), Output('loading-output', 'children')],
    [Input('run-checks-button', 'n_clicks')],
    [State('project-dropdown', 'value'), State('study-dropdown', 'value'), State('analysis-folder-dropdown', 'value')]
)
def run_checks_and_display_tabs(n_clicks, selected_project, selected_study, selected_analysis_folder):
    if not selected_project or not selected_study or not selected_analysis_folder or n_clicks == 0:
        raise PreventUpdate

    data_path = f"{base_dir}/{selected_project}/{selected_study}/{selected_analysis_folder}"
    sas_directory = f"{base_dir}/{selected_project}/{selected_study}/{selected_analysis_folder}/draft1/rawdata"
    spec_path = f"{base_dir}/{selected_project}/{selected_study}/{selected_analysis_folder}/_csdtm_dev_sdtm_mapping.xlsx"

    try:
        # Attempt to access the directory or file
        global summary_df, detailed_data, combined_df, study_info, standards_df, dates_df, all_dates
        summary_df, detailed_data = run_checks(data_path)
        #dates_df, all_dates = process_datasets(sas_directory, aggregation='max', remove_time=True, all_dates=True)
        # Load and transform the specifications
        study_info, standards_df, combined_df = specs_transform(spec_path)

        # Filter out "TRIAL DESIGN" datasets and get dataset names in the correct order
        unique_sheets = combined_df["Dataset"].str.upper().unique().tolist()  # Normalize to uppercase
        trial_design_datasets = combined_df[combined_df["Class"].str.upper() == "TRIAL DESIGN"]["Dataset"].str.upper().unique().tolist()

        # Step 2: Load datasets dynamically from the directory
        dataset_files = [
            f for f in os.listdir(data_path)
            if f.endswith('.sas7bdat') 
            and not f.lower().startswith('supp')
            and os.path.splitext(f)[0].upper() not in trial_design_datasets
        ]
        dataset_names = [os.path.splitext(f)[0].upper() for f in dataset_files]

        # Load datasets into a dictionary
        datasets = {
            dataset_name: load_data(data_path, dataset_name)
            for dataset_name in dataset_names
        }

        # Step 3: Order datasets based on specifications
        ordered_datasets = {name: datasets[name] for name in unique_sheets if name in datasets}

        # Extract datasets from the summary_df
        unique_datasets = set(
            sum([ds.split(",") for ds in summary_df["Datasets"].dropna()], [])  # Split by commas
        )
        unique_datasets = {ds.strip() for ds in unique_datasets if ds}

        # Identify available datasets in the directory
        available_datasets = {
            os.path.splitext(f)[0].upper() for f in os.listdir(data_path)
            if f.endswith('.sas7bdat') and not f.lower().startswith('supp')
        }

        # Combine unique datasets and available datasets
        all_datasets = list(ordered_datasets.keys()) + list(unique_datasets - set(ordered_datasets.keys())) + list(available_datasets - set(ordered_datasets.keys()))

        # Ensure "Full Summary" is at the beginning
        all_tabs = ["SDTM Specifications", "All Dates", "Full Summary"] + all_datasets + ["Pateint Level"]


        class_color_mapping = {
            "SPECIAL PURPOSE": "#D8BFD8",  # Light Purple (Thistle)
            "INTERVENTIONS": "#FFA07A",  # Light Red (Light Salmon)
            "EVENTS": "#ADD8E6",  # Light Blue
            "FINDINGS": "#90EE90",  # Light Green
            "FINDINGS ABOUT": "#FFFFE0",  # Light Yellow (Light Yellow)
            "OTHER": "#F0F0F0",  # Light Gray
            "TRIAL DESIGN": "#D3D3D3",  # Light Gray (for neutral tones)
        }


        # Get a dictionary of dataset classes
        dataset_classes = {
            dataset["Dataset"].upper(): dataset["Class"].upper()
            for _, dataset in combined_df.iterrows()
        }

        # Generate tabs with different styles based on their class
        tabs = dcc.Tabs(
            id="dataset-tabs",
            value="SDTM Specifications",  # Default tab
            children=[
                dcc.Tab(
                    label=tab,
                    value=tab,
                    style={
                        "backgroundColor": class_color_mapping.get(
                            dataset_classes.get(tab, "OTHER"), "#f7f7f7"
                        ),
                        "borderRadius": "8px",
                        "padding": "10px 25px",
                        "margin": "5px",
                        "fontWeight": "bold",
                        "color": "#000000",
                        "width": "auto",
                    },
                    selected_style={
                        "backgroundColor": class_color_mapping.get(
                            dataset_classes.get(tab, "OTHER"), "#2E8B57"
                        ),
                        "color": "red",
                        "fontWeight": "bold",
                        "borderRadius": "8px",
                        "padding": "10px 25px",
                        "margin": "5px",
                        "width": "auto",
                    },
                )
                for tab in all_tabs
            ],
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "justifyContent": "center",
                "borderBottom": "2px solid #A2D2A2",
                "margin": "10px 0",
            },
        )

        # Return tabs and clear the loading message
        return tabs, ""

    except PermissionError as e:
        error_message = f"PermissionError: Unable to access the folder or file. {str(e)}"
        return None, html.Div(
            error_message,
            style={
                "color": "red",
                "fontWeight": "bold",
                "textAlign": "center",
                "margin": "20px",
                "border": "2px solid red",
                "padding": "10px",
                "borderRadius": "8px",
            }
        )

    # except Exception as e:
    #     error_message = f"An unexpected error occurred: {str(e)}"
    #     return None, html.Div(
    #         error_message,
    #         style={
    #             "color": "red",
    #             "fontWeight": "bold",
    #             "textAlign": "center",
    #             "margin": "20px",
    #             "border": "2px solid red",
    #             "padding": "10px",
    #             "borderRadius": "8px",
    #         }
    #     )


# Callback to render content in each tab
@app.callback(
    Output('tab-content', 'children'),
    [Input('dataset-tabs', 'value')],
    [State('project-dropdown', 'value'), State('study-dropdown', 'value'), State('analysis-folder-dropdown', 'value')]
)
def render_tab_content(selected_tab, selected_project, selected_study, selected_analysis_folder):
    if not selected_tab or not selected_project or not selected_study or not selected_analysis_folder:
        raise PreventUpdate

    # Define the SDTM data path
    data_path = f"{base_dir}/{selected_project}/{selected_study}/{selected_analysis_folder}"
    content = []

    if selected_tab == "Pateint Level":
        # Dynamically get all datasets from the data path
        try:
            # List all .sas7bdat files in the directory
            dataset_files = [
                f for f in os.listdir(data_path)
                if f.endswith('.sas7bdat') and not f.lower().startswith('supp')  # Exclude supplemental datasets
            ]
            
            # Remove file extensions to get dataset names
            dataset_names = [os.path.splitext(f)[0].upper() for f in dataset_files]

            # Load each dataset into a dictionary
            datasets = {
                dataset_name: load_data(data_path, dataset_name)  # Use your load_data function
                for dataset_name in dataset_names
            }

            # Generate a dropdown with unique USUBJID values across all datasets
            usubjid_options = [{"label": usubjid, "value": usubjid} for usubjid in 
                               pd.concat([df["USUBJID"] for df in datasets.values() if "USUBJID" in df.columns]).unique()]
            
            return html.Div([
                html.Label("Select USUBJID to generate Pateint Level:", style={"font-weight": "bold", "margin-bottom": "10px"}),
                dcc.Dropdown(id="narrative-usubjid-dropdown", options=usubjid_options, style={"width": "50%"}),
                html.Div(id="narrative-content")
            ])
        except Exception as e:
            return html.Div(f"Error loading datasets: {str(e)}", style={"color": "red", "font-weight": "bold"})

        
    elif selected_tab == "All Dates":
        if  all_dates.empty:
            return html.Div(
                "The dataset for All Dates is empty. Please check input files.",
                style={"color": "red", "font-weight": "bold", "text-align": "center", "margin": "20px"}
            )
        else:
            return [
                html.H2("All Dates", style={"text-align": "center", "color": "#2E8B57"}),
                dag.AgGrid(
                    rowData=all_dates.to_dict('records'),
                    columnDefs=[{"headerName": col, "field": col} for col in all_dates.columns],
                    defaultColDef={
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "editable": False,
                        "cellStyle": {
                            "color": "#333333",
                            "fontSize": "14px",
                            "border": "1px solid #A2D2A2",
                            "backgroundColor": "#F9F9F9",
                        },
                    },
                    style={"height": "600px", "width": "100%"},
                ),
            ]
    # Check if the selected tab is "SDTM Specifications"
    elif selected_tab == "SDTM Specifications":
        # Ensure `combined_df` exists
        if combined_df is None or combined_df.empty:
            return html.Div("No SDTM Specifications available.")

        # Create Study Info card
        study_info_cards = []
        if study_info is not None:
            for _, row in study_info.iterrows():
                study_info_cards.append(
                    html.Div(
                        [
                            html.H4(row["Attribute"], style={"color": "#412d8a", "font-weight": "bold"}),
                            html.P(row["Value"], style={"font-size": "14px", "color": "#333"}),
                        ],
                        style={
                            "border": "1px solid #A2D2A2",
                            "border-radius": "8px",
                            "padding": "10px",
                            "margin": "10px",
                            "backgroundColor": "#F9F9F9",
                            "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)",
                            "width": "300px",
                            "display": "inline-block",
                            "vertical-align": "top",
                        },
                    )
                )
        else:
            study_info_cards.append(
                html.Div("Study Info sheet not available.", style={"color": "#FF0000", "font-weight": "bold"})
            )

        # Create Standards Info card
        if standards_df is not None:
            standards_card = html.Div(
                [
                    html.H4("Standards Information", style={"color": "#412d8a", "font-weight": "bold"}),
                    html.Table(
                        [
                            html.Tr([html.Th(col, style={"padding": "8px", "text-align": "left"}) for col in standards_df.columns])
                        ]
                        + [
                            html.Tr([html.Td(row[col], style={"padding": "8px"}) for col in standards_df.columns])
                            for _, row in standards_df.iterrows()
                        ],
                        style={"width": "100%", "border-collapse": "collapse", "table-layout": "fixed"},
                    ),
                ],
                style={
                    "border": "1px solid #A2D2A2",
                    "border-radius": "8px",
                    "padding": "15px",
                    "margin": "10px",
                    "backgroundColor": "#E8F5E9",
                    "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)",
                },
            )
        else:
            standards_card = html.Div(
                "Standards sheet not available.",
                style={
                    "color": "#FF0000",
                    "font-weight": "bold",
                    "border": "1px solid #A2D2A2",
                    "border-radius": "8px",
                    "padding": "15px",
                    "margin": "10px",
                    "backgroundColor": "#FFEBEE",
                    "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)",
                },
            )

        # Return the SDTM Specifications tab content
        return [
            html.H2("SDTM Specifications", style={"text-align": "center", "color": "#2E8B57"}),
            html.Div(
                study_info_cards,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "flexWrap": "wrap",
                    "margin-bottom": "20px",
                },
            ),
            standards_card,
            html.Div(
                [
                    html.H3("Specifications Table", style={"text-align": "center", "color": "#2E8B57"}),
                    dag.AgGrid(
                        rowData=combined_df.to_dict('records'),
                        columnDefs=[{"headerName": col, "field": col} for col in combined_df.columns],
                        defaultColDef={
                            "sortable": True,
                            "filter": True,
                            "resizable": True,
                            "editable": False,
                            "cellStyle": {
                                "color": "#333333",
                                "fontSize": "14px",
                                "border": "1px solid #A2D2A2",
                                "backgroundColor": "#F9F9F9",
                            },
                        },
                        style={"height": "600px", "width": "100%"},
                    ),
                ],
            ),
        ]

    # Display "Full Summary" if selected


    elif selected_tab == "Full Summary":
        if summary_df.empty:
            content.append(html.Div("No summary data available."))
        else:
            row_count = len(summary_df)
            if row_count <= 10:
                height = f"{80 +row_count * 40}px"
            else:
                height = '400px'
            pagination = row_count > 10
            pagination_page_size = 10 if pagination else row_count

            grid_options = {
                'pagination' : pagination,
                'paginationPageSize': pagination_page_size,
                'defaultColDef' : {
                        'sortable': True,
                        'filter': True,
                        'resizable': True,
                        'floatingFilter': False,
                },
                'enableAdvancedFilter': True
            }
            content.append(html.H2("Full Summary Table"))
            content.append(
                dag.AgGrid(
                    rowData=summary_df.to_dict('records'),
                    dashGridOptions = grid_options,
                    columnDefs=[
                        {"headerName": "CHECK", "field": "CHECK"},
                        {"headerName": "Message", "field": "Message"},
                        {"headerName": "Notes", "field": "Notes"},
                        {"headerName": "Datasets", "field": "Datasets"}
                    ],
                    defaultColDef={
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "editable": False,
                        "cellStyle": {
                            "color": "#333333",
                            "fontSize": "14px",
                            "border": "1px solid #A2D2A2",
                            "backgroundColor": "#F9F9F9"
                        },
                    },
                    style={"height": height, "width": "100%", 'margin':'0 auto'}
                )
            )
    else:
        
        dataset_df = load_data(data_path, selected_tab)  # Placeholder function to load dataset
        
        if dataset_df.empty:
            content.append(html.Div(f"No data found for {selected_tab}."))
        else:
            
            # Dropdown for filtering by USUBJID if in DM dataset
            if  "USUBJID" in dataset_df.columns:
                usubjid_options = [{"label": usubjid, "value": usubjid} for usubjid in dataset_df["USUBJID"].unique()]
                content.append(html.Label("Select USUBJID to filter across datasets"))
                content.append(dcc.Dropdown(id="usubjid-dropdown", options=usubjid_options, style={"width": "50%"}))
                content.append(html.Div(id="filtered-dataset"))

            # Display full dataset
            content.append(html.H2(f"{selected_tab} - Full Dataset"))
            content.append(
                dag.AgGrid(
                    rowData=dataset_df.to_dict('records'),
                    columnDefs=[
                        {
                            "headerName": col,
                            "field": col,
                            "enableValue": True,  # Enable aggregation for numeric columns
                            "menuTabs": ["generalMenuTab", "filterMenuTab", "aggregationMenuTab"],  # Enable aggregation tab in the menu
                            "aggFunc": "sum" if pd.api.types.is_numeric_dtype(dataset_df[col]) else None  # Default aggregation function for numeric columns
                        }
                        for col in dataset_df.columns
                    ],
                    defaultColDef={
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "editable": False,
                        "cellStyle": {
                            "color": "#333333",
                            "fontSize": "14px",
                            "border": "1px solid #A2D2A2",
                            "backgroundColor": "#F9F9F9"
                        },
                        "menuTabs": ["generalMenuTab", "filterMenuTab", "aggregationMenuTab"],  # Add aggregation tab for all columns
                    },
                    dashGridOptions={
                        "statusBar": {
                            "statusPanels": [
                                {
                                    "statusPanel": "agAggregationComponent",
                                    "statusPanelParams": {"aggFuncs": ["sum", "avg", "min", "max", "count"]}
                                }
                            ]
                        },
                        "sideBar": {
                            "toolPanels": [
                                {"id": "columns", "labelDefault": "Columns", "toolPanel": "agColumnsToolPanel", "iconKey": "columns"},
                                {"id": "filters", "labelDefault": "Filters", "toolPanel": "agFiltersToolPanel", "iconKey": "filter"},
                            ],
                            "defaultToolPanel": "columns"  # Show column menu tool panel by default
                        },
                    },
                    style={"height": "600px", "width": "100%"}
                )


            )
        
            # Display summary checks
            filtered_summary = summary_df[
                summary_df["Datasets"].str.split(",", expand=True)[0].str.strip().eq(selected_tab)
            ]
            if filtered_summary.empty:
                # Display message for no checks
                content.append(
                    html.Div(
                        "No checks were written for this domain.",
                        style={
                            "text-align": "center",
                            "font-size": "18px",
                            "color": "#cd25b7",
                            "margin": "20px",
                            "font-weight": "bold",
                        },
                    )
                )
                # Add a horizontal line
                content.append(html.Hr(style={"border": "1px solid #A2D2A2", "margin": "20px 0"}))
    
            
            passed_checks = filtered_summary[filtered_summary["Message"] == "Pass"]
            failed_checks = filtered_summary[filtered_summary["Message"] != "Pass"]

            #if passed_checks.empty and failed_checks.empty:
                #content.append(html.Div(f"No checks were written for this domain.", style={"text-align": "center", "font-size": "18px", "color": "#333"}))
                #return content
            if not passed_checks.empty:
                pass_card = html.Div(
                    [
                        html.H3("Pass", style={"color": "#2E8B57", "font-weight": "bold", "text-align": "center"}),
                        html.Table(
                            [
                                html.Tr(
                                    [
                                        html.Th("Check", style={"padding": "8px", "text-align": "center", "fontWeight": "bold"}),
                                        html.Th("Message", style={"padding": "8px", "text-align": "center", "fontWeight": "bold"}),
                                        html.Th("Datasets", style={"padding": "8px", "text-align": "center", "fontWeight": "bold"}),
                                    ]
                                )
                            ]
                            + [
                                html.Tr(
                                    [
                                        html.Td(row["CHECK"], style={"padding": "8px"}),
                                        html.Td(row["Message"], style={"padding": "8px"}),
                                        html.Td(row["Datasets"], style={"padding": "8px"}),
                                    ]
                                )
                                for _, row in passed_checks.iterrows()
                            ],
                            style={"width": "100%", "border-collapse": "collapse", "table-layout": "fixed"},
                        ),
                    ],
                    style={
                        "border": "2px solid #A2D2A2",
                        "border-radius": "8px",
                        "padding": "15px",
                        "margin": "10px",
                        "backgroundColor": "#E8F5E9",
                        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)",
                        "width": "48%",
                        "display": "inline-block",
                        "vertical-align": "top",
                    },
                )
            else:
                pass_card = None

            # Fail Card
            if not failed_checks.empty:
                fail_card = html.Div(
                    [
                        html.H3("Fail / Warnings", style={"color": "#FF0000", "font-weight": "bold", "text-align": "center"}),
                        html.Table(
                            [
                                html.Tr(
                                    [
                                        html.Th("Check", style={"padding": "8px", "text-align": "center", "fontWeight": "bold"}),
                                        html.Th("Message", style={"padding": "8px", "text-align": "center", "fontWeight": "bold"}),
                                        html.Th("Datasets", style={"padding": "8px", "text-align": "center", "fontWeight": "bold"}),
                                    ]
                                )
                            ]
                            + [
                                html.Tr(
                                    [
                                        html.Td(row["CHECK"], style={"padding": "8px"}),
                                        html.Td(
                                            row["Message"],
                                            style={
                                                "padding": "8px",
                                                "color": "#FF0000" if "Fail" in row["Message"] else "#333333",
                                                "animation": "blinking 1.5s infinite" if "Fail" in row["Message"] else "",
                                            },
                                        ),
                                        html.Td(row["Datasets"], style={"padding": "8px"}),
                                    ]
                                )
                                for _, row in failed_checks.iterrows()
                            ],
                            style={"width": "100%", "border-collapse": "collapse", "table-layout": "fixed"},
                        ),
                    ],
                    style={
                        "border": "2px solid #FF0000",
                        "border-radius": "8px",
                        "padding": "15px",
                        "margin": "10px",
                        "backgroundColor": "#FFEBEE",
                        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)",
                        "width": "48%",
                        "display": "inline-block",
                        "vertical-align": "top",
                    },
                )
            else:
                fail_card = None
            # Combine Pass and Fail Cards
            cards = [card for card in [pass_card, fail_card] if card]
            content.append(
                html.Div(
                    cards,
                    style={"text-align": "center", "display": "flex", "gap": "4%", "justify-content": "center"},
                )
            )

            detail_content = []
            
            for _, row in filtered_summary.iterrows():
                if row["CHECK"] in detailed_data:
                    detail_content.append(
                        html.Div([
                            html.H3(f"Details for {row['CHECK']}", style={"color": "#FF0000", "font-weight": "bold", "text-align": "center"}),
                            dag.AgGrid(
                                rowData=detailed_data[row["CHECK"]].to_dict('records'),
                                columnDefs=[
                                    {"headerName": col, "field": col} for col in detailed_data[row["CHECK"]].columns
                                ],
                                defaultColDef={
                                    "sortable": True,
                                    "filter": True,
                                    "resizable": True,
                                    "editable": False,
                                    "cellStyle": {
                                        "color": "#333333",
                                        "fontSize": "14px",
                                        "border": "1px solid #A3D3A3",
                                        "backgroundColor": "#F9F9F9"
                                    },
                                },
                                style={"height": "400px", "width": "100%"}
                            )
                        ])
                    )

            # Append the detailed data tables to the content only if there are entries
            if detail_content:
                content.extend(detail_content)

                          
            # Add dataset-specific content, like DM, AE, LB plots
            if selected_tab == "DM":
                content.extend(generate_dm_plots(data_path))
            elif selected_tab == "AE":
                content.extend(generate_ae_plots(data_path))
            elif selected_tab == "SV":
                content.extend(subject_compliance_plot(data_path))
                content.extend(visit_timing_distribution_plot(data_path))
                content.extend(visit_sequence_plot(data_path))
                #content.extend(cumulative_visit_completion_plot(data_path))
                content.extend(subject_dropout_analysis_plot(data_path))
                
            elif selected_tab == "DS":
                content.extend(comp_status_dis(data_path))
                content.extend(study_status_arm(data_path))
                content.extend(dispo_time(data_path))
                content.extend(sub_stat_epoch(data_path))
                content.extend(dispo_event(data_path))
                content.extend(dispo_reas(data_path))
            elif selected_tab == "EX":
                print('selected tab', selected_tab) 
                content.extend(dose_overtime(data_path))
                content.extend(dose_cumdose(data_path))

            elif selected_tab == "SE":
                #print('selected tab', selected_tab)    
                content.extend(subject_timeline(data_path))
                content.extend(subject_time_spent(data_path))
                #content.extend(subject_duration(data_path))
                content.extend(study_elements(data_path))
                
            elif selected_tab == "SS":
                content.extend(surv_dist(data_path))
                    
            if dataset_df.empty:
                content.append(html.Div(f"No data found for {selected_tab}."))
                return content
            normalized_columns = [col.strip().upper() for col in dataset_df.columns]
            test_columns = [col for col, normalized_col in zip(dataset_df.columns, normalized_columns) if normalized_col.endswith("TEST")]
            value_columns = [col for col, normalized_col in zip(dataset_df.columns, normalized_columns) if normalized_col.endswith("STRESN")]

            if test_columns and value_columns:
                        test_column = test_columns[0]  # Use the first matching column
                        test_options = [{"label": test, "value": test} for test in dataset_df[test_column].unique()]
                        # Add dropdown for the detected test column
                        dropdown_id = {'type': 'test-dropdown', 'index': selected_tab}
                        plot_id = {'type': 'test-plot', 'index': selected_tab}

                        content.append(
                            html.H3(
                                "Mean plots for Data Review",
                                style={
                                    "font-size": "20px",          # Slightly larger font for emphasis
                                    "font-weight": "bold",        # Bold text
                                    "color": "#4B0082",           # Indigo color for contrast
                                    "text-align": "center",       # Center-align the heading
                                    "margin-bottom": "15px",      # Add spacing below the heading
                                }
                            )
                        )

                        content.append(
                            html.Label(
                                f"Select {test_column} to view mean plot",
                                style={
                                    "font-size": "16px",          # Regular font size
                                    "font-weight": "bold",        # Bold text for consistency
                                    "color": "#2E8B57",           # Green color for emphasis
                                    "margin-bottom": "10px",      # Space below the label
                                    "display": "block",           # Full-width block display
                                    "text-align": "left",       # Center-align the label
                                }
                            )
                        )
                        content.append(dcc.Dropdown(
                            id=dropdown_id, 
                            options=test_options,
                            value=test_options[0]["value"] if test_options else None,
                            clearable=False,
                            style={"width": "50%"}
                        ))

                        # Add placeholder for the plot
                        content.append(html.Div(id=plot_id))
    # Return content to display on the tab
    return content
@app.callback(
    Output("filtered-dataset", "children"),
    [
        Input("usubjid-dropdown", "value"),
        Input("dataset-tabs", "value"),
        State("project-dropdown", "value"),
        State("study-dropdown", "value"),
        State('analysis-folder-dropdown', 'value')
    ]
)

def update_filtered_dataset(selected_usubjid, selected_dataset, selected_project, selected_study, selected_analysis_folder):
    # Ensure all required values are provided
    if not selected_usubjid or not selected_dataset or not selected_project or not selected_study:
        raise PreventUpdate

    # Define the data path
    data_path = f"{base_dir}/{selected_project}/{selected_study}/{selected_analysis_folder}"

    # Load the dataset and filter based on USUBJID
    dataset_df = load_data(data_path, selected_dataset)
    filtered_df = dataset_df[dataset_df["USUBJID"] == selected_usubjid]

    # Return the filtered dataset
    if not filtered_df.empty:
        return dag.AgGrid(
            rowData=filtered_df.to_dict('records'),
            columnDefs=[{"headerName": col, "field": col} for col in filtered_df.columns],
            defaultColDef={
                "sortable": True,
                "filter": True,
                "resizable": True,
                "editable": False,
                "cellStyle": {
                    "color": "#333333",
                    "fontSize": "14px",
                    "border": "1px solid #A2D2A2",
                    "backgroundColor": "#F9F9F9"
                },
            },
            style={"height": "600px", "width": "100%"}
        )
    else:
        return html.Div("No data found for the selected USUBJID.")

@app.callback(
    Output({'type': 'test-plot', 'index': MATCH}, "children"),
    [
        Input({'type': 'test-dropdown', 'index': MATCH}, "value"),
        State("project-dropdown", "value"),
        State("study-dropdown", "value"),
        State("analysis-folder-dropdown", "value"),
        State({'type': 'test-dropdown', 'index': MATCH}, 'id')  # Include dropdown ID
    ]
)
def update_test_plot(selected_test, selected_project, selected_study, selected_analysis_folder, dropdown_id):
    if not selected_project or not selected_study or not selected_analysis_folder:
        raise PreventUpdate

    # Extract dataset name from the dropdown ID
    dataset = dropdown_id['index']

    # Load the dataset
    data_path = f"{base_dir}/{selected_project}/{selected_study}/{selected_analysis_folder}"

    df = load_data(data_path, dataset)
    normalized_columns = [col.strip().upper() for col in df.columns]
    test_columns = [col for col, normalized_col in zip(df.columns, normalized_columns) if normalized_col.endswith("TEST") ]
    value_columns = [col for col, normalized_col in zip(df.columns, normalized_columns) if normalized_col.endswith("STRESN")]
    #print('testing cols', test_columns)
    if  test_columns and value_columns:
        #return html.Div(f"No column ending with 'TEST' found in {dataset}.")

        test_col = test_columns[0]  # Use the first matching column

        # Dynamically detect the value column ending with "STRESN"
        value_columns = [col for col, normalized_col in zip(df.columns, normalized_columns) if normalized_col.endswith("STRESN")]

        if not value_columns:
            return html.Div(f"No column ending with 'STRESN' found in {dataset}.")

        value_col = value_columns[0]  # Use the first detected value column

        # Generate the plot
        return generate_test_plot(
            df=df,
            test_value=selected_test,
            test_col=test_col,    
            visit_col_n="VISITNUM",
            visit_col="VISIT"
        )
@app.callback(
    Output("narrative-content", "children"),
    Input("narrative-usubjid-dropdown", "value"),
    [State('project-dropdown', 'value'), State('study-dropdown', 'value'), State('analysis-folder-dropdown', 'value')]
)
def update_narrative(selected_usubjid, selected_project, selected_study, selected_analysis_folder):
    if not selected_usubjid or not selected_project or not selected_study:
        raise PreventUpdate

    # Define paths
    data_path = f"{base_dir}/{selected_project}/{selected_study}/{selected_analysis_folder}"
    spec_path = f"{base_dir}/{selected_project}/{selected_study}/{selected_analysis_folder}/_csdtm_dev_sdtm_mapping.xlsx"

    # Step 1: Load specifications to get the dataset order
    try:
        study_info, standards_df, combined_df = specs_transform(spec_path)
        #filtered_specs = combined_df[combined_df["Class"] != "TRIAL DESIGN"]
        filtered_specs = combined_df[combined_df["Class"].str.upper() != "TRIAL DESIGN"]  # Exclude "TRIAL DESIGN"
        unique_sheets = filtered_specs["Dataset"].str.upper().unique().tolist()  # Normalize to uppercase
        trial_design_datasets = combined_df[combined_df["Class"].str.upper() == "TRIAL DESIGN"]["Dataset"].str.upper().unique().tolist()
        
        #print("Unique Sheets from Specifications:", unique_sheets)
       #print("Trial Design Datasets to Exclude:", trial_design_datasets)

        # Step 2: Load datasets dynamically from the directory
        dataset_files = [
            f for f in os.listdir(data_path) 
            if f.endswith('.sas7bdat') 
            and not f.lower().startswith('supp')
            and os.path.splitext(f)[0].upper() not in trial_design_datasets
        ]
        dataset_names = [os.path.splitext(f)[0].upper() for f in dataset_files]

        datasets = {
            dataset_name: load_data(data_path, dataset_name)
            for dataset_name in dataset_names
        }

        #print("Dataset Names from Directory:", dataset_names)
        #print("Loaded Datasets:", datasets.keys())

        # Step 3: Order datasets based on specifications
        ordered_datasets = {name: datasets[name] for name in unique_sheets if name in datasets}
        #print("Ordered Datasets:", ordered_datasets.keys())
    except Exception as e:
        return html.Div(f"Error loading datasets: {str(e)}", style={"color": "red", "font-weight": "bold"})

    # Step 4: Filter and display data for the selected USUBJID
    grid_content = []
    missing_domains = []
    
    for dataset_name, df in ordered_datasets.items():
        filtered_df = df[df["USUBJID"] == selected_usubjid]
        if not filtered_df.empty:
            narrative_text = generate_domain_narrative(dataset_name, filtered_df)
            grid_content.append(html.Div([
                html.H4(f"Dataset: {dataset_name}", style={"text-align": "center", "color": "#2E8B57"}),
                html.Div(
                    narrative_text, 
                    style={
                        "whiteSpace": "pre-wrap", 
                        "border": "1px solid #ccc", 
                        "padding": "10px", 
                        "margin-bottom": "10px", 
                         "fontFamily": "Calibri, sans-serif",
                        "fontSize": "16px"
                    }
                ),
          

                dag.AgGrid(
                    rowData=filtered_df.to_dict('records'),
                    columnDefs=[{"headerName": col, "field": col} for col in filtered_df.columns],
                    defaultColDef={
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "editable": False,
                        "cellStyle": {
                            "color": "#333333",
                            "fontSize": "14px",
                            "border": "1px solid #A2D2A2",
                            "backgroundColor": "#F9F9F9"
                        },
                    },
                    style={"height": "400px", "width": "100%", "margin-bottom": "20px"}
                )
            ]))
        else:
            missing_domains.append(dataset_name)

    # Step 5: Display missing domains
    if missing_domains:
        grid_content.append(html.Div([
            html.H4("No Data Found for Selected USUBJID in the Following Domains:", 
                    style={"text-align": "center", "color": "red", "font-weight": "bold"}),
            html.Ul([html.Li(domain, style={"text-align": "center", "color": "#CD5C5C", "font-weight": "bold"}) 
                     for domain in missing_domains])
        ]))

    # Step 6: Handle case where no data is found in any domain
    if not grid_content:
        return html.Div(
            "No data found for the selected USUBJID across all datasets.",
            style={"color": "red", "text-align": "center", "font-weight": "bold"}
        )

    return html.Div(grid_content)

if __name__ == '__main__':
    app.run_server(debug=True)
    
