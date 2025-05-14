from dash import html, dcc

def home_section(is_protocol=True):
    return html.Div(
        [
            # Header Row.
            html.Div(
                [
                    # Left Group: Home, Back, and Info buttons.
                    html.Div(
                        [
                            html.A(
                                html.Button(
                                    [html.I(className="bi bi-house"), " Home"],
                                    className="home-button",
                                ),
                                href="/sdtmchecks/",
                                className="home-link",
                            ),
                            dcc.Link(
                                html.Button(
                                    [html.I(className="bi bi-arrow-left"), " Back"],
                                    className="back-button",
                                ),
                                href="#",
                                id="back-link",
                            ),
                            html.Button(
                                [html.I(className="bi bi-info-circle"), " Info"],
                                id="info-button",
                                className="info-button btn btn-primary",
                                style={"marginLeft": "10px"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"},
                    ),
                    # Center Group: Welcome message (conditionally displayed)
                    html.Div(
                        "Welcome to the cSDTM Quality Checks Home Page!" if is_protocol else "",
                        className="home-content",
                        style={
                            "flex": "1",
                            "textAlign": "center",
                            "fontSize": "32px",
                            "color": "#2E8B57",  # SeaGreen color
                            "fontWeight": "bold",
                            "animation": "flash 1s infinite",  # Flashing animation
                        },
                    ),
                    # Right Group: Submit Query button.
                    html.Div(
                        html.Button(
                            [html.I(className="bi bi-send"), " Submit Query"],
                            id="submit-query-button",
                            className="btn btn-info",
                        ),
                        style={"display": "flex", "alignItems": "center"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "width": "100%",
                    "marginBottom": "20px",
                },
            ),

            # Info Popup.
            html.Div(
                [
                    html.H4("Submit Query", className="fancy-title"),
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
                draggable="false",  # JavaScript will handle drag events
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
                    "width": "43%",    # Adjusted width as desired
                    "cursor": "move",
                    "borderRadius": "8px",
                },
            ),
        ]
    )