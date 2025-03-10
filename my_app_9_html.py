import pandas as pd
import os
import sys
import dash
from dash import dcc, html
import dash_ag_grid as dag
from dash.dependencies import Input, Output
from flask import Flask
import threading
import time
import asyncio
from pyppeteer import launch
import pyreadstat  # For reading .sas7bdat files

def load_sas_datasets(data_path):
    """ Load all SAS datasets from the given path. """
    sas_files = [f for f in os.listdir(data_path) if f.endswith('.sas7bdat')]
    datasets = {}

    if not sas_files:
        print("⚠️ No SAS datasets found. Using dummy data instead.")
        return generate_dummy_data()

    for file in sas_files:
        dataset_name = os.path.splitext(file)[0].upper()
        try:
            df, _ = pyreadstat.read_sas7bdat(os.path.join(data_path, file))
            datasets[dataset_name] = df
        except Exception as e:
            print(f"⚠️ Error loading {file}: {e}")
    
    return datasets

def generate_dummy_data():
    """ Generate dummy datasets if no real datasets are available. """
    dummy_datasets = {
        "DM": pd.DataFrame({
            "USUBJID": ["001", "002", "003"],
            "AGE": [25, 30, 45],
            "SEX": ["M", "F", "M"],
            "RACE": ["Asian", "Caucasian", "Hispanic"]
        }),
        "AE": pd.DataFrame({
            "USUBJID": ["001", "001", "002"],
            "AEDECOD": ["Headache", "Fatigue", "Nausea"],
            "AESTDTC": ["2024-01-01", "2024-01-03", "2024-02-15"]
        }),
        "LB": pd.DataFrame({
            "USUBJID": ["001", "002", "003"],
            "TEST": ["Hemoglobin", "WBC", "Platelet Count"],
            "RESULT": [13.5, 6.2, 250]
        })
    }
    return dummy_datasets

def create_dash_app(data_path):
    """ Create and return a Dash app with dataset tabs. """
    datasets = load_sas_datasets(data_path)

    server = Flask(__name__)  
    app = dash.Dash(__name__, server=server)

    if not datasets:
        print("⚠️ No datasets loaded. Exiting.")
        sys.exit(1)

    tabs = [
        dcc.Tab(
            label=dataset_name,
            value=dataset_name,
            children=[
                dag.AgGrid(
                    rowData=df.to_dict("records"),
                    columnDefs=[{"headerName": col, "field": col} for col in df.columns],
                    defaultColDef={
                        "sortable": True, "filter": True, "resizable": True, "editable": False
                    },
                    style={"height": "600px", "width": "100%"},
                )
            ],
        )
        for dataset_name, df in datasets.items()
    ]

    app.layout = html.Div(
        [
            html.H1("SDTM Interactive Report", style={"text-align": "center", "color": "#2E8B57"}),
            dcc.Tabs(id="dataset-tabs", children=tabs),
        ]
    )

    return app, server

async def save_dash_as_html(output_file="sdtm_report.html", port=8050):
    """ Render the Dash app in a headless browser and save as HTML. """
    browser = await launch(executablePath="C:/Program Files/Google/Chrome/Application/chrome.exe")  
    page = await browser.newPage()
    await page.goto(f"http://127.0.0.1:{port}")
    await asyncio.sleep(3)  

    html_content = await page.content()
    await browser.close()

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Report saved as {output_file}")

def run_server_and_save(data_path, output_file="sdtm_report.html"):
    """ Run Dash server, render in browser, and save as HTML. """
    app, server = create_dash_app(data_path)

    def run_dash():
        app.run_server(debug=False, port=8050, use_reloader=False)

    thread = threading.Thread(target=run_dash)
    thread.start()

    time.sleep(5)  
    asyncio.run(save_dash_as_html(output_file))

    os._exit(0)  

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <data_path>")
        sys.exit(1)

    data_path = sys.argv[1]
    run_server_and_save(data_path)
