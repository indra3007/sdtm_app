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
from dash.dependencies import Input, Output, State
import dash_ag_grid as dag
from dash import dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate

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
                       check_ds_sc_strat
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
                       check_lb_missing_month,
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
    return summary_df, detailed_data



# Initialize app
# Initialize app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
base_dir = "G:/projects"

# Helper functions to get projects and studies dynamically
def get_projects():
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

def get_studies(project):
    project_path = os.path.join(base_dir, project)
    return [d for d in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, d))]

# Main layout of the app with improved styling
app.layout = html.Div([
    html.H1("SDTM Quality Checks", style={
        "color": "#2E8B57", 
        "font-weight": "bold", 
        "text-align": "center", 
        "margin-bottom": "20px"}), 

    # Project and Study selection with custom styling
    html.Div([
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
        ], style={"width": "45%", "display": "inline-block", "vertical-align": "top", "margin-right": "5%"}),

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
        ], style={"width": "45%", "display": "inline-block", "vertical-align": "top"}),
    ], style={"display": "flex", "justify-content": "center", "margin-bottom": "20px"}),

    # Run checks button
    html.Div([
        html.Button("Run Checks", id="run-checks-button", n_clicks=0, style={
            "background-color": "#2E8B57", "color": "white", "border": "none", 
            "border-radius": "8px", "padding": "10px 20px", "font-size": "16px",
            "font-weight": "bold", "cursor": "pointer"
        })
    ], style={"text-align": "center", "margin-bottom": "20px"}),

    # Tabs container
    html.Div(id='tabs-container', style={"margin-bottom": "20px"}),

    # Content area for selected tab with additional styling
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

# Callback to generate tabs and data path after "Run Checks" is clicked
@app.callback(
    [Output('tabs-container', 'children')],
    [Input('run-checks-button', 'n_clicks')],
    [State('project-dropdown', 'value'), State('study-dropdown', 'value')]
)
def run_checks_and_display_tabs(n_clicks, selected_project, selected_study):
    if not selected_project or not selected_study or n_clicks == 0:
        raise PreventUpdate

    data_path = f"{base_dir}/{selected_project}/{selected_study}/csdtm_dev/draft1/sdtmdata"
    global summary_df, detailed_data
    summary_df, detailed_data = run_checks(data_path)
    
    unique_datasets = set(
        sum([ds.split(",") for ds in summary_df["Datasets"].dropna()], [])  # Split by comma only
    )
    unique_datasets = {ds.strip() for ds in unique_datasets if ds}  
    available_datasets = sorted(
        set(os.path.splitext(f)[0].upper() for f in os.listdir(data_path)
            if f.endswith('.sas7bdat') and not f.lower().startswith('supp'))
    )
    all_datasets = sorted(unique_datasets | set(available_datasets))
    all_datasets.insert(0, "Full Summary")

# Generate tabs with improved styling to prevent truncation
    tabs = dcc.Tabs(
        id="dataset-tabs",
        value="Full Summary",
        children=[
            dcc.Tab(
                label=dataset,
                value=dataset,
                style={
                    "backgroundColor": "#f7f7f7",
                    "borderRadius": "8px",
                    "padding": "10px 15px",  # Padding for spacing around text
                    "margin": "5px",
                    "fontWeight": "bold",
                    "color": "#2E8B57",
                    "whiteSpace": "nowrap",  # Ensure the text doesn't wrap
                    "overflow": "visible",  # Prevent clipping of text
                    "width": "auto",  # Adjust width to the content size
                    "display": "inline-block",  # Fit box to text size
                    "textAlign": "center",  # Center-align text
                    "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)",
                },
                selected_style={
                    "backgroundColor": "#2E8B57",
                    "color": "white",
                    "fontWeight": "bold",
                    "borderRadius": "8px",
                    "padding": "10px 15px",
                    "margin": "5px",
                    "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.2)",
                },
            )
            for dataset in all_datasets
        ],
        style={
            "display": "flex",
            "flexWrap": "wrap",  # Allow tabs to wrap to the next line
            "justifyContent": "center",
            "borderBottom": "2px solid #A2D2A2",
            "margin": "10px 0",
        },
    )


    return [tabs]

