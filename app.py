from dash import Dash, html, Input, Output, dcc
import dash_ag_grid as dag
import pandas as pd
from datetime import datetime
from connection import get_engine
from dash.dependencies import State
from dash import dcc, html
import dash
from openpyxl import load_workbook
import os
from flask import jsonify


external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",  # Bootstrap CSS
    "https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css",  # Bootstrap Icons
]
# Initialize the Dash app with external stylesheets
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)
server = app.server

# Add external stylesheets (e.g., Bootstrap and Bootstrap Icons)


# Fetch the table from the SQL database
def fetch_summary_table():
    try:
        engine = get_engine()
        query = "SELECT * FROM Quality_checks_combined"
        with engine.connect() as connection:
            summary_df = pd.read_sql(query, connection)
        print("Summary table fetched successfully!")
        return summary_df
    except Exception as e:
        print(f"Error fetching summary table: {e}")
        return pd.DataFrame()


# Fetch the summary table
summary_df = fetch_summary_table()


@app.server.route("/open-folder", methods=["POST"])
def open_folder():
    import json
    from flask import request

    # Get the folder path from the request
    data = json.loads(request.data)
    folder_path = data.get("folder_path")
    print(f"Attempting to open folder: {folder_path}")  # Debugging

    if folder_path and os.path.exists(folder_path):
        try:
            os.startfile(folder_path)  # Open the folder in Windows Explorer
            return jsonify(
                {"success": True, "message": f"Opened folder: {folder_path}"}
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    return jsonify(
        {"success": False, "message": "Invalid folder path or folder does not exist."}
    )


# Add a "Date" column for demonstration purposes
summary_df["Date"] = datetime.today().strftime("%Y-%m-%d")
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),  # Tracks the current page
        dcc.Store(id="store-selected-protocol"),  # Store for selected_protocol
        dcc.Store(id="store-selected-project"),  # Store for selected_project
        html.Div(id="page-content"),  # Content of the current page
    ]
)
# App layout
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),  # Tracks the current page
        html.Div(id="page-content"),  # Content of the current page
    ]
)


def header():
    return html.Div(
        [
            html.Div(
                [
                    html.Img(
                        src="/assets/gilead_logo.png",  # Path to the logo in the assets folder
                        className="logo",
                    ),
                    html.Div("cSDTM Quality Checks", className="header-title"),
                ],
                className="header-container",
            )
        ]
    )


def home_section():
    return html.Div(
        [
            html.A(
                html.Button(
                    [html.I(className="bi bi-house"), " Home"],  # Icon and text
                    className="home-button",
                ),
                href="/",
                className="home-link",
            ),
            dcc.Link(
                html.Button(
                    [html.I(className="bi bi-arrow-left"), " Back"],  # Icon and text
                    className="back-button",
                ),
                href="#",  # Placeholder, updated dynamically by the callback
                id="back-link",  # Add an ID for the Back link
            ),
            html.Div(
                [
                    html.Button(
                        [
                            html.I(className="bi bi-info-circle"),
                            " Info",
                        ],  # Icon and text
                        className="info-button",
                        id="info-button",
                    ),
                    html.Div(
                        [
                            html.P(
                                "Important Information: The checks are intended to assist with cSDTM TA Head review. "
                                "Some checks marked as 'Fail' may be acceptable depending on the data collection process, "
                                "SDTM IG version, and protocol-specific requirements. Please consult the relevant documentation "
                                "or team for clarification.",
                                className="info-text",
                            ),
                            html.Button(
                                "OK",
                                className="ok-button",
                                id="ok-button",  # Add an ID for the OK button
                            ),
                        ],
                        id="info-popup",
                        className="info-popup",
                        style={"display": "none"},
                    ),  # Initially hidden
                ],
                className="info-container",
            ),  # Container for the info button and popup
        ],
        className="home-container",
    )


