


# Extract unique dataset names from data_path, excluding files that start with 'supp'
available_datasets = sorted(
    set(os.path.splitext(f)[0].upper() for f in os.listdir(data_path)
        if f.endswith('.sas7bdat') and not f.lower().startswith('supp'))
)

# Add "Full Summary" as the first (default) tab
available_datasets.insert(0, "Full Summary")

# Layout with tabs for each unique dataset
app.layout = html.Div([
    html.H1("SDTM Quality Checks", style={"color": "#2E8B57", "font-weight": "bold"}),  # Page title styling
    
    # Tabs for each unique dataset with "Full Summary" as the default tab
    dcc.Tabs(id="dataset-tabs", value="Full Summary", children=[
        dcc.Tab(label=dataset, value=dataset, style={
            "backgroundColor": "#D5E8D4", 
            "border": "1px solid #A2D2A2", 
            "padding": "10px",
            "fontWeight": "bold",
            "color": "#2E8B57",
        }) for dataset in available_datasets
    ], style={"borderBottom": "2px solid #A2D2A2", "margin": "10px 0"}),
    
    # Content area for the selected tab with additional styling
    html.Div(id='tab-content', style={
        "border": "2px solid #A2D2A2", 
        "border-radius": "10px", 
        "padding": "20px",
        "backgroundColor": "#ffffff",
        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)"
    })
], style={"maxWidth": "2000px", "margin": "auto"})  # Center the entire layout on the page

# Function to load a specific dataset
def load_data(data_path, dataset_name):
    """Load a dataset from data_path based on dataset_name."""
    file_path = os.path.join(data_path, f"{dataset_name.lower()}.sas7bdat")
    if os.path.exists(file_path):
        return pd.read_sas(file_path)
    else:
        return pd.DataFrame()  # Return an empty DataFrame if the file doesn't exist

