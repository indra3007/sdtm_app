from os import path

from dash import html
import dash_ag_grid as dag
import pandas as pd

from pages.home import home_section


def analysis_version_page(
    selected_protocol, selected_project, selected_task, summary_df
):
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
        two_steps_back = path.normpath(path.join(original_path, "../"))
        # Append the new path structure
        new_path = path.join(
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
    #writer = pd.ExcelWriter("testing_analysis_version.xlsx", engine="xlsxwriter")
    #ersion_df.to_excel(writer, sheet_name="Summary", index=False)
    #writer.close()  # Save and close the file
    return html.Div(
        [
            home_section(is_protocol=False),
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
