from pages.header import header
from pages.home import home_section
import dash_ag_grid as dag
import pandas as pd
import dash
from dash import dcc, html
import os
from dash import Dash, html, Input, Output, dcc

def display_table_page(selected_prot, selected_project, selected_task, selected_version, summary_df):
    # Filter the DataFrame for the selected task and version
    filtered_df = summary_df[
        (summary_df["Protocol"] == selected_prot)
        & (summary_df["Project"] == selected_project)
        & (summary_df["Analysis_Task"] == selected_task)
        & (summary_df["Analysis_Version"] == selected_version)
    ].copy()
    writer = pd.ExcelWriter("testing_table_version.xlsx", engine="xlsxwriter")
    filtered_df.to_excel(writer, sheet_name="Summary", index=False)
    writer.close()  # Save and close the file
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
