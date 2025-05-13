from datetime import datetime
from os import path, startfile

from dash import callback_context, Dash, dcc, html, Input, no_update, Output, State
from flask import jsonify
import pandas as pd

from connection import get_engine
from pages.header import header
from pages.protocol_page import protocol_page
from pages.project_page import project_page
from pages.analysis_task_page import analysis_task_page
from pages.analysis_version_page import analysis_version_page
from pages.display_table_page import display_table_page


external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",  # Bootstrap CSS
    "https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css",  # Bootstrap Icons
]
# Initialize the Dash app with external stylesheets
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    routes_pathname_prefix="/sdtmchecks/",
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

    if folder_path and path.exists(folder_path):
        try:
            startfile(folder_path)  # Open the folder in Windows Explorer
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
# Update the app layout
# Update the app layout
# Update the app layout
# filepath: c:\Users\inarisetty\sdtm_local\sdtm_checks\app.py

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="store-selected-protocol", storage_type="session"),
        dcc.Store(id="store-selected-project", storage_type="session"),
        dcc.Store(id="store-selected-task", storage_type="session"),
        dcc.Store(id="store-selected-version", storage_type="session"),
        header(),
        html.Div(id="page-content"),
    ]
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
    ctx = callback_context
    if not ctx.triggered:
        return {"display": "none"}
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id == "info-button":
        return {"display": "block"}
    elif triggered_id == "ok-button":
        return {"display": "none"}
    return {"display": "none"}


@app.callback(
    [
        Output("store-selected-protocol", "data"),
        Output("store-selected-project", "data"),
    ],
    Input("protocol-grid", "selectedRows"),
)
def update_protocol_state(selectedRows):
    if selectedRows and len(selectedRows) > 0:
        row = selectedRows[0]
        selected_protocol = row.get("Protocol", "").strip().lower()
        selected_project = (
            row.get("Project", "").strip().lower() if "Project" in row else None
        )
        print(
            f"update_protocol_state: protocol={selected_protocol}, project={selected_project}"
        )
        if selected_protocol and selected_project:
            return selected_protocol, selected_project
        else:
            return no_update, no_update
    return no_update, no_update