# Callback to update content based on selected tab
@app.callback(
    Output('tab-content', 'children'),
    Input('dataset-tabs', 'value')
)
def render_tab_content(selected_dataset):
    # Default to "Full Summary" if selected_dataset is None
    if selected_dataset is None:
        selected_dataset = "Full Summary"
    
    # Ensure content is initialized as a list of Dash components
    content = []

    # Display the entire summary table if "Full Summary" is selected
    if selected_dataset == "Full Summary":
        filtered_summary = summary_df  # Display all data
        content = [
            html.H2("Full Summary Table"),
            dag.AgGrid(
                rowData=filtered_summary.to_dict('records'),  # Ensure this is a list of dicts
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
                        "color": "#333333",  # Text color
                        "fontSize": "14px",  # Font size
                        "border": "1px solid #A2D2A2",  # Cell border
                        "backgroundColor": "#F9F9F9"   # Light background for cells
                    },
                },
                style={"height": "300px", "width": "100%"}
            )
        ]
    
    else:
        # Display the relevant checks from summary_df
        filtered_summary = summary_df[summary_df["Datasets"].str.contains(selected_dataset, na=False)]
        content = [
            html.H2(f"{selected_dataset} - Summary Table"),
            dag.AgGrid(
                rowData=filtered_summary.to_dict('records'),  # Ensure this is a list of dicts
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
                        "color": "#333333",  # Text color
                        "fontSize": "14px",  # Font size
                        "border": "1px solid #A2D2A2",  # Cell border
                        "backgroundColor": "#F9F9F9"   # Light background for cells
                    },
                },
                style={"height": "300px", "width": "100%"}
            )
        ]
        
        # Load and display the full dataset if the selected tab matches a dataset in data_path
        dataset_df = load_data(data_path, selected_dataset)
        content.append(html.H2(f"{selected_dataset} - Full Dataset"))

        if not dataset_df.empty:
            # Display the full dataset in AgGrid
            content.append(
                dag.AgGrid(
                    rowData=dataset_df.to_dict('records'),  # Ensure this is a list of dicts
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
        else:
            # Display a message if no data is found
            content.append(html.Div(f"No data found for {selected_dataset}."))

    return content
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Extract unique dataset names for tabs, and add a "Full Summary" tab for all datasets
unique_datasets = sorted(set(d for datasets in summary_df["Datasets"] for d in datasets.split(",") if d.strip()))
unique_datasets.insert(0, "Full Summary")  # Add "Full Summary" as the first (default) tab

# Layout with tabs for each unique dataset
app.layout = html.Div([
    html.H1("SDTM Quality Checks", style={"color": "#2E8B57", "font-weight": "bold"}),  # Page title styling
    
    # Tabs for each unique dataset with "Full Summary" as the default tab
    dcc.Tabs(id="dataset-tabs", value="Full Summary", children=[
        dcc.Tab(label=dataset, value=dataset, style={
            "backgroundColor": "#D5E8D4", 
            "border": "1px solid #A2D2A2", 
            "padding": "10px",
            "fontWeight": "bold",
            "color": "#2E8B57",
        }) for dataset in unique_datasets
    ], style={"borderBottom": "2px solid #A2D2A2", "margin": "10px 0"}),
    
    # Content area for the selected tab with additional styling
    html.Div(id='tab-content', style={
        "border": "2px solid #A2D2A2", 
        "border-radius": "10px", 
        "padding": "20px",
        "backgroundColor": "#ffffff",
        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)"
    })
], style={"maxWidth": "2000px", "margin": "auto"})  # Center the entire layout on the page

# Callback to update content based on selected tab
@app.callback(
    Output('tab-content', 'children'),
    Input('dataset-tabs', 'value')
)
def render_tab_content(selected_dataset):
    # Default to "Full Summary" if selected_dataset is None
    if selected_dataset is None:
        selected_dataset = "Full Summary"

    # Initialize the content list
    content = []

    # 1. Display "Full Summary" if selected
    if selected_dataset == "Full Summary":
        if summary_df.empty:
            content.append(html.Div("No summary data available."))
        else:
            content.append(html.H2("Full Summary Table"))
            content.append(
                dag.AgGrid(
                    rowData=summary_df.to_dict('records'),
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
                    style={"height": "300px", "width": "100%"}
                )
            )
    else:
        # 2. Display the full dataset for the selected tab
        dataset_df = load_data(data_path, selected_dataset)
        if dataset_df.empty:
            content.append(html.Div(f"No data found for {selected_dataset}."))
        else:
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

        # 3. Display summary checks for the selected dataset
        filtered_summary = summary_df[summary_df["Datasets"].str.contains(selected_dataset, na=False)]

        # Debug: Print filtered summary content
        print(f"Filtered Summary for {selected_dataset}:\n", filtered_summary)

        if filtered_summary.empty:
            content.append(html.Div(f"No summary checks found for {selected_dataset}."))
        else:
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
                            "border": "1px solid #FF0000",
                            "backgroundColor": "#F9F9F9"
                        },
                    },
                    style={"height": "300px", "width": "100%"}
                )
            )

        # 4. Display detailed checks if present in `detailed_data`
        detail_content = []
        for _, row in filtered_summary.iterrows():
            check_name = row["CHECK"]
            if check_name in detailed_data and not detailed_data[check_name].empty:
                detail_content.append(html.H3(f"Details for {check_name}"))
                detail_content.append(
                    dag.AgGrid(
                        rowData=detailed_data[check_name].to_dict('records'),
                        columnDefs=[{"headerName": col, "field": col} for col in detailed_data[check_name].columns],
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
                )

        # Append detailed data if available
        if detail_content:
            content.extend(detail_content)
        else:
            content.append(html.Div("No detailed checks available."))

        # 5. Add dataset-specific plots, if applicable
        if selected_dataset == "DM":
            plots = generate_dm_plots(data_path)
            print(f"DM Plots for {selected_dataset}: ", plots)
            if plots:
                content.extend(plots)
            else:
                content.append(html.Div("No DM plots available."))
        elif selected_dataset == "AE":
            plots = generate_ae_plots(data_path)
            print(f"AE Plots for {selected_dataset}: ", plots)
            if plots:
                content.extend(plots)
            else:
                content.append(html.Div("No AE plots available."))
        elif selected_dataset == "LB":
            lb_df = load_data(data_path, 'lb')
            if "LBTEST" in lb_df.columns:
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





app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Base directory where all projects are located
base_dir = "G:/projects"

# Helper function to list all projects and studies dynamically
def get_projects():
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

def get_studies(project):
    project_path = os.path.join(base_dir, project)
    return [d for d in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, d))]

