import dash_ag_grid as dag
from dash import html

from pages.home import home_section


def extract_study_path(full_path, protocol):
    tokens = [token.strip() for token in full_path.split("/") if token.strip()]
    protocol_lower = protocol.strip().lower()
    for i, token in enumerate(tokens):
        if token.lower() == protocol_lower:
            return "/" + "/".join(tokens[: i + 1])
    return full_path


def protocol_page(summary_df):
    protocol_df = (
        summary_df.groupby("Protocol")
        .agg({"Data_Path": "first", "Date": "first"})
        .reset_index()
    )
    # Update the Data_Path column to show only the truncated study path
    protocol_df["Data_Path"] = protocol_df.apply(
        lambda row: extract_study_path(row["Data_Path"], row["Protocol"]), axis=1
    )

    return html.Div(
        [
            home_section(),
            html.Div(
                [
                    html.I(
                        className="bi bi-folder-fill folder-icon",
                        style={
                            "marginLeft": "25px",
                            "marginRight": "10px",
                            "color": "#007bff",
                            "fontSize": "1.5rem",
                            "marginBottom": "10px",
                        },
                    ),
                    html.H1(
                        "Protocols",
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
                    "marginRight": "25px",
                },
            ),
            html.Div(
                dag.AgGrid(
                    id="protocol-grid",
                    rowData=protocol_df.to_dict("records"),
                    columnDefs=[
                        {
                            "headerName": "Protocol",
                            "field": "Protocol",
                            "cellRenderer": "ProtocolLink",  # Your custom renderer should link to /project/<protocol>
                            "width": 800,
                        },
                        {
                            "headerName": "Study Path",
                            "field": "Data_Path",
                            "width": 1200,
                        },
                        {
                            "headerName": "Latest Date",
                            "field": "Date",
                            "width": 500,
                        },
                    ],
                    # Enable row selection
                    dashGridOptions={
                        "pagination": True,
                        "paginationPageSize": 30,
                        "rowSelection": "single",
                    },
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