@app.callback(
    [
        Output("page-content", "children"),
        Output("store-selected-protocol", "data", allow_duplicate=True),
        Output("store-selected-project", "data", allow_duplicate=True),
        Output("store-selected-task", "data"),
        Output("store-selected-version", "data"),
    ],
    [Input("url", "pathname")],
    [
        State("store-selected-protocol", "data"),
        State("store-selected-project", "data"),
    ],
    prevent_initial_call="initial_duplicate",  # Allow duplicate outputs on initial call
)
def display_page(pathname, stored_protocol, stored_project):
    # Initialize default values from storage (these should be set on previous pages)
    selected_protocol = stored_protocol
    selected_project = stored_project
    selected_task = None
    selected_version = None

    # Remove the prefix if present
    prefix = "/sdtmchecks/"
    if pathname.startswith(prefix):
        pathname = pathname[len(prefix) :]
    print(f"Processed Pathname: {pathname}")

    # Handle the root path (protocol page)
    if pathname == "":
        return protocol_page(summary_df), None, None, None, None

    # Analysis-version display-table branch
    elif pathname.startswith("project/analysis-task/analysis-version/display-table/"):
        prefix = "project/analysis-task/analysis-version/display-table/"
        parts = [part for part in pathname[len(prefix) :].split("/") if part]
        print(f"URL Parts display-table: {parts}")

        if len(parts) == 2:  # URL structure: /display-table/<task>/<version>
            selected_task = parts[0].strip().lower()
            selected_version = parts[1].strip().lower()
            if not selected_protocol or not selected_project:
                return (
                    html.Div(
                        "State missing: Please re‑select your Protocol and Project."
                    ),
                    None,
                    None,
                    None,
                    None,
                )
            protocol_row = summary_df[
                (summary_df["Protocol"] == selected_protocol)
                & (summary_df["Project"] == selected_project)
                & (summary_df["Analysis_Task"].str.strip().str.lower() == selected_task)
                & (
                    summary_df["Analysis_Version"].str.strip().str.lower()
                    == selected_version
                )
            ]
            if protocol_row.empty:
                return (
                    html.Div(
                        f"Invalid URL: No match for Task {selected_task} and Version {selected_version} under Protocol {selected_protocol} and Project {selected_project}."
                    ),
                    None,
                    None,
                    None,
                    None,
                )
        elif (
            len(parts) == 4
        ):  # URL structure: /display-table/<protocol>/<project>/<task>/<version>
            selected_protocol = parts[0].strip().lower()
            selected_project = parts[1].strip().lower()
            selected_task = parts[2].strip().lower()
            selected_version = parts[3].strip().lower()
        else:
            return (
                html.Div(
                    f"Invalid URL structure for display-table. Expected 2 or 4 parts, got {len(parts)}: {parts}"
                ),
                None,
                None,
                None,
                None,
            )

        return (
            display_table_page(
                selected_protocol,
                selected_project,
                selected_task,
                selected_version,
                summary_df,
            ),
            selected_protocol,
            selected_project,
            selected_task,
            selected_version,
        )

    # Analysis-version branch (without display-table)
    elif pathname.startswith("project/analysis-task/analysis-version/"):
        parts = [
            part
            for part in pathname[
                len("project/analysis-task/analysis-version/") :
            ].split("/")
            if part
        ]
        print(f"URL Parts analysis-version: {parts}")

        if len(parts) == 1:  # URL: /analysis-version/<analysis_task>
            selected_task = parts[0].strip().lower()
            print(f"Selected Task: {selected_task}")
            if not selected_protocol or not selected_project:
                return (
                    html.Div(
                        "State missing: Please re‑select your Protocol and Project."
                    ),
                    None,
                    None,
                    None,
                    None,
                )
            task_row = summary_df[
                (summary_df["Analysis_Task"].str.strip().str.lower() == selected_task)
                & (summary_df["Protocol"] == selected_protocol)
                & (summary_df["Project"] == selected_project)
            ]
            if task_row.empty:
                return (
                    html.Div(
                        f"Invalid URL: {selected_task} is not valid for Protocol {selected_protocol} and Project {selected_project}."
                    ),
                    None,
                    None,
                    None,
                    None,
                )
        elif (
            len(parts) == 3
        ):  # URL: /analysis-version/<protocol>/<project>/<analysis_task>
            selected_protocol = parts[0].strip().lower()
            selected_project = parts[1].strip().lower()
            selected_task = parts[2].strip().lower()
            print(
                f"Selected Protocol: {selected_protocol}, Project: {selected_project}, Task: {selected_task}"
            )
        else:
            return (
                html.Div(
                    f"Invalid URL structure for analysis-version. Expected 1 or 3 parts, got {len(parts)}: {parts}"
                ),
                None,
                None,
                None,
                None,
            )
        return (
            analysis_version_page(
                selected_protocol, selected_project, selected_task, summary_df
            ),
            selected_protocol,
            selected_project,
            selected_task,
            None,
        )

    # Analysis-task branch – URL structure: /project/analysis-task/<project> or /analysis-task/<protocol>/<project>
    elif pathname.startswith("project/analysis-task/"):
        parts = [
            part
            for part in pathname[len("project/analysis-task/") :].split("/")
            if part
        ]
        print(f"URL Parts analysis-task: {parts}")
        if len(parts) == 1:
            selected_project = parts[0].strip().lower()
            print(f"Selected Project (from URL): {selected_project}")
            protocol_row = summary_df[summary_df["Project"] == selected_project]
            if not protocol_row.empty:
                selected_protocol = protocol_row["Protocol"].iloc[0]
                print(f"Inferred Protocol (from summary_df): {selected_protocol}")
            else:
                return (
                    html.Div(
                        f"Invalid URL: Could not determine Protocol for Project {selected_project}."
                    ),
                    None,
                    None,
                    None,
                    None,
                )
        elif len(parts) == 2:
            selected_protocol = parts[0].strip().lower()
            selected_project = parts[1].strip().lower()
            print(
                f"Selected Protocol and Project (from URL): {selected_protocol}, {selected_project}"
            )
        else:
            return (
                html.Div(
                    f"Invalid URL structure for analysis-task. Expected 1 or 2 parts, got {len(parts)}: {parts}"
                ),
                None,
                None,
                None,
                None,
            )
        return (
            analysis_task_page(selected_protocol, selected_project, summary_df),
            selected_protocol,
            selected_project,
            None,
            None,
        )

    # Project branch – URL structure: /project/<protocol>
    elif pathname.startswith("project/"):
        parts = [part for part in pathname[len("project/") :].split("/") if part]
        print(f"URL Parts project: {parts}")
        if len(parts) == 1:
            selected_protocol = parts[0].strip().lower()
            return (
                project_page(selected_protocol, summary_df),
                selected_protocol,
                None,
                None,
                None,
            )
        else:
            return (
                html.Div(
                    f"Invalid URL structure for project. Expected 1 part, got {len(parts)}: {parts}"
                ),
                None,
                None,
                None,
                None,
            )

    else:
        return (html.Div("404: Page not found"), None, None, None, None)


