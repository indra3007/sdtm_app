from dash import Dash, html, Input, Output, dcc
def home_section():
    return html.Div(
        [
            html.A(
                html.Button(
                    [html.I(className="bi bi-house"), " Home"],  # Icon and text
                    className="home-button",
                ),
                href="/sdtmchecks/",
                className="home-link",
            ),
            dcc.Link(
                html.Button(
                    [html.I(className="bi bi-arrow-left"), " Back"],  # Icon and text
                    className="back-button",
                ),
                href="#",  # Placeholder, updated dynamically by the callback
                id="back-link",  # Add an ID for the Back link
            ),
            html.Div(
                [
                    html.Button(
                        [
                            html.I(className="bi bi-info-circle"),
                            " Info",
                        ],  # Icon and text
                        className="info-button",
                        id="info-button",
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
                                className="ok-button",
                                id="ok-button",  # Add an ID for the OK button
                            ),
                        ],
                        id="info-popup",
                        className="info-popup",
                        style={"display": "none"},
                    ),  # Initially hidden
                ],
                className="info-container",
            ),  # Container for the info button and popup
        ],
        className="home-container",
    )
