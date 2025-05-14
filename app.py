from datetime import datetime
from os import path
import dash
from dash import callback_context, Dash, dcc, html, Input, no_update, Output, State
from flask import jsonify
from loguru import logger
import pandas as pd
from sqlalchemy import text
from dash import callback_context

from connection import get_engine
from pages.header import header
from pages.protocol_page import protocol_page
from pages.project_page import project_page
from pages.analysis_task_page import analysis_task_page
from pages.analysis_version_page import analysis_version_page
from pages.display_table_page import display_table_page

engine = get_engine()

# Ensure the table exists (create if not exists)
create_table_query = text("""
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'query_submit_sdtm_checks')
BEGIN
    CREATE TABLE query_submit_sdtm_checks (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255),
        domain NVARCHAR(255),
        description NVARCHAR(MAX),
        [rule] NVARCHAR(MAX),
        submission_date DATETIME DEFAULT GETDATE()
    )
END
""")
with engine.begin() as conn:
    conn.execute(create_table_query)
    print("Table 'query_submit_sdtm_checks' is ready!")
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
            # startfile(folder_path)  # Open the folder in Windows Explorer
            logger.warning("cannot open Windows Explorer on remote client")
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


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="store-selected-protocol", storage_type="session"),
        dcc.Store(id="store-selected-project", storage_type="session"),
        dcc.Store(id="store-selected-task", storage_type="session"),
        dcc.Store(id="store-selected-version", storage_type="session"),
        # Add a div for query status messages
        html.Div(id="query-status", style={"textAlign": "center", "margin": "20px 0"}),
        header(),
        html.Div(id="page-content"),
    ]
)

@app.callback(
    Output("info-popup", "style"),
    [
        Input("info-button", "n_clicks"),
        Input("ok-button", "n_clicks"),
    ],
    prevent_initial_call=True
)
def toggle_info_popup(info_clicks, ok_clicks):
    ctx = dash.callback_context
    # If nothing triggered, hide the popup.
    if not ctx.triggered:
        return {"display": "none"}
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    # When Info button is clicked, show the popup.
    if triggered_id == "info-button" and info_clicks:
        return {
            "display": "block",
            "position": "fixed",
            "top": "20%",
            "left": "50%",
            "transform": "translateX(-50%)",
            "backgroundColor": "#fff",
            "padding": "20px",
            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
            "zIndex": 1000,
        }
    # When OK button is clicked, hide the popup.
    elif triggered_id == "ok-button" and ok_clicks:
        return {"display": "none"}
    # Default: hide the popup.
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

import re