# from dash.dependencies import State
@app.callback(
    Output("back-link", "href"),
    Input("url", "pathname"),
    State("store-selected-protocol", "data"),
    State("store-selected-project", "data"),
)
def update_back_link(pathname, stored_protocol, stored_project):
    # Remove the initial prefix
    prefix = "/sdtmchecks/"
    relative = pathname[len(prefix) :] if pathname.startswith(prefix) else pathname
    print(f"Relative URL for back link: {relative}")

    # Level 1: Display-table page (child of analysis-version)
    if relative.startswith("project/analysis-task/analysis-version/display-table/"):
        # Expected structure: display-table/<task>/<version>
        suffix = relative[
            len("project/analysis-task/analysis-version/display-table/") :
        ]
        parts = [p for p in suffix.split("/") if p]
        if len(parts) >= 1:
            task = parts[0].strip().lower()
            # Return to analysis-version page for that task (Level 2)
            return f"/sdtmchecks/project/analysis-task/analysis-version/{task}"
        else:
            return "/sdtmchecks/"

    # Level 2: Analysis-version page -> go back to analysis-task page
    elif relative.startswith("project/analysis-task/analysis-version/"):
        # Ideally, we want to go up one level to analysis-task.
        # We can use stored_protocol and stored_project to build the analysis-task URL.
        if stored_protocol and stored_project:
            # Assuming the analysis-task URL follows the format: /project/analysis-task/<protocol>/<project>
            return (
                f"/sdtmchecks/project/analysis-task/{stored_protocol}/{stored_project}"
            )
        else:
            # Fallback: remove the analysis-version piece
            return "/sdtmchecks/project/analysis-task/"

    # Level 3: Analysis-task page -> go back to project level
    elif relative.startswith("project/analysis-task/"):
        # Analysis-task URL could be either: <project> or <protocol>/<project>
        parts = [p for p in relative[len("project/analysis-task/") :].split("/") if p]
        if len(parts) == 2:
            # e.g., /project/analysis-task/<protocol>/<project>
            protocol = parts[0].strip().lower()
            return f"/sdtmchecks/project/{protocol}"
        elif len(parts) == 1:
            # e.g., /project/analysis-task/<project>
            # Use stored_protocol if available to return to full projects page
            if stored_protocol:
                return f"/sdtmchecks/project/{stored_protocol}"
            else:
                return f"/sdtmchecks/project/{parts[0].strip().lower()}"
        else:
            return "/sdtmchecks/project/"

    # Level 4: Project page -> go back to protocol landing page
    elif relative.startswith("project/"):
        return "/sdtmchecks/"

    # Default fallback
    else:
        return "/sdtmchecks/"


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
            # Updated URL to match the registered route.
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
