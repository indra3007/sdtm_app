from dash import html

def header():
    return html.Div(
        [
            html.Div(
                [
                    html.Img(
                        src="./assets/gilead_logo.png",  # Use the root-relative path
                        className="logo",
                    ),
                    html.Div("cSDTM Quality Checks", className="header-title"),
                ],
                className="header-container",
            )
        ]
    )