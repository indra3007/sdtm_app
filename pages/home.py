import os
from dash import html, dcc

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
                                                "SDTM IG version, and protocol-specific requirements. Please consult the relevant documentation "
                                                "or team for clarification.",
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
                                            # X Mark at the top right to close the popup.
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
                                            # Header container with logo on left and title next to it.
                                            html.Div(
                                                [
                                                    html.Img(
                                                        src="/sdtmchecks/assets/quality_checks.png",
                                                        style={
                                                            "height": "80px",
                                                            "marginRight": "10px",  # add some space between logo and title
                                                        },
                                                    ),
                                                    html.H2(
                                                        "cSDTM Quality Checks – User Guide",
                                                        style={
                                                            "textAlign": "center",
                                                            "fontFamily": "cursive",
                                                            "color": "#2E8B57",
                                                            "margin": "0",  # remove default margins if needed
                                                        },
                                                    ),
                                                ],
                                                style={
                                                    "marginBottom": "20px",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                },
                                            ),
                                            # Markdown content for the user guide.
                                            dcc.Markdown(
                                                user_guide_content,
                                                style={"marginTop": "10px"},
                                            ),
                                            # Traditional Close button.
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
                    # Right Group: Submit Query button.
                    html.Div(
                        html.Button(
                            [html.I(className="bi bi-send"), " Submit Query"],
                            id="submit-query-button",
                            className="btn btn-info",
                        ),
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
            html.Div(
                [
                    # Header container with logo and title in one row.
                    html.Div(
                        [
                            html.Img(
                                src="/sdtmchecks/assets/quality_checks.png",
                                style={
                                    "height": "80px",
                                    "marginRight": "10px",  # space between logo and title
                                },
                            ),
                            html.H4(
                                "Submit Query",
                                className="fancy-title",
                                style={
                                    "margin": "0"
                                },  # remove extra margin for tight alignment
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"},
                    ),
                    # Rainbow-colored horizontal line below the header.
                    html.Div(
                        style={
                            "height": "4px",
                            "width": "100%",
                            "background": "linear-gradient(to right, red, orange, yellow, green, blue, indigo, violet)",
                            "marginTop": "5px",
                        },
                    ),
                    # The query form elements.
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
                            html.Label("Query Description: ", className="fancy-label"),
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
                            html.Label("Query Rule / Code: ", className="fancy-label"),
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
        ]
    )