def load_data(data_path, dataset_name):
    # Replace with the actual logic to load datasets based on dataset_name
    # For demonstration, we return a sample DataFrame
    return pd.DataFrame({"USUBJID": ["01", "02"], "VAR1": [10, 20], "VAR2": ["A", "B"]})

# Layout for the app with dropdowns for project and study selection
app.layout = html.Div([
    html.H1("SDTM Quality Checks", style={"color": "#2E8B57", "font-weight": "bold"}),  # Page title styling
    
    # Project selection dropdown
    html.Label("Select Project"),
    dcc.Dropdown(
        id="project-dropdown",
        options=[{"label": proj, "value": proj} for proj in get_projects()],
        placeholder="Select a project",
        clearable=False,
        style={"width": "50%", "margin-bottom": "10px"}
    ),
    
    # Study selection dropdown, updated based on selected project
    html.Label("Select Study"),
    dcc.Dropdown(
        id="study-dropdown",
        placeholder="Select a study",
        clearable=False,
        style={"width": "50%", "margin-bottom": "10px"}
    ),
    
    # Tabs container, dynamically generated after project and study are selected
    html.Div(id='tabs-container'),
    
    # Content area for selected tab
    html.Div(id='tab-content', style={
        "border": "2px solid #A2D2A2", 
        "border-radius": "10px", 
        "padding": "20px",
        "backgroundColor": "#ffffff",
        "boxShadow": "0px 4px 8px rgba(0, 0, 0, 0.1)"
    })
])

# Callback to populate study dropdown based on selected project
@app.callback(
    Output('study-dropdown', 'options'),
    Input('project-dropdown', 'value')
)
def update_study_dropdown(selected_project):
    if not selected_project:
        raise PreventUpdate
    studies = get_studies(selected_project)
    return [{"label": study, "value": study} for study in studies]

# Callback to display tabs after project and study are selected
@app.callback(
    Output('tabs-container', 'children'),
    [Input('project-dropdown', 'value'), Input('study-dropdown', 'value')]
)
def display_tabs(selected_project, selected_study):
    if not selected_project or not selected_study:
        raise PreventUpdate
    
    # Construct dynamic data path based on selected project and study
    data_path = f"{base_dir}/{selected_project}/{selected_study}/csdtm_dev/draft1/sdtmdata"
    
    # Find available datasets in the data path
    available_datasets = sorted(
        set(os.path.splitext(f)[0].upper() for f in os.listdir(data_path)
            if f.endswith('.sas7bdat') and not f.lower().startswith('supp'))
    )
    available_datasets.insert(0, "Full Summary")  # Add "Full Summary" as the first (default) tab
    
    # Create tabs for each dataset
    return dcc.Tabs(id="dataset-tabs", value="Full Summary", children=[
        dcc.Tab(label=dataset, value=dataset, style={
            "backgroundColor": "#D5E8D4", 
            "border": "1px solid #A2D2A2", 
            "padding": "10px",
            "fontWeight": "bold",
            "color": "#2E8B57",
        }) for dataset in available_datasets
    ], style={"borderBottom": "2px solid #A2D2A2", "margin": "10px 0"})

# Callback to update the content for each tab
@app.callback(
    Output('tab-content', 'children'),
    [Input('dataset-tabs', 'value'), State('project-dropdown', 'value'), State('study-dropdown', 'value')]
)
def render_tab_content(selected_dataset, selected_project, selected_study):
    if not selected_project or not selected_study:
        raise PreventUpdate
    
    # Construct the data path
    data_path = f"{base_dir}/{selected_project}/{selected_study}/csdtm_dev/draft1/sdtmdata"
    
    # Initialize content list
    content = []

    # Display "Full Summary" if selected
    if selected_dataset == "Full Summary":
        content.append(html.H2("Full Summary Table"))
        # Placeholder for summary data display
        content.append(html.Div("Summary Data Will Go Here"))
        
    else:
        # Load and display dataset
        dataset_df = load_data(data_path, selected_dataset)
        content.append(html.H2(f"{selected_dataset} - Full Dataset"))
        
        # Display dataset in AgGrid
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

    return content