# Callback to render content in each tab
@app.callback(
    Output('tab-content', 'children'),
    [Input('dataset-tabs', 'value')],
    [State('project-dropdown', 'value'), State('study-dropdown', 'value')]
)
def render_tab_content(selected_dataset, selected_project, selected_study):
    if not selected_dataset or not selected_project or not selected_study:
        raise PreventUpdate

    data_path = f"{base_dir}/{selected_project}/{selected_study}/csdtm_dev/draft1/sdtmdata"
    content = []

    # Display "Full Summary" if selected
    if selected_dataset == "Full Summary":
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
        dataset_df = load_data(data_path, selected_dataset)  # Placeholder function to load dataset
        if dataset_df.empty:
            content.append(html.Div(f"No data found for {selected_dataset}."))
        else:
            # Dropdown for filtering by USUBJID if in DM dataset
            if  "USUBJID" in dataset_df.columns:
                usubjid_options = [{"label": usubjid, "value": usubjid} for usubjid in dataset_df["USUBJID"].unique()]
                content.append(html.Label("Select USUBJID to filter across datasets"))
                content.append(dcc.Dropdown(id="usubjid-dropdown", options=usubjid_options, style={"width": "50%"}))
                content.append(html.Div(id="filtered-dataset"))

            # Display full dataset
            content.append(html.H2(f"{selected_dataset} - Full Dataset"))
            content.append(
                dag.AgGrid(
                    rowData=dataset_df.to_dict('records'),
                    columnDefs=[{"headerName": col, "field": col} for col in dataset_df.columns],
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
            )

            # Display summary checks
            filtered_summary = summary_df[summary_df["Datasets"].str.contains(selected_dataset, na=False)]
            if not filtered_summary.empty:
                content.append(html.H2(f"{selected_dataset} - Summary Checks"))
                content.append(
                    dag.AgGrid(
                        rowData=filtered_summary.to_dict('records'),
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
                                "border": "1px solid #A3D3A3",
                                "backgroundColor": "#F9F9F9"
                            },
                        },
                        style={"height": "300px", "width": "100%"}
                    )
                )
            detail_content = []
            for _, row in filtered_summary.iterrows():
                if row["CHECK"] in detailed_data:
                    detail_content.append(
                        html.Div([
                            html.H3(f"Details for {row['CHECK']}"),
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
            if selected_dataset == "DM":
                content.extend(generate_dm_plots(data_path))
            elif selected_dataset == "AE":
                content.extend(generate_ae_plots(data_path))
            elif selected_dataset == "LB":
                # Load LB data
                lb_df = load_data(data_path, 'lb')

                # Ensure LBTEST column exists in the data
                if "LBTEST" in lb_df.columns:
                    # Add dropdown for LBTEST selection and plot placeholder
                    lbtest_options = [{"label": lbtest, "value": lbtest} for lbtest in lb_df["LBTEST"].unique()]
                    content.append(html.Label("Select LBTEST to view mean plot"))
                    content.append(dcc.Dropdown(
                        id="lbtest-dropdown",
                        options=lbtest_options,
                        value=lbtest_options[0]["value"] if lbtest_options else None,
                        clearable=False,
                        style={"width": "50%"}
                    ))
                    content.append(html.Div(id="lbtest-plot"))
                else:
                    content.append(html.Div("LBTEST column not found in the data."))
    
    # Return content to display on the tab
    return content
@app.callback(
    Output("filtered-dataset", "children"),
    [
        Input("usubjid-dropdown", "value"),
        Input("dataset-tabs", "value"),
        State("project-dropdown", "value"),
        State("study-dropdown", "value")
    ]
)
def update_filtered_dataset(selected_usubjid, selected_dataset, selected_project, selected_study):
    # Ensure all required values are provided
    if not selected_usubjid or not selected_dataset or not selected_project or not selected_study:
        raise PreventUpdate

    # Define the data path
    data_path = f"{base_dir}/{selected_project}/{selected_study}/csdtm_dev/draft1/sdtmdata"

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
# Callback to update the LBTEST plot based on the selected LBTEST value
@app.callback(
    Output("lbtest-plot", "children"),
    [Input("lbtest-dropdown", "value"), State("project-dropdown", "value"), State("study-dropdown", "value")]
)
def update_lbtest_plot(selected_lbtest, selected_project, selected_study):
    if not selected_project or not selected_study:
        raise PreventUpdate

    data_path = f"{base_dir}/{selected_project}/{selected_study}/csdtm_dev/draft1/sdtmdata"
    lb_df = load_data(data_path, 'LB')

    if not selected_lbtest or lb_df.empty:
        return html.Div("Select a parameter to view the plot.")
    
    return generate_lbtest_plot(lb_df, selected_lbtest)  # Replace with your plotting function


if __name__ == '__main__':
    app.run_server(debug=True)
    