def sanitize_analysis_url(parts):
    """
    Given a raw parts list from an analysis-version display-table URL that may contain duplicate segments,
    this function returns a sanitized list in the expected format:
      [protocol, "analysis-version", "display-table", task, version]
    
    It assumes:
      - parts[0] is the protocol,
      - parts[1] is "analysis-version",
      - parts[2] is "display-table",
      - parts[3] is the intended task,
      - and parts[-1] is the intended version.
    
    For example, if parts is:
      ['p627', 'analysis-version', 'display-table', 'drc', 'display-table', 'drc', 'version1']
    then it returns:
      ['p627', 'analysis-version', 'display-table', 'drc', 'version1']
    """
    try:
        if len(parts) >= 5 and parts[1] == "analysis-version" and parts[2] == "display-table":
            protocol = parts[0]
            task = parts[3]
            version = parts[-1]  # take the last token as the version
            return [protocol, "analysis-version", "display-table", task, version]
        else:
            return parts
    except Exception as e:
        print(f"Error in sanitize_analysis_url: {e}")
        return parts

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
    prevent_initial_call="initial_duplicate",
)
def display_page(pathname, stored_protocol, stored_project):
    # Initialize from stored state
    selected_protocol = stored_protocol
    selected_project = stored_project
    selected_task = None
    selected_version = None

    prefix = "/sdtmchecks/"
    if pathname.startswith(prefix):
        pathname = pathname[len(prefix):]
    print(f"Processed Pathname: {pathname}")

    # Root path: Protocol page
    if pathname == "":
        return protocol_page(summary_df), None, None, None, None

    # Branch for display-table URLs (analysis-version display)
    if pathname.startswith("project/analysis-task/analysis-version/display-table/"):
        dt_prefix = "project/analysis-task/analysis-version/display-table/"
        parts = [part.strip().lower() for part in pathname[len(dt_prefix):].split("/") if part]
        print(f"URL Parts display-table: {parts}")
        if len(parts) == 2:  # /display-table/<task>/<version>
            selected_task = parts[0]
            selected_version = parts[1]
            if not selected_protocol or not selected_project:
                return (
                    html.Div("State missing: Please re‑select your Protocol and Project."),
                    None, None, None, None,
                )
            protocol_row = summary_df[
                (summary_df["Protocol"].str.strip().str.lower() == selected_protocol)
                & (summary_df["Project"].str.strip().str.lower() == selected_project)
                & (summary_df["Analysis_Task"].str.strip().str.lower() == selected_task)
                & (summary_df["Analysis_Version"].str.strip().str.lower() == selected_version)
            ]
            if protocol_row.empty:
                return (
                    html.Div(
                        f"Invalid URL: No match for Task {selected_task} and Version {selected_version} under Protocol {selected_protocol} and Project {selected_project}."
                    ),
                    None, None, None, None,
                )
        elif len(parts) == 4:  # /display-table/<protocol>/<project>/<task>/<version>
            selected_protocol = parts[0]
            selected_project = parts[1]
            selected_task = parts[2]
            selected_version = parts[3]
        else:
            return (
                html.Div(f"Invalid URL structure for display-table. Expected 2 or 4 parts, got {len(parts)}: {parts}"),
                None, None, None, None,
            )
        return (
            display_table_page(selected_protocol, selected_project, selected_task, selected_version, summary_df),
            selected_protocol,
            selected_project,
            selected_task,
            selected_version,
        )

    # Branch for analysis-version (non-display-table)
    elif pathname.startswith("project/analysis-task/analysis-version/"):
        av_prefix = "project/analysis-task/analysis-version/"
        parts = [part.strip().lower() for part in pathname[len(av_prefix):].split("/") if part]
        print(f"URL Parts analysis-version: {parts}")
        if len(parts) == 1:  # /analysis-version/<task>
            selected_task = parts[0]
            if not selected_protocol or not selected_project:
                return (
                    html.Div("State missing: Please re‑select your Protocol and Project."),
                    None, None, None, None,
                )
            task_row = summary_df[
                (summary_df["Analysis_Task"].str.strip().str.lower() == selected_task) &
                (summary_df["Protocol"].str.strip().str.lower() == selected_protocol) &
                (summary_df["Project"].str.strip().str.lower() == selected_project)
            ]
            if task_row.empty:
                return (
                    html.Div(
                        f"Invalid URL: {selected_task} is not valid for Protocol {selected_protocol} and Project {selected_project}."
                    ),
                    None, None, None, None,
                )
        elif len(parts) == 3:  # /analysis-version/<protocol>/<project>/<task>
            selected_protocol = parts[0]
            selected_project = parts[1]
            selected_task = parts[2]
            print(f"Selected Protocol: {selected_protocol}, Project: {selected_project}, Task: {selected_task}")
        else:
            return (
                html.Div(f"Invalid URL structure for analysis-version. Expected 1 or 3 parts, got {len(parts)}: {parts}"),
                None, None, None, None,
            )
        return (
            analysis_version_page(selected_protocol, selected_project, selected_task, summary_df),
            selected_protocol,
            selected_project,
            selected_task,
            None,
        )

    # Branch for analysis-task pages (under project/analysis-task/)
    elif pathname.startswith("project/analysis-task/"):
        parts = [part.strip().lower() for part in pathname[len("project/analysis-task/"):].split("/") if part]
        print(f"URL Parts analysis-task (raw): {parts}")
        # Branch for analysis-version display-table URLs with extra segments
        if len(parts) >= 5 and parts[1] == "analysis-version" and parts[2] == "display-table":
            parts = sanitize_analysis_url(parts)
            print(f"Sanitized URL Parts: {parts}")
            selected_protocol = parts[0]
            if stored_project:
                selected_project = stored_project
            else:
                proj_rows = summary_df[
                    summary_df["Protocol"].str.strip().str.lower() == selected_protocol
                ]
                if not proj_rows.empty:
                    selected_project = proj_rows["Project"].iloc[0].strip().lower()
                    print(f"Inferred Project (from summary_df): {selected_project}")
                else:
                    return (
                        html.Div(f"Invalid URL: Could not determine Project for Protocol {selected_protocol}."),
                        None, None, None, None,
                    )
            selected_task = parts[3]
            selected_version = parts[4]
            return (
                display_table_page(selected_protocol, selected_project, selected_task, selected_version, summary_df),
                selected_protocol,
                selected_project,
                selected_task,
                selected_version,
            )
        # Branch for 3-part URLs: /project/analysis-task/<project>/analysis-version/<task>
        elif len(parts) == 3 and parts[1] == "analysis-version":
            selected_project = stored_project if stored_project else parts[0]
            selected_task = parts[2]
            if stored_protocol:
                selected_protocol = stored_protocol
            else:
                protocol_row = summary_df[
                    summary_df["Project"].str.strip().str.lower() == selected_project
                ]
                if not protocol_row.empty:
                    selected_protocol = protocol_row["Protocol"].iloc[0].strip().lower()
                    print(f"Inferred Protocol (from summary_df): {selected_protocol}")
                else:
                    return (
                        html.Div(f"Invalid URL: Could not determine Protocol for Project {selected_project}."),
                        None, None, None, None,
                    )
            return (
                analysis_version_page(selected_protocol, selected_project, selected_task, summary_df),
                selected_protocol,
                selected_project,
                selected_task,
                None,
            )
        # Branch for URLs with 1 part: /project/analysis-task/<project>
        elif len(parts) == 1:
            selected_project = parts[0]
            print(f"Selected Project (from URL): {selected_project}")
            protocol_row = summary_df[
                summary_df["Project"].str.strip().str.lower() == selected_project
            ]
            if not protocol_row.empty:
                selected_protocol = protocol_row["Protocol"].iloc[0].strip().lower()
                print(f"Inferred Protocol (from summary_df): {selected_protocol}")
            else:
                return (
                    html.Div(f"Invalid URL: Could not determine Protocol for Project {selected_project}."),
                    None, None, None, None,
                )
            return (
                analysis_task_page(selected_protocol, selected_project, summary_df),
                selected_protocol,
                selected_project,
                None,
                None,
            )
        # Branch for URLs with 2 parts: /project/analysis-task/<protocol>/<project>
        elif len(parts) == 2:
            selected_protocol = parts[0]
            selected_project = parts[1]
            print(f"Selected Protocol and Project (from URL): {selected_protocol}, {selected_project}")
            return (
                analysis_task_page(selected_protocol, selected_project, summary_df),
                selected_protocol,
                selected_project,
                None,
                None,
            )
        else:
            return (
                html.Div(f"Invalid URL structure for analysis-task. Expected 1, 2, or a structured 5 parts if analysis-version is used, got {len(parts)}: {parts}"),
                None, None, None, None,
            )

    # Branch for project pages: /project/<protocol>
    elif pathname.startswith("project/"):
        parts = [part.strip().lower() for part in pathname[len("project/") :].split("/") if part]
        print(f"URL Parts project: {parts}")
        if len(parts) == 1:
            selected_protocol = parts[0]
            return (
                project_page(selected_protocol, summary_df),
                selected_protocol,
                None,
                None,
                None,
            )
        else:
            return (
                html.Div(f"Invalid URL structure for project. Expected 1 part, got {len(parts)}: {parts}"),
                None, None, None, None,
            )
    else:
        return (html.Div("404: Page not found"), None, None, None, None)

