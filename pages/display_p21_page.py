from dash import html
import dash_ag_grid as dag

import pandas as pd

from connection import get_engine
from pages.home import home_section


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
