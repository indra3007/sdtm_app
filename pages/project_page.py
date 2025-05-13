import dash_ag_grid as dag
from dash import html

from pages.home import home_section


def project_page(selected_protocol, summary_df):
    # Filter the DataFrame for the selected protocol
    filtered_df = summary_df[summary_df["Protocol"] == selected_protocol]

    project_df = (
        filtered_df.groupby("Project").agg({"Data_Path": "first"}).reset_index()
    )

    return html.Div(
        [
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