# from dash.dependencies import State
@app.callback(
    Output("back-link", "href"),
    [Input("url", "pathname")],
    [
        State("store-selected-protocol", "data"),
        State("store-selected-project", "data"),
        State("store-selected-task", "data"),
        State("store-selected-version", "data"),
    ],
)
def update_back_link(pathname, stored_protocol, stored_project, stored_task, stored_version):
    prefix = "/sdtmchecks/"
    # Strip off the prefix to work with a relative URL.
    relative = pathname[len(prefix):] if pathname.startswith(prefix) else pathname
    print(f"Relative URL for back link: {relative}")
    
    # If you're on a display-table page (i.e. the URL contains "display-table"),
    # we want to step back to the analysis-version page for that task.
    if "display-table" in relative:
        if stored_task:
            # Back to the analysis-version selection for the given task.
            return f"/sdtmchecks/project/analysis-task/analysis-version/{stored_task}"
        elif stored_protocol and stored_project:
            # Fallback: go to the analysis-task page.
            return f"/sdtmchecks/project/analysis-task/{stored_protocol}/{stored_project}"
        else:
            return "/sdtmchecks/"
    
    # If on an analysis-version page (without "display-table"), go back to the analysis-task page.
    elif "analysis-version" in relative:
        if stored_protocol and stored_project:
            return f"/sdtmchecks/project/analysis-task/{stored_protocol}/{stored_project}"
        else:
            return "/sdtmchecks/"
    
    # If on an analysis-task page, return to the project page.
    elif relative.startswith("project/analysis-task/"):
        if stored_protocol:
            return f"/sdtmchecks/project/{stored_protocol}"
        else:
            return "/sdtmchecks/"
    
    # If on a project page, return to the main page.
    elif relative.startswith("project/"):
        return "/sdtmchecks/"
    
    # Default fallback:
    else:
        return "/sdtmchecks/"

