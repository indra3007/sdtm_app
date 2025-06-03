import os
from dash import html, dcc
from datetime import datetime
from dash import html, dcc, Input, Output
from app_instance import app
from dash.exceptions import PreventUpdate

# Read the user guide markdown file (assumed to be in the same folder as app.py)
user_guide_file = os.path.join(os.path.dirname(__file__), "..", "user_guide.md")
with open(user_guide_file, "r", encoding="utf-8") as f:
    user_guide_content = f.read()


def home_section(is_protocol=True):
    return html.Div(
        [
            # Header Row.
            html.Div(
                [
                    # Left Group: Home, Back, Info, and User Guide buttons.
                    html.Div(
                        [
                            html.A(
                                html.Button(
                                    [html.I(className="bi bi-house"), " Home"],
                                    className="button-36",
                                    style={"marginLeft": "10px"},
                                ),
                                href="/sdtmchecks/",
                                className="home-link",
                            ),
                            dcc.Link(
                                html.Button(
                                    [html.I(className="bi bi-arrow-left"), " Back"],
                                    className="button-36",
                                    style={"marginLeft": "10px"},
                                ),
                                href="#",
                                id="back-link",
                            ),
                            # Info Button and Popup Container.
                            html.Div(
                                [
                                    html.Button(
                                        [
                                            html.I(className="bi bi-info-circle"),
                                            " Info",
                                        ],
                                        id="info-button",
                                        className="button-36",
                                        style={
                                            "cursor": "pointer",
                                            "marginLeft": "10px",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.P(
                                                "Important Information: The checks are intended to assist with cSDTM TA Head review. "
                                                "Some checks marked as 'Fail' may be acceptable depending on the data collection process, "
                                                "SDTM IG version, and protocol-specific requirements. Please consult the relevant documentation or team for clarification.",
                                                className="info-text",
                                            ),
                                            html.Button(
                                                "OK",
                                                id="ok-button",
                                                className="ok-button btn btn-secondary",
                                                style={"cursor": "pointer"},
                                            ),
                                        ],
                                        id="info-popup",
                                        className="info-popup",
                                        style={"display": "none"},
                                    ),
                                ],
                                className="info-container",
                                style={
                                    "position": "relative",
                                    "display": "inline-block",
                                },
                            ),
                            # User Guide Button and Popup Container.
                            html.Div(
                                [
                                    html.Button(
                                        [html.I(className="bi bi-book"), " User Guide"],
                                        id="user-guide-button",
                                        className="button-36",
                                        style={
                                            "cursor": "pointer",
                                            "marginLeft": "10px",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                "X",
                                                id="user-guide-x-button",
                                                style={
                                                    "position": "absolute",
                                                    "top": "5px",
                                                    "right": "5px",
                                                    "background": "transparent",
                                                    "border": "none",
                                                    "fontSize": "20px",
                                                    "cursor": "pointer",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.Img(
                                                        src="/sdtmchecks/assets/quality_checks.png",
                                                        style={
                                                            "height": "80px",
                                                            "marginRight": "10px",
                                                        },
                                                    ),
                                                    html.H2(
                                                        "cSDTM Quality Checks – User Guide",
                                                        style={
                                                            "textAlign": "center",
                                                            "fontFamily": "cursive",
                                                            "color": "#2E8B57",
                                                            "margin": "0",
                                                        },
                                                    ),
                                                ],
                                                style={
                                                    "marginBottom": "20px",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                },
                                            ),
                                            dcc.Markdown(
                                                user_guide_content,
                                                style={"marginTop": "10px"},
                                            ),
                                            html.Button(
                                                "Close",
                                                id="user-guide-close-button",
                                                className="btn btn-secondary",
                                                style={
                                                    "cursor": "pointer",
                                                    "marginTop": "10px",
                                                    "display": "block",
                                                    "marginLeft": "auto",
                                                    "marginRight": "auto",
                                                },
                                            ),
                                        ],
                                        id="user-guide-popup",
                                        className="user-guide-popup",
                                        style={
                                            "display": "none",
                                            "position": "fixed",
                                            "top": "10%",
                                            "left": "50%",
                                            "transform": "translateX(-50%)",
                                            "backgroundColor": "#fff",
                                            "padding": "20px",
                                            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
                                            "zIndex": 1000,
                                            "width": "60%",
                                            "cursor": "move",
                                            "borderRadius": "8px",
                                            "maxHeight": "70vh",
                                            "overflowY": "auto",
                                        },
                                    ),
                                ],
                                style={"display": "inline-block"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"},
                    ),
                    # Center Group: Welcome message (conditionally displayed)
                    html.Div(
                        (
                            "Welcome to the cSDTM Quality Checks Home Page!"
                            if is_protocol
                            else ""
                        ),
                        className="home-content",
                        style={
                            "flex": "1",
                            "textAlign": "center",
                            "fontSize": "32px",
                            "color": "#2E8B57",
                            "fontWeight": "bold",
                            "animation": "flash 1s infinite",
                        },
                    ),
                    # Right Group: Submit Query and Report Bug buttons.
                    html.Div(
                        [
                            html.Button(
                                [html.I(className="bi bi-send"), " Submit Query"],
                                id="submit-query-button",
                                className="btn btn-info",
                            ),
                            html.Button(
                                [html.I(className="bi bi-bug"), " Report Bug"],
                                id="report-bug-button",
                                className="btn btn-warning",
                                style={"marginLeft": "10px"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "borderRadius": "20px",
                            "marginRight": "10px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "width": "100%",
                    "marginBottom": "20px",
                },
            ),
            # The Submit Query Popup (and you can similarly add a Report Bug Popup)
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Img(
                                        src="/sdtmchecks/assets/quality_checks.png",
                                        style={
                                            "height": "80px",
                                            "marginRight": "10px",
                                        },
                                    ),
                                    html.H4(
                                        "Submit Query",
                                        className="fancy-title",
                                        style={"margin": "0"},
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center"},
                            ),
                            html.Div(
                                style={
                                    "height": "4px",
                                    "width": "100%",
                                    "background": "linear-gradient(to right, red, orange, yellow, green, blue, indigo, violet)",
                                    "marginTop": "5px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Label("Name: ", className="fancy-label"),
                                    dcc.Input(
                                        id="query-name",
                                        type="text",
                                        placeholder="Enter your name",
                                        className="fancy-input",
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            html.Div(
                                [
                                    html.Label("Email: ", className="fancy-label"),
                                    dcc.Input(
                                        id="query-email",
                                        type="email",
                                        placeholder="Enter your email",
                                        className="fancy-input",
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            html.Div(
                                [
                                    html.Label("Domain: ", className="fancy-label"),
                                    dcc.Input(
                                        id="query-domain",
                                        type="text",
                                        placeholder="Enter domain",
                                        className="fancy-input",
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            html.Div(
                                [
                                    html.Label(
                                        "Query Description: ", className="fancy-label"
                                    ),
                                    dcc.Textarea(
                                        id="query-description",
                                        placeholder="Describe your query",
                                        className="fancy-textarea",
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            html.Div(
                                [
                                    html.Label(
                                        "Query Rule / Code: ", className="fancy-label"
                                    ),
                                    dcc.Textarea(
                                        id="query-rule",
                                        placeholder="Enter query rule or code",
                                        className="fancy-textarea",
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            html.Button(
                                "Submit",
                                id="query-submit-btn",
                                className="btn btn-success",
                            ),
                            html.Button(
                                "Cancel",
                                id="query-cancel-btn",
                                className="btn btn-secondary",
                                style={"marginLeft": "10px"},
                            ),
                        ],
                        id="submit-query-popup",
                        className="submit-query-popup",
                        draggable="false",
                        style={
                            "display": "none",
                            "position": "fixed",
                            "top": "20%",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "backgroundColor": "#fff",
                            "padding": "20px",
                            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
                            "zIndex": 1000,
                            "width": "43%",
                            "cursor": "move",
                            "borderRadius": "8px",
                        },
                    ),
                    # Report Bug Popup (existing)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Img(
                                        src="/sdtmchecks/assets/quality_checks.png",
                                        style={
                                            "height": "80px",
                                            "marginRight": "10px",
                                        },
                                    ),
                                    html.H4(
                                        "Report Bug",
                                        className="fancy-title",
                                        style={"margin": "0"},
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center"},
                            ),
                            html.Div(
                                style={
                                    "height": "4px",
                                    "width": "100%",
                                    "background": "linear-gradient(to right, red, orange, yellow, green, blue, indigo, violet)",
                                    "marginTop": "5px",
                                },
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "Please describe the issue you encountered, steps to reproduce the bug, "
                                        "and any additional information (e.g., browser details, error messages) that may help us debug the problem."
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            # Date Picker
                            html.Div(
                                [
                                    html.Label(
                                        "Date:",
                                        className="fancy-label",
                                        style={"marginRight": "10px"},
                                    ),
                                    dcc.DatePickerSingle(
                                        id="bug-report-date",
                                        date=datetime.today().date().isoformat(),
                                        display_format="YYYY-MM-DD",
                                        style={"marginBottom": "10px"},
                                    ),
                                ],
                                style={
                                    "marginBottom": "5x",
                                    "display": "flex",
                                    "alignItems": "center",
                                },
                            ),
                            # Name and Email Input
                            html.Div(
                                [
                                    html.Label("Name:", className="fancy-label"),
                                    dcc.Input(
                                        id="bug-name",
                                        type="text",
                                        placeholder="Enter your name",
                                        className="fancy-input",
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            html.Div(
                                [
                                    html.Label("Email:", className="fancy-label"),
                                    dcc.Input(
                                        id="bug-email",
                                        type="email",
                                        placeholder="Enter your email",
                                        className="fancy-input",
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            # Bug Description Textarea
                            html.Div(
                                [
                                    html.Label(
                                        "Bug Description:", className="fancy-label"
                                    ),
                                    dcc.Textarea(
                                        id="bug-description",
                                        placeholder="Describe the bug in detail...",
                                        className="fancy-textarea",
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            # Upload Component for Screenshot
                            html.Div(
                                [
                                    html.Label(
                                        "Attach Screenshot (optional):",
                                        className="fancy-label",
                                    ),
                                    dcc.Upload(
                                        id="bug-screenshot-upload",
                                        children=html.Div(
                                            "Drag and drop or click to select a file"
                                        ),
                                        style={
                                            "width": "100%",
                                            "height": "60px",
                                            "lineHeight": "60px",
                                            "borderWidth": "1px",
                                            "borderStyle": "dashed",
                                            "borderRadius": "5px",
                                            "textAlign": "center",
                                            "marginBottom": "10px",
                                        },
                                        multiple=True,
                                    ),
                                    # Move the screenshot-status container here
                                    html.Div(
                                        id="screenshot-status",
                                        style={"marginTop": "10px"},
                                    ),
                                ],
                                style={"marginBottom": "10px"},
                            ),
                            html.Button(
                                "Submit",
                                id="bug-submit-btn",
                                className="btn btn-danger",
                            ),
                            html.Button(
                                "Cancel",
                                id="bug-cancel-btn",
                                className="btn btn-secondary",
                                style={"marginLeft": "10px"},
                            ),
                        ],
                        id="report-bug-popup",
                        className="report-bug-popup",
                        draggable="false",
                        style={
                            "display": "none",
                            "position": "fixed",
                            "top": "20%",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "backgroundColor": "#fff",
                            "padding": "20px",
                            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
                            "zIndex": 1000,
                            "width": "43%",
                            "cursor": "move",
                            "borderRadius": "8px",
                        },
                    ),
                    # New Thank You Popup for Bug Report Submission
                    html.Div(
                        [
                            html.H4("Thank you!"),
                            html.P("Your bug report has been submitted successfully."),
                            # Optionally show the submitted email:
                            dcc.Markdown(id="bug-submitted-email", children=""),
                            html.Button(
                                "Close",
                                id="bug-thankyou-close-btn",
                                className="btn btn-secondary",
                            ),
                        ],
                        id="bug-thankyou-popup",
                        className="bug-thankyou-popup",
                        draggable="false",
                        style={
                            "display": "none",
                            "position": "fixed",
                            "top": "30%",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "backgroundColor": "#fff",
                            "padding": "20px",
                            "boxShadow": "0 4px 8px rgba(0,0,0,0.2)",
                            "zIndex": 1000,
                            "width": "40%",
                            "cursor": "move",
                            "borderRadius": "8px",
                        },
                    ),
                    # New Thank You Popup for Query Submission
                    html.Div(
                        [
                            html.H4("Thank you!"),
                            html.P("Your query has been submitted to the developer."),
                            dcc.Markdown(id="query-submitted-message", children=""),
                            html.Button(
                                "Close",
                                id="query-thankyou-close-btn",
                                className="btn btn-secondary",
                            ),
                        ],
                        id="query-thankyou-popup",
                        className="query-thankyou-popup",
                        draggable="false",
                        style={
                            "display": "none",
                            "position": "fixed",
                            "top": "30%",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "backgroundColor": "#fff",
                            "padding": "20px",
                            "boxShadow": "0 4px 8px rgba(0,0,0,0.2)",
                            "zIndex": 1000,
                            "width": "40%",
                            "cursor": "move",
                            "borderRadius": "8px",
                        },
                    ),
                ],
            ),
        ]
    )


@app.callback(
    Output("screenshot-status", "children"),
    [Input("bug-screenshot-upload", "contents")],
)
def update_screenshot_status(contents):
    if contents:
        # If multiple files are allowed, contents will be a list.
        count = len(contents) if isinstance(contents, list) else 1
        return html.Div(
            [
                html.I(className="bi bi-paperclip", style={"marginRight": "5px"}),
                f"{count} file{'s' if count > 1 else ''} attached",
            ],
            style={"display": "flex", "alignItems": "center"},
        )
    return "No attachment"


@app.callback(
    [
        Output("bug-screenshot-upload", "contents", allow_duplicate=True),
        Output("screenshot-status", "children", allow_duplicate=True),
        Output("bug-name", "value", allow_duplicate=True),
        Output("bug-email", "value", allow_duplicate=True),
        Output("bug-description", "value", allow_duplicate=True),
    ],
    [Input("bug-cancel-btn", "n_clicks")],
    prevent_initial_call=True,
)
def clear_bug_report_fields(n_clicks):
    if n_clicks:
        return None, "No attachment", "", "", ""
    raise PreventUpdate