@app.callback(
    Output("info-popup", "style"),  # Toggle the popup's visibility
    [
        Input("info-button", "n_clicks"),
        Input("ok-button", "n_clicks"),
    ],  # Triggered by Info or OK button
    prevent_initial_call=True,  # Prevent callback from firing on page load
)
def toggle_info_popup(info_clicks, ok_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id == "info-button":
        return {"display": "block"}
    elif triggered_id == "ok-button":
        return {"display": "none"}
    return {"display": "none"}


# Page 1: Protocol Table
def protocol_page():
    protocol_df = (
        summary_df.groupby("Protocol")
        .agg({"Data_Path": "first", "Date": "first"})
        .reset_index()
    )

    return html.Div(
        [
            header(),  # Include the shared header
            home_section(),
            html.Div(
                [
                    html.I(
                        className="bi bi-folder-fill folder-icon",
                        style={
                            "marginLeft": "25px",
                            "marginRight": "10px",
                            "color": "#007bff",
                            "fontSize": "1.5rem",
                            "marginBottom": "10px",
                        },
                    ),
                    html.H1(
                        "Protocols",
                        style={
                            "display": "inline-block",
                            "color": "#007bff",
                            "fontFamily": "Arial, sans-serif",
                            "fontWeight": "bold",
                            "fontSize": "1.5rem",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginTop": "20px",
                    "marginBottom": "10px",
                    "marginRight": "25px",
                },
            ),
            html.Div(
                dag.AgGrid(
                    id="protocol-grid",
                    rowData=protocol_df.to_dict("records"),
                    columnDefs=[
                        {
                            "headerName": "Protocol",
                            "field": "Protocol",
                            "cellRenderer": "ProtocolLink",
                            "width": 800,
                        },
                        {
                            "headerName": "Study Path",
                            "field": "Data_Path",
                            "width": 1200,
                        },
                        {"headerName": "Latest Date", "field": "Date", "width": 500},
                    ],
                    dashGridOptions={"pagination": True, "paginationPageSize": 30},
                    defaultColDef={
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "editable": False,
                    },
                    style={"height": "1000px", "width": "100%"},
                ),
                className="grid-container",
            ),
        ],
        className="page-container",
    )


# Page 2: Project Table
# Page 2: Project Table
def project_page(selected_protocol):
    # Filter the DataFrame for the selected protocol
    filtered_df = summary_df[summary_df["Protocol"] == selected_protocol]
    # Write the filtered DataFrame to an Excel file
    # writer = pd.ExcelWriter("testing_project.xlsx", engine="xlsxwriter")
    # filtered_df.to_excel(writer, sheet_name="Summary", index=False)
    # writer.close()  # Save and close the file

    project_df = (
        filtered_df.groupby("Project").agg({"Data_Path": "first"}).reset_index()
    )

    return html.Div(
        [
            header(),  # Include the shared header
            home_section(),
            html.Div(
                [
                    html.I(
                        className="bi bi-folder-fill",
                        style={
                            "marginLeft": "25px",
                            "marginRight": "10px",
                            "color": "#007bff",
                            "fontSize": "1.5rem",
                            "marginBottom": "10px",
                        },
                    ),
                    html.H1(
                        f"Projects for Protocol: {selected_protocol}",
                        style={
                            "display": "inline-block",
                            "color": "#007bff",
                            "fontFamily": "Arial, sans-serif",
                            "fontWeight": "bold",
                            "fontSize": "1.5rem",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginTop": "20px",
                    "marginBottom": "10px",
                },
            ),
            html.Div(
                dag.AgGrid(
                    id="project-grid",
                    rowData=project_df.to_dict("records"),
                    columnDefs=[
                        {
                            "headerName": "Project",
                            "field": "Project",
                            "cellRenderer": "ProjectLink",  # Use the ProjectLink renderer
                            "width": 400,
                        },
                        {"headerName": "Path", "field": "Data_Path", "width": 800},
                    ],
                    dashGridOptions={
                        "pagination": True,
                        "paginationPageSize": 30,
                        "frameworkComponents": {
                            "ProjectLink": "ProjectLink"  # Register the ProjectLink renderer
                        },
                    },
                    defaultColDef={
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "editable": False,
                    },
                    style={"height": "1000px", "width": "100%"},
                ),
                className="grid-container",
            ),
        ],
        className="page-container",
    )


# Page 2: Analysis Task Table
# Page 3: Analysis Task Table
def analysis_task_page(selected_protocol, selected_project):
    # Filter the DataFrame for the selected protocol and project
    filtered_df = summary_df[
        (summary_df["Protocol"] == selected_protocol)
        & (summary_df["Project"] == selected_project)
    ]
    task_df = (
        filtered_df.groupby("Analysis_Task").agg({"Data_Path": "first"}).reset_index()
    )

    return html.Div(
        [
            header(),
            home_section(),
            html.Div(
                [
                    html.I(
                        className="bi bi-list-task",
                        style={
                            "marginLeft": "25px",
                            "marginRight": "10px",
                            "color": "#007bff",
                            "fontSize": "1.5rem",
                            "marginBottom": "10px",
                        },
                    ),
                    html.H1(
                        f"Analysis Tasks for Protocol: {selected_protocol}, Project: {selected_project}",
                        style={
                            "display": "inline-block",
                            "color": "#007bff",
                            "fontFamily": "Arial, sans-serif",
                            "fontWeight": "bold",
                            "fontSize": "1.5rem",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginTop": "20px",
                    "marginBottom": "10px",
                },
            ),
            html.Div(
                dag.AgGrid(
                    id="task-grid",
                    rowData=task_df.to_dict("records"),
                    columnDefs=[
                        {
                            "headerName": "Task",
                            "field": "Analysis_Task",
                            "cellRenderer": "TaskLink",  # Custom renderer for clickable links
                            "width": 400,
                        },
                        {"headerName": "Path", "field": "Data_Path", "width": 800},
                    ],
                    dashGridOptions={"pagination": True, "paginationPageSize": 30},
                    defaultColDef={
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "editable": False,
                    },
                    style={"height": "1000px", "width": "100%"},
                ),
                className="grid-container",
            ),
        ],
        className="page-container",
    )


# Page 3: Analysis Version Table
import os  # Import the os module for path manipulation


def analysis_version_page(selected_protocol, selected_project, selected_task):
    # Filter the DataFrame for the selected protocol, project, and task
    filtered_df = summary_df[
        (
            summary_df["Protocol"].str.strip().str.lower()
            == selected_protocol.strip().lower()
        )
        & (
            summary_df["Project"].str.strip().str.lower()
            == selected_project.strip().lower()
        )
        & (
            summary_df["Analysis_Task"].str.strip().str.lower()
            == selected_task.strip().lower()
        )
    ]

    if filtered_df.empty:
        return html.Div("No data available for the selected filters.")

    # Add a new column for the modified path
    def generate_sdtm_path(row):
        # Get the original Data_Path
        original_path = row["Data_Path"]
        # Go two steps back in the path
        two_steps_back = os.path.normpath(os.path.join(original_path, "../"))
        # Append the new path structure
        new_path = os.path.join(
            two_steps_back,
            f"docs/sdtm/{row['Project']}_{row['Analysis_Task']}_sdtm_mapping.xlsx",
        )
        # Replace backslashes with forward slashes
        return new_path.replace("\\", "/")

    # Generate the SDTM_Path
    filtered_df["SDTM_Path"] = filtered_df.apply(generate_sdtm_path, axis=1)

    # Attach the base_url to make it a full hyperlink
    base_url = "https://gdash-ds.gilead.com/specstor/detail?path="
    filtered_df["SDTM_Spec"] = filtered_df["SDTM_Path"].apply(
        lambda path: f"{base_url}{path}"
    )

    # writer = pd.ExcelWriter("testing_analysis_version.xlsx", engine="xlsxwriter")
    # filtered_df.to_excel(writer, sheet_name="Summary", index=False)
    # writer.close()  # Save and close the file
    # Group by Protocol, Project, and Analysis_Version if needed
    version_df = (
        filtered_df.groupby(
            [
                "Protocol",
                "Project",
                "Analysis_Version",
                "SDTM_Spec",
                "Max_Modified_Date",
            ]
        )
        .agg({"Data_Path": "first"})
        .reset_index()
    )
    writer = pd.ExcelWriter("testing_analysis_version.xlsx", engine="xlsxwriter")
    version_df.to_excel(writer, sheet_name="Summary", index=False)
    writer.close()  # Save and close the file
    return html.Div(
        [
            header(),
            home_section(),
            html.Div(
                [
                    html.I(
                        className="bi bi-bar-chart-fill",
                        style={
                            "marginLeft": "25px",
                            "marginRight": "10px",
                            "color": "#007bff",
                            "fontSize": "1.5rem",
                            "marginBottom": "10px",
                        },
                    ),
                    html.H1(
                        f"Analysis Versions for Protocol: {selected_protocol}, Project: {selected_project}, Task: {selected_task}",
                        style={
                            "display": "inline-block",
                            "color": "#007bff",
                            "fontFamily": "Arial, sans-serif",
                            "fontWeight": "bold",
                            "fontSize": "1.5rem",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginTop": "20px",
                    "marginBottom": "10px",
                },
            ),
            html.Div(
                dag.AgGrid(
                    id="version-grid",
                    rowData=version_df.to_dict("records"),
                    columnDefs=[
                        {
                            "headerName": "Version",
                            "field": "Analysis_Version",
                            "cellRenderer": "VersionLink",  # Custom renderer for clickable links
                            "width": 400,
                        },
                        {"headerName": "Path", "field": "Data_Path", "width": 800},
                        {
                            "headerName": "SDTM Specification",
                            "field": "SDTM_Spec",
                            "cellRenderer": "LinkCellRenderer",  # Use the new LinkCellRenderer
                            "width": 800,
                        },
                        {
                            "headerName": "SDTM Run Date",
                            "field": "Max_Modified_Date",
                            "width": 200,
                        },
                    ],
                    dashGridOptions={
                        "pagination": True,
                        "paginationPageSize": 10,
                        "frameworkComponents": {
                            "VersionLink": "VersionLink",  # Register the VersionLink renderer
                            "LinkCellRenderer": "LinkCellRenderer",  # Register the LinkCellRenderer for hyperlinks
                        },
                        "context": {  # Pass the selectedTask value to the context
                            "selectedTask": selected_task
                        },
                    },
                    defaultColDef={
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "editable": False,
                    },
                    style={"height": "400px", "width": "100%"},
                ),
                className="grid-container",
            ),
        ],
        className="page-container",
    )


# Page 4: Display Table
def display_table_page(
    selected_prot, selected_project, selected_task, selected_version
):
    # Filter the DataFrame for the selected task and version
    filtered_df = summary_df[
        (summary_df["Protocol"] == selected_prot)
        & (summary_df["Project"] == selected_project)
        & (summary_df["Analysis_Task"] == selected_task)
        & (summary_df["Analysis_Version"] == selected_version)
    ].copy()

    # Generate the path for the quality checks file
    def generate_quality_checks_path():
        if not filtered_df.empty:
            original_path = filtered_df.iloc[0]["Data_Path"]
            # Replace "biometrics" with "G:" if present
            if "biometrics" in original_path.lower():
                original_path = original_path.lower().replace("biometrics", "G:")
            # Go two steps back in the path
            two_steps_back = os.path.normpath(os.path.join(original_path, "../"))
            # Append the new path structure
            new_path = os.path.join(two_steps_back, f"docs/sdtm")
            # Replace backslashes with forward slashes and remove the leading "/"
            return new_path.replace("\\", "/").lstrip("/")
        return None

    # Get the quality checks file path
    quality_checks_path = generate_quality_checks_path()

    # Define the column definitions for the grid
    column_defs = [
        {"headerName": "Protocol", "field": "Protocol", "width": 110},
        {"headerName": "Project", "field": "Project", "width": 150},
        {"headerName": "Analysis Task", "field": "Analysis_Task", "width": 150},
        {"headerName": "Analysis Version", "field": "Analysis_Version", "width": 150},
        {"headerName": "CHECK", "field": "CHECK", "width": 800},
        {"headerName": "Message", "field": "Message", "width": 400},
        {"headerName": "Notes", "field": "Notes", "width": 550},
        {"headerName": "Datasets", "field": "Datasets", "width": 180},
    ]

    # Create a copy of the "Message" column for plotting purposes
    plot_message = filtered_df["Message"].apply(
        lambda x: x if x in ["Pass", "Fail"] else "Other"
    )

    # Aggregate data for the pie chart
    pie_data = plot_message.value_counts().reset_index()
    pie_data.columns = ["Status", "Count"]

    # Create the pie chart
    pie_chart = dcc.Graph(
        id="pie-chart",
        figure={
            "data": [
                {
                    "labels": pie_data["Status"],
                    "values": pie_data["Count"],
                    "type": "pie",
                    "hole": 0.4,  # Optional: Makes it a donut chart
                }
            ],
            "layout": {
                "title": "Pass/Fail Distribution",  # Add a title for the pie chart
                "margin": {"l": 10, "r": 10, "t": 30, "b": 10},
                "plot_bgcolor": "rgba(0,0,0,0)",  # Transparent plot background
                "paper_bgcolor": "rgba(0,0,0,0)",  # Transparent paper background
                "legend": {
                    "orientation": "h",  # Horizontal legend
                    "x": 0.5,  # Center the legend horizontally
                    "xanchor": "center",  # Anchor the legend at the center
                    "y": -0.2,  # Position the legend below the chart
                },
            },
        },
        style={"height": "300px", "width": "100%"},  # Adjust size as needed
    )

    # Aggregate data for the bar chart
    dataset_counts = filtered_df["Datasets"].value_counts().reset_index()
    dataset_counts.columns = ["Dataset", "Count"]

    # Create the bar chart
    bar_chart = dcc.Graph(
        id="bar-chart",
        figure={
            "data": [
                {
                    "x": dataset_counts["Dataset"],
                    "y": dataset_counts["Count"],
                    "type": "bar",
                    "marker": {"color": "#007bff"},
                }
            ],
            "layout": {
                "title": "Dataset Distribution",  # Add a title for the bar chart
                "xaxis": {"title": "Datasets"},
                "yaxis": {"title": "Count"},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
            },
        },
        style={"height": "300px", "width": "100%"},  # Adjust size as needed
    )

    # Create the layout
    layout = [
        header(),
        home_section(),
        # Add the pie chart and bar chart side by side
        html.Div(
            [
                # Pie chart with border
                html.Div(
                    pie_chart,
                    style={
                        "flex": "1",
                        "marginRight": "10px",
                        "border": "2px solid #6a0dad",  # Purple border
                        "borderRadius": "8px",  # Rounded corners
                        "padding": "10px",  # Padding inside the border
                        "backgroundColor": "#f9f9f9",  # Optional: Light background color
                    },
                ),
                # Bar chart with border
                html.Div(
                    bar_chart,
                    style={
                        "flex": "1",
                        "marginLeft": "10px",
                        "border": "2px solid #6a0dad",  # Purple border
                        "borderRadius": "8px",  # Rounded corners
                        "padding": "10px",  # Padding inside the border
                        "backgroundColor": "#f9f9f9",  # Optional: Light background color
                    },
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "marginBottom": "20px",
            },
        ),
        # Add the "Table for Task" section below the charts
        html.Div(
            [
                html.I(
                    className="bi bi-table",
                    style={
                        "marginLeft": "25px",
                        "marginRight": "10px",
                        "color": "#007bff",
                        "fontSize": "1.5rem",
                        "marginBottom": "10px",
                    },
                ),
                html.H1(
                    f"Table for Task: {selected_task}, Version: {selected_version}",
                    style={
                        "display": "inline-block",
                        "color": "#007bff",
                        "fontFamily": "Arial, sans-serif",
                        "fontWeight": "bold",
                        "fontSize": "1.5rem",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "marginTop": "20px",
                "marginBottom": "10px",
            },
        ),
        # Add the data grid
        html.Div(
            [
                dag.AgGrid(
                    rowData=filtered_df.to_dict("records"),
                    columnDefs=column_defs,
                    dashGridOptions={
                        "pagination": True,
                        "paginationPageSize": 30,
                        "rowHeight": 25,
                    },
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
                    style={"height": "700px", "width": "100%", "marginTop": "10px"},
                ),
            ],
            className="grid-container",
        ),
    ]

    # Conditionally add the "Quality Checks File" button if the task is "csdtm_dev"
    if selected_task.strip().lower() == "csdtm_dev":
        layout.append(
            html.Div(
                [
                    html.Button(
                        "Quality Checks File",
                        id="quality-checks-button",
                        style={
                            "backgroundColor": "#6a0dad",
                            "color": "white",
                            "border": "none",
                            "padding": "10px 20px",
                            "cursor": "pointer",
                            "fontSize": "16px",
                            "marginTop": "10px",
                            "borderRadius": "12px",
                        },
                    ),
                    dcc.Store(
                        id="quality-checks-path", data=quality_checks_path
                    ),  # Store the folder path
                    html.Div(
                        id="quality-checks-message",
                        style={"marginTop": "10px", "color": "red"},
                    ),  # Message display
                ],
                style={"textAlign": "center"},
            )
        )

    return html.Div(layout)


# Callback to handle Pinnacle 21 button click
selected_protocol = None
selected_project = None
selected_task = None
selected_version = None


def display_pinnacle_21_page(
    selected_prot, selected_project, selected_task, selected_version
):
    try:
        # Use the passed arguments directly instead of declaring them as global
        # Your logic to fetch and display the Pinnacle 21 page
        engine = get_engine()
        query = f"""
            SELECT * FROM "Combined P21 checks"
            WHERE "Protocol" = '{selected_prot}'
            AND "Project" = '{selected_project}'
            AND "Analysis_Task" = '{selected_task}'
            AND "Analysis_Version" = '{selected_version}'
        """
        with engine.connect() as connection:
            p21_df = pd.read_sql(query, connection)

        # Define column definitions for the grid
        column_defs = [
            {"headerName": "Protocol", "field": "Protocol", "width": 110},
            {"headerName": "Project", "field": "Project", "width": 150},
            {"headerName": "Analysis Task", "field": "Analysis_Task", "width": 150},
            {
                "headerName": "Analysis Version",
                "field": "Analysis_Version",
                "width": 150,
            },
            {"headerName": "Check Name", "field": "Check_Name", "width": 300},
            {"headerName": "Message", "field": "Message", "width": 400},
            {"headerName": "Details", "field": "Details", "width": 550},
        ]

        # Return the layout for the Pinnacle 21 page
        return html.Div(
            [
                header(),
                home_section(),
                html.Div(
                    [
                        html.H1(
                            f"Pinnacle 21 Checks for Protocol: {selected_prot}, Project: {selected_project}, Task: {selected_task}, Version: {selected_version}",
                            style={
                                "color": "#007bff",
                                "fontFamily": "Arial, sans-serif",
                                "fontWeight": "bold",
                                "fontSize": "1.5rem",
                                "marginBottom": "20px",
                            },
                        ),
                    ],
                    style={"textAlign": "center"},
                ),
                # Add the data grid
                html.Div(
                    [
                        dag.AgGrid(
                            rowData=p21_df.to_dict("records"),
                            columnDefs=column_defs,
                            dashGridOptions={
                                "pagination": True,
                                "paginationPageSize": 30,
                                "rowHeight": 25,
                            },
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
                            style={
                                "height": "700px",
                                "width": "100%",
                                "marginTop": "10px",
                            },
                        ),
                    ],
                    className="grid-container",
                ),
            ]
        )
    except Exception as e:
        return html.Div(f"Error fetching Pinnacle 21 data: {e}")


# Callback to update the page content based on the URL

# Define global variables
selected_protocol = None
selected_project = None
selected_task = None
selected_version = None


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def display_page(pathname):
    global selected_protocol, selected_project, selected_task, selected_version  # Use global variables
    print(f"{pathname=}")
    if pathname in ("/", "/sdtmchecks/"):
        return protocol_page()

    elif pathname.startswith("/project/"):
        selected_protocol = pathname.split("/")[-1]
        return project_page(selected_protocol)

    elif pathname.startswith("/analysis-task/"):
        parts = pathname.strip("/").split("/")
        print(f"URL Parts: {parts}")  # Debugging: Print the URL parts

        # Handle 2-part URLs (e.g., /analysis-task/<project>)
        if len(parts) == 2:
            selected_project = parts[1]
            protocol_row = summary_df[summary_df["Project"] == selected_project]
            if not protocol_row.empty:
                selected_protocol = protocol_row["Protocol"].iloc[0]
            else:
                return html.Div(
                    f"Invalid URL: Protocol could not be determined for Project {selected_project}."
                )
        # Handle 3-part URLs (e.g., /analysis-task/<protocol>/<project>)
        elif len(parts) == 3:
            selected_protocol = parts[1]
            selected_project = parts[2]
        else:
            return html.Div("Invalid URL structure for analysis-task.")

        return analysis_task_page(selected_protocol, selected_project)

    elif pathname.startswith("/analysis-version/"):
        parts = pathname.strip("/").split("/")
        print(f"URL Parts: {parts}")  # Debugging: Print the URL parts

        # Handle 2-part URLs (e.g., /analysis-version/<analysis_task>)
        if len(parts) == 2:
            value = parts[1].strip().lower()
            print(f"value print: {value}")

            # Use global `selected_protocol` and `selected_project`
            task_row = summary_df[
                (summary_df["Analysis_Task"].str.strip().str.lower() == value)
                & (summary_df["Protocol"] == selected_protocol)
                & (
                    summary_df["Project"] == selected_project
                )  # Filter by global protocol
            ]
            print(f"Filtered DataFrame for Analysis Task {value}:")
            # print(task_row)

            if not task_row.empty:
                selected_task = value
                selected_project = task_row["Project"].iloc[0]
                print(
                    f"Resolved as Analysis Task: {selected_task}, Protocol: {selected_protocol}, Project: {selected_project}"
                )
                return analysis_version_page(
                    selected_protocol, selected_project, selected_task
                )

            return html.Div(
                f"Invalid URL: {value} is not valid for the current Protocol."
            )

        # Handle 4-part URLs (e.g., /analysis-version/<protocol>/<project>/<task>)
        elif len(parts) == 4:
            selected_protocol = parts[1].strip().lower()
            selected_project = parts[2].strip().lower()
            selected_task = parts[3].strip().lower()
            print(
                f"Resolved 4-part URL - Protocol: {selected_protocol}, Project: {selected_project}, Task: {selected_task}"
            )
        else:
            return html.Div("Invalid URL structure for analysis-version.")

        return analysis_version_page(selected_protocol, selected_project, selected_task)

    elif pathname.startswith("/display-table/"):
        parts = pathname.strip("/").split("/")
        print(f"URL Parts: {parts}")  # Debugging: Print the URL parts

        # Handle 3-part URLs (e.g., /display-table/<task>/<version>)
        if len(parts) == 3:
            selected_task = parts[1].strip().lower()
            selected_version = parts[2].strip().lower()

            # Use global `selected_protocol` and `selected_project`
            protocol_row = summary_df[
                (
                    summary_df["Protocol"] == selected_protocol
                )  # Filter by global protocol
                & (summary_df["Project"] == selected_project)
                & (summary_df["Analysis_Task"].str.strip().str.lower() == selected_task)
                & (
                    summary_df["Analysis_Version"].str.strip().str.lower()
                    == selected_version
                )
            ]
            print(
                f"Filtered DataFrame for Protocol {selected_protocol} and Project {selected_project} and Task {selected_task} and Version {selected_version} "
            )
            # print(protocol_row)

            if not protocol_row.empty:
                selected_project = protocol_row["Project"].iloc[0]
            else:
                return html.Div(
                    f"Invalid URL: Protocol or Project could not be determined for Task {selected_task} and Version {selected_version}."
                )
        # Handle 5-part URLs (e.g., /display-table/<protocol>/<project>/<task>/<version>)
        elif len(parts) == 5:
            # selected_protocol = parts[1].strip().lower()
            # selected_project = parts[2].strip().lower()
            selected_task = parts[3].strip().lower()
            selected_version = parts[4].strip().lower()
        else:
            return html.Div("Invalid URL structure for display-table.")

        print(
            f"Resolved Values - Protocol: {selected_protocol}, Project: {selected_project}, Task: {selected_task}, Version: {selected_version}"
        )  # Debugging
        return display_table_page(
            selected_protocol, selected_project, selected_task, selected_version
        )

    else:
        return protocol_page()
        # return html.Div("404: Page not found")


# from dash.dependencies import State
selected_protocol = None
selected_project = None
selected_task = None
selected_version = None


@app.callback(
    Output("back-link", "href"),  # Update the href of the Back button
    Input("url", "pathname"),  # Get the current pathname
)
def update_back_link(pathname):
    global selected_protocol, selected_project, selected_task, selected_version

    if pathname.startswith("/project/"):
        selected_protocol = pathname.split("/")[-1]
        return "/"

    elif pathname.startswith("/analysis-task/"):
        parts = pathname.strip("/").split("/")
        print(f"URL Parts: {parts}")  # Debugging: Print the URL parts

        # Handle 2-part URLs (e.g., /analysis-task/<project>)
        if len(parts) == 2:
            selected_project = parts[1]
            protocol_row = summary_df[summary_df["Project"] == selected_project]
            if not protocol_row.empty:
                selected_protocol = protocol_row["Protocol"].iloc[0]
            else:
                return html.Div(
                    f"Invalid URL: Protocol could not be determined for Project {selected_project}."
                )
        # Handle 3-part URLs (e.g., /analysis-task/<protocol>/<project>)
        elif len(parts) == 3:
            selected_protocol = parts[1]
            selected_project = parts[2]
        else:
            return html.Div("Invalid URL structure for analysis-task.")

        return f"/project/{selected_protocol}"
    elif pathname.startswith("/analysis-version/"):
        parts = pathname.strip("/").split("/")
        print(f"URL Parts: {parts}")  # Debugging: Print the URL parts

        # Handle 2-part URLs (e.g., /analysis-version/<analysis_task>)
        if len(parts) == 2:
            value = parts[1].strip().lower()
            print(f"value print: {value}")

            # Use global `selected_protocol` and `selected_project`
            task_row = summary_df[
                (summary_df["Analysis_Task"].str.strip().str.lower() == value)
                & (
                    summary_df["Protocol"] == selected_protocol
                )  # Filter by global protocol
                & (summary_df["Project"] == selected_project)
            ]
            print(f"Filtered DataFrame for Analysis Task {value}:")
            # print(task_row)

            if not task_row.empty:
                selected_task = value
                selected_project = task_row["Project"].iloc[0]
                print(
                    f"Resolved as Analysis Task: {selected_task}, Protocol: {selected_protocol}, Project: {selected_project}"
                )
                return f"/analysis-task/{selected_project}"
        else:
            return "/"
    elif pathname.startswith("/display-table/"):
        parts = pathname.strip("/").split("/")
        print(f"URL Parts: {parts}")  # Debugging: Print the URL parts

        # Handle 3-part URLs (e.g., /display-table/<task>/<version>)
        if len(parts) == 3:
            selected_task = parts[1].strip().lower()
            selected_version = parts[2].strip().lower()

            # Use global `selected_protocol` and `selected_project`
            protocol_row = summary_df[
                (
                    summary_df["Protocol"] == selected_protocol
                )  # Filter by global protocol
                & (summary_df["Project"] == selected_project)
                & (summary_df["Analysis_Task"].str.strip().str.lower() == selected_task)
                & (
                    summary_df["Analysis_Version"].str.strip().str.lower()
                    == selected_version
                )
            ]
            print(
                f"Filtered DataFrame for Task {selected_task} and Version {selected_version}:"
            )
            # print(protocol_row)

            if not protocol_row.empty:
                selected_project = protocol_row["Project"].iloc[0]
            else:
                return html.Div(
                    f"Invalid URL: Protocol or Project could not be determined for Task {selected_task} and Version {selected_version}."
                )
        # Handle 5-part URLs (e.g., /display-table/<protocol>/<project>/<task>/<version>)
        elif len(parts) == 5:
            selected_protocol = parts[1].strip().lower()
            selected_project = parts[2].strip().lower()
            selected_task = parts[3].strip().lower()
            selected_version = parts[4].strip().lower()
        else:
            return html.Div("Invalid URL structure for display-table.")

        return f"/analysis-version/{selected_task}"
    else:
        return "/"


@app.callback(
    Output("quality-checks-message", "children"),
    Input("quality-checks-button", "n_clicks"),
    State("quality-checks-path", "data"),
    prevent_initial_call=True,
)
def handle_quality_checks_button(n_clicks, folder_path):
    import requests

    if folder_path:
        try:
            # Send a POST request to the backend to open the folder
            response = requests.post(
                "http://127.0.0.1:8050/open-folder", json={"folder_path": folder_path}
            )
            response_data = response.json()

            if response_data.get("success"):
                return f"Folder opened: {folder_path}"
            else:
                return f"Error: {response_data.get('message')}"
        except Exception as e:
            return f"Error: {str(e)}"
    return "Invalid folder path."


if __name__ == "__main__":
    app.run(debug=True)