app.clientside_callback(
    """
    function(n_clicks, folder_path) {
        if (n_clicks && folder_path) {
            navigator.clipboard.writeText(folder_path);
            return "For more information: " + folder_path;
        }
        return "";
    }
    """,
    Output("quality-checks-message", "children"),
    [Input("copy-clipboard-element", "n_clicks")],
    [State("quality-checks-path", "data")]
)
app.clientside_callback(
    """
    function(n_clicks, folder_path) {
        if (n_clicks && folder_path) {
            navigator.clipboard.writeText(folder_path);
            return "For more information: " + folder_path;
        }
        return "";
    }
    """,
    Output("back-link", "children", allow_duplicate=True),
    Input("back-btn", "n_clicks"),
    State("quality-checks-path", "data"),
    prevent_initial_call="initial_duplicate"  # set this as required
)
@app.callback(
    [
        Output("query-status", "children"),
        Output("submit-query-popup", "style")
    ],
    [
        Input("submit-query-button", "n_clicks"),
        Input("query-cancel-btn", "n_clicks"),
        Input("query-submit-btn", "n_clicks")
    ],
    [
        State("query-name", "value"),
        State("query-domain", "value"),
        State("query-description", "value"),
        State("query-rule", "value")
    ],
    prevent_initial_call=True
)
# Callback to toggle the Submit Query popup
def combined_popup_action(n_submit, n_cancel, n_form, name, domain, description, rule):
    ctx = callback_context
    # If no clicks yet, ensure popup is hidden.
    if not ctx.triggered or (n_submit is None and n_cancel is None and n_form is None):
        return "", {"display": "none"}
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Open popup ONLY if the submit query button was clicked and its n_clicks is > 0.
    if triggered_id == "submit-query-button" and n_submit:
        return "", {
            "display": "block",
            "position": "fixed",
            "top": "20%",
            "left": "50%",
            "transform": "translateX(-50%)",
            "backgroundColor": "#fff",
            "padding": "20px",
            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
            "zIndex": 1000,
        }
    # If cancel button is clicked, hide the popup.
    elif triggered_id == "query-cancel-btn" and n_cancel:
        return "", {"display": "none"}
    # Process the form submit button.
    elif triggered_id == "query-submit-btn" and n_form:
        insert_query = text("""
            INSERT INTO query_submit_sdtm_checks (name, domain, description, [rule])
            VALUES (:name, :domain, :description, :rule)
        """)
        try:
            with engine.begin() as conn:
                conn.execute(insert_query, {
                    "name": name,
                    "domain": domain,
                    "description": description,
                    "rule": rule
                })
            # On success, show a success message and close the popup.
            return "Query successfully submitted!", {"display": "none"}
        except Exception as e:
            # On error, remain visible.
            return f"Error submitting query: {str(e)}", {
                "display": "block",
                "position": "fixed",
                "top": "20%",
                "left": "50%",
                "transform": "translateX(-50%)",
                "backgroundColor": "#fff",
                "padding": "20px",
                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
                "zIndex": 1000,
            }
    # For any other trigger, ensure the popup is hidden.
    else:
        return "", {"display": "none"}

@app.callback(
    Output("url", "pathname"),
    [Input("gilead-logo", "n_clicks")],
    prevent_initial_call=True,
)
def go_home(n_clicks):
    if n_clicks:
        return "/sdtmchecks/"  # home page route
    return no_update

if __name__ == "__main__":
    app.run(debug=True)
