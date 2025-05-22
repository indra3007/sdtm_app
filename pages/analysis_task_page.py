from dash import html
import dash_ag_grid as dag

from pages.home import home_section


def extract_task_path(full_path, stop_token="final", offset=1):
    tokens = [token.strip() for token in full_path.split("/") if token.strip()]
    for i, token in enumerate(tokens):
        if token.lower() == stop_token.lower():
            end_index = i + offset  # include additional tokens as specified
            if end_index > len(tokens):
                end_index = len(tokens)
            return "/" + "/".join(tokens[:end_index])
    return full_path


def analysis_task_page(selected_protocol, selected_project, summary_df):
    print(
        f"Generating analysis_task_page for Protocol: {selected_protocol}, Project: {selected_project}"
    )
    print(selected_protocol, selected_project)
    # Ensure case-insensitivity and strip whitespace
    selected_protocol = selected_protocol.strip().lower()
    selected_project = selected_project.strip().lower()

    # Normalize the DataFrame columns for comparison
    summary_df["Protocol"] = summary_df["Protocol"].str.strip().str.lower()
    summary_df["Project"] = summary_df["Project"].str.strip().str.lower()

    # Filter the DataFrame
    filtered_df = summary_df[
        (summary_df["Protocol"] == selected_protocol)
        & (summary_df["Project"] == selected_project)
    ]
    # print(f"Filtered DataFrame:\n{filtered_df}")

    if filtered_df.empty:
        print("No rows found for the selected protocol and project.")
        return html.Div("No rows to show for the selected protocol and project.")

    # Group and prepare the data for display
    task_df = (
        filtered_df.groupby("Analysis_Task").agg({"Data_Path": "first"}).reset_index()
    )
    task_df["Data_Path"] = task_df["Data_Path"].apply(
        lambda p: extract_task_path(p, stop_token=selected_project, offset=2)
    )

    return html.Div(
        [
            home_section(is_protocol=False),
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
