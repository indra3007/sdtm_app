from dash import html


def header():
    return html.Div(
        [
            html.Div(
                [
                    html.Img(
                        src="/sdtmchecks/assets/gilead_logo.png",  # Existing logo
                        className="logo",
                        id="gilead-logo",
                        style={
                            "cursor": "pointer",
                            "height": "60px",
                            "borderRadius": "20px",
                        },
                    ),
                    # Additional image inserted before the title
                    html.Img(
                        src="/sdtmchecks/assets/quality_checks.png",  # Replace with your image
                        className="header-extra-image",
                        style={
                            "height": "60px",
                            "marginRight": "1490px",
                            "borderRadius": "20px",
                        },
                    ),
                    html.Div(
                        "cSDTM Quality Checks",
                        className="header-title",
                        style={"marginLeft": "10px", "borderRadius": "20px"},
                    ),
                ],
                className="header-container",
            )
        ]
    )
