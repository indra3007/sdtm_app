from os import path

from dash import dcc, html
import dash_ag_grid as dag
import pandas as pd
from connection import get_engine
from pages.home import home_section
import asyncio


async def fetch_db_logs_async():
    query = "SELECT path, severity FROM MACRO.dbo.sptrakerd_logmessage"
    engine = get_engine()
    try:

        def run_query():
            with engine.connect() as connection:
                return pd.read_sql(query, connection)

        # Run the blocking query in a separate thread
        df = await asyncio.to_thread(run_query)
        return df
    except Exception as e:
        print(f"Failed to execute query or save data: {e}")
        return pd.DataFrame()
    finally:
        engine.dispose()


async def fetch_db_summary_async():
    query = "SELECT path, sdtm_complete, sdtm_total FROM MACRO.dbo.sptrakerd_summary"
    engine = get_engine()
    try:

        def run_query():
            with engine.connect() as connection:
                return pd.read_sql(query, connection)

        # Run the blocking query in a separate thread
        df = await asyncio.to_thread(run_query)
        return df
    except Exception as e:
        print(f"Failed to execute query or save data: {e}")
        return pd.DataFrame()
    finally:
        engine.dispose()


def display_table_page(
    selected_prot, selected_project, selected_task, selected_version, summary_df
):
    # Filter the DataFrame for the selected task and version
    filtered_df = summary_df[
        (summary_df["Protocol"] == selected_prot)
        & (summary_df["Project"] == selected_project)
        & (summary_df["Analysis_Task"] == selected_task)
        & (summary_df["Analysis_Version"] == selected_version)
    ].copy()
    # writer = pd.ExcelWriter("testing_table_version.xlsx", engine="xlsxwriter")
    # filtered_df.to_excel(writer, sheet_name="Summary", index=False)
    # writer.close()  # Save and close the file

    # Generate the path for the quality checks file
    def generate_quality_checks_path():
        if not filtered_df.empty:
            original_path = filtered_df.iloc[0]["Data_Path"]
            # Replace "biometrics" with "G:" if present
            if "biometrics" in original_path.lower():
                original_path = original_path.lower().replace("biometrics", "G:")
            # Go two steps back in the path
            two_steps_back = path.normpath(path.join(original_path, "../"))
            # Append the new path structure
            new_path = path.join(two_steps_back, f"docs/sdtm")
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
                    "hole": 0.2,
                }
            ],
            "layout": {
                "title": "Pass/Fail Distribution",
                "margin": {"l": 10, "r": 10, "t": 30, "b": 10},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "legend": {
                    "orientation": "v",
                    "x": 1.02,
                    "xanchor": "left",
                    "y": 0.5,
                },
            },
        },
        style={"height": "280px", "width": "100%"},
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
    df_db_logs = asyncio.run(fetch_db_logs_async())
    common_prefixes = (
        filtered_df["Data_Path"].apply(lambda x: "/".join(x.split("/")[:-1])).unique()
    )

    filtered_logs = df_db_logs[
        df_db_logs["path"].apply(
            lambda p: any(p.startswith(prefix) for prefix in common_prefixes)
        )
    ]
    df_db_summary = asyncio.run(fetch_db_summary_async())
    common_prefixes = (
        filtered_df["Data_Path"].apply(lambda x: "/".join(x.split("/")[:-1])).unique()
    )

    filtered_summary = df_db_summary[
        df_db_summary["path"].apply(
            lambda p: any(p.startswith(prefix) for prefix in common_prefixes)
        )
    ]
    print("Path values:", filtered_summary["path"].tolist())

    # output_excel = "filtered_data_fromdp.xlsx"
    # filtered_logs.to_excel(output_excel, index=False)
    # Create the header row with conditionally inserted "Copy Path"
    header_row = html.Div(
        children=[  # Start a list for the first two elements
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
        ]
        + (
            # Only insert these elements if selected_task is "csdtm_dev"
            [
                html.Span(
                    "For detailed information; ",
                    style={
                        "display": "inline-block",
                        "marginLeft": "20px",
                        "color": "#007bff",
                        "fontSize": "1rem",
                    },
                ),
                html.Span(
                    [html.I(className="bi bi-clipboard"), " Copy Path"],
                    id="copy-clipboard-element",
                    style={
                        "backgroundColor": "#6a0dad",
                        "color": "white",
                        "padding": "5px 10px",
                        "cursor": "pointer",
                        "fontSize": "16px",
                        "borderRadius": "12px",
                        "marginLeft": "5px",
                        "display": "inline-block",
                    },
                ),
                dcc.Store(id="quality-checks-path", data=quality_checks_path),
                html.Div(
                    id="quality-checks-message",
                    style={
                        "marginLeft": "10px",
                        "color": "red",
                        "fontSize": "14px",
                        "display": "inline-block",
                    },
                ),
            ]
            if selected_task.strip().lower() == "csdtm_dev"
            else []
        ),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "flex-start",
            "marginTop": "20px",
            "marginBottom": "10px",
        },
    )

    # --- New Code for Two Donut Plots (Severity Grouped) in the Same Box ---
    # Filter for log files (paths ending with ".log")
    logs_df = filtered_logs[filtered_logs["path"].str.endswith(".log", na=False)].copy()

    # Extract file name from the path (e.g. "ae.log", "vs.log", "v-ae.log", etc.)
    logs_df["file_name"] = logs_df["path"].apply(lambda p: p.split("/")[-1])

    # Determine Environment: if file name starts with "v-" then mark as "Validation", else "Production"
    logs_df["Environment"] = logs_df["file_name"].apply(
        lambda x: "Validation" if x.lower().startswith("v-") else "Production"
    )

    # For each environment, group by severity and count records
    prod_df = (
        logs_df[logs_df["Environment"] == "Production"]
        .groupby("severity")
        .size()
        .reset_index(name="Count")
    )
    val_df = (
        logs_df[logs_df["Environment"] == "Validation"]
        .groupby("severity")
        .size()
        .reset_index(name="Count")
    )

    # Create the donut plot for Production logs
    production_donut = dcc.Graph(
        id="production-donut",
        figure={
            "data": [
                {
                    "labels": prod_df["severity"],
                    "values": prod_df["Count"],
                    "type": "pie",
                    "hole": 0.4,  # Donut style
                    "marker": {"colors": ["#007bff", "#ff5733", "#33ff57", "#f3ff33"]},
                    "textinfo": "label+percent",  # Reduce number info
                    "textfont": {"size": 10},
                }
            ],
            "layout": {
                "title": "Production",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "margin": {"l": 20, "r": 20, "t": 50, "b": 50},
                "legend": {
                    "orientation": "h",
                    "x": 0.5,
                    "xanchor": "center",
                    "y": -0.1,
                    "font": {"size": 10},
                },
            },
        },
        style={"height": "300px", "width": "100%"},
    )

    # Create the donut plot for Validation logs
    validation_donut = dcc.Graph(
        id="validation-donut",
        figure={
            "data": [
                {
                    "labels": val_df["severity"],
                    "values": val_df["Count"],
                    "type": "pie",
                    "hole": 0.4,  # Donut style
                    "marker": {"colors": ["#8e44ad", "#e74c3c", "#f39c12", "#2ecc71"]},
                    "textinfo": "label+percent",
                    "textfont": {"size": 10},
                }
            ],
            "layout": {
                "title": "Validation",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "margin": {"l": 20, "r": 20, "t": 50, "b": 50},
                "legend": {
                    "orientation": "h",
                    "x": 0.5,
                    "xanchor": "center",
                    "y": -0.1,
                    "font": {"size": 10},
                },
            },
        },
        style={"height": "300px", "width": "100%"},
    )

    # --- New Code for Two Donut Plots (Severity Grouped) in the Same Box ---
    donuts_box = html.Div(
        children=[
            html.H3(
                "Log Scans:",
                style={
                    "textAlign": "center",
                    "color": "#6a0dad",
                    "marginBottom": "20px",
                    "fontWeight": "bold",
                    "fontSize": "24px",
                },
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            production_donut,
                            html.Div(
                                "Production",
                                style={
                                    "textAlign": "center",
                                    "fontWeight": "bold",
                                    "marginTop": "10px",
                                    "fontSize": "16px",
                                },
                            ),
                        ],
                        style={
                            "width": "50%",
                            "display": "inline-block",
                            "verticalAlign": "top",
                            "padding": "10px",
                        },
                    ),
                    html.Div(
                        children=[
                            validation_donut,
                            html.Div(
                                "Validation",
                                style={
                                    "textAlign": "center",
                                    "fontWeight": "bold",
                                    "marginTop": "10px",
                                    "fontSize": "16px",
                                },
                            ),
                        ],
                        style={
                            "width": "50%",
                            "display": "inline-block",
                            "verticalAlign": "top",
                            "padding": "10px",
                        },
                    ),
                ],
                style={"display": "flex", "justifyContent": "space-between"},
            ),
        ],
        style={
            "flex": "0 0 33%",
            "marginLeft": "10px",
            "border": "2px solid #6a0dad",  # Added purple border
            "borderRadius": "8px",
            "padding": "20px",
            "backgroundColor": "#f9f9f9",
            "minHeight": "400px",
            "width": "100%",
            "boxSizing": "border-box",
        },
    )
    # Compute SDTM completion percentage before using progress_bar
    # --- Compute SDTM completion percentage ---
    if not filtered_summary.empty:
        total_complete = filtered_summary["sdtm_complete"].sum()
        total_total = filtered_summary["sdtm_total"].sum()
        percentage = (total_complete / total_total) * 100 if total_total > 0 else 0
    else:
        percentage = 0

    # --- Compute dynamic inner color (0% red, 100% green) ---
    inner_color = f"hsl({(percentage/100)*120}, 100%, 50%)"

    # --- Create the battery-style progress bar (battery_bar) with slanted cut ---
    battery_bar = html.Div(
        children=[
            html.Div(
                f"{percentage:.1f}% Completed",
                style={
                    "width": "100%",
                    "textAlign": "center",
                    "position": "absolute",
                    "top": 0,
                    "left": 0,
                    "lineHeight": "30px",
                    "color": "white",
                    "fontWeight": "bold",
                    # Optional: apply the same clipPath to the label for consistency
                },
            ),
            html.Div(
                style={
                    "width": f"{percentage}%",
                    "height": "30px",
                    "backgroundColor": inner_color,
                    # Apply a clip-path for a slanted cut on the right side
                }
            ),
        ],
        style={
            "position": "relative",
            "width": "calc(100% - 20px)",  # leave space for the terminal
            "height": "30px",
            "backgroundColor": "#e6e6e6",
            "borderRadius": "4px",
            "overflow": "hidden",
            "marginRight": "5px",
        },
    )

    # --- Combine battery_bar and battery_terminal into battery_container ---
    battery_container = html.Div(
        children=[battery_bar],
        style={
            "display": "flex",
            "alignItems": "center",
            "width": "300px",  # adjust overall width as desired
            "margin": "20px auto 0",  # centers the container horizontally
        },
    )

    # Create a container box for the pie chart with its own header
    pie_box = html.Div(
        children=[
            html.H3(
                "Status of Checks:",
                style={
                    "textAlign": "center",
                    "color": "#6a0dad",
                    "marginBottom": "5px",
                    "fontWeight": "bold",
                    "fontSize": "24px",
                },
            ),
            # Container for the pie chart, moved a little to the left
            html.Div(
                children=[
                    html.Div(
                        pie_chart,
                        style={"marginLeft": "40px"},  # adjust this value as needed
                    )
                ],
                style={"display": "flex", "justifyContent": "flex-start"},
            ),
            # Container for the battery progress bar with header (centered under the pie chart)
            html.Div(
                children=[
                    html.H3(
                        "Status of SDTM Programming:",
                        style={
                            "textAlign": "center",
                            "color": "#6a0dad",
                            "marginBottom": "2px",
                            "fontWeight": "bold",
                            "fontSize": "24px",
                        },
                    ),
                    battery_container,
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "marginTop": "5px",
                    "border": "2px solid #6a0dad",
                    "borderRadius": "8px",
                    "padding": "10px",
                },
            ),
        ],
        style={
            "width": "800px",
            "marginRight": "10px",
            "border": "2px solid #6a0dad",
            "borderRadius": "8px",
            "padding": "10px",
            "backgroundColor": "#f9f9f9",
            "minHeight": "400px",
            "boxSizing": "border-box",
        },
    )
    # Create a container box for the bar chart with its own header
    bar_box = html.Div(
        children=[
            html.H3(
                "Number of Checks Performed Across the Datasets:",
                style={
                    "textAlign": "center",
                    "color": "#6a0dad",
                    "marginBottom": "20px",
                    "fontWeight": "bold",
                    "fontSize": "24px",
                },
            ),
            bar_chart,
        ],
        style={
            "width": "840px",  # fixed width
            "marginLeft": "10px",
            "border": "2px solid #6a0dad",
            "borderRadius": "8px",
            "padding": "10px",
            "backgroundColor": "#f9f9f9",
            "minHeight": "400px",
            "boxSizing": "border-box",
        },
    )

    # Now, update the charts_row to include all three boxes side by side:
    charts_row = html.Div(
        children=[
            pie_box,
            bar_box,
            html.Div(
                donuts_box,
                style={
                    "width": "830px",
                    "marginLeft": "10px",
                    "boxSizing": "border-box",
                },
            ),
        ],
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "justifyContent": "flex-start",
            "marginBottom": "20px",
        },
    )

    # Create the layout
    layout = [
        home_section(is_protocol=False),
        html.Div(
            children=[charts_row],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "marginBottom": "20px",
            },
        ),
        # progress_row,    # Using the progress bar row here.
        header_row,
        html.Div(
            children=[
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
    # Wrap the entire layout in a Loading component
    loading_layout = dcc.Loading(
        id="loading-all",
        type="default",  # You can also try "circle", "cube", etc.
        children=html.Div(layout),
    )

    return html.Div(loading_layout)
